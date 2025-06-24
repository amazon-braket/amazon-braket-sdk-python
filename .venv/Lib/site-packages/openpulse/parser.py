"""
=============================
Parser (``openpulse.parser``)
=============================

Tools for parsing OpenPulse programs into the :obj:`reference AST <openpulse.ast>`.

The quick-start interface is simply to call ``openpulse.parse``:

.. currentmodule:: openpulse
.. autofunction:: openpulse.parse

The rest of this module provides some lower-level internals of the parser.

.. currentmodule:: openpulse.parser
.. autoclass:: OpenPulseNodeVisitor
"""

# pylint: disable=wrong-import-order

__all__ = [
    "parse",
    "OpenPulseNodeVisitor",
]

from contextlib import contextmanager
from typing import List, Union

try:
    from antlr4 import CommonTokenStream, InputStream, ParserRuleContext, RecognitionException
    from antlr4.error.Errors import ParseCancellationException
    from antlr4.error.ErrorStrategy import BailErrorStrategy
except ImportError as exc:
    raise ImportError(
        "Parsing is not available unless the [parser] extra is installed,"
        " such as by 'pip install openqasm3[parser]'."
    ) from exc

import openpulse.ast as openpulse_ast
from openqasm3._antlr.qasm3Parser import qasm3Parser  # pylint: disable=import-error
from openqasm3 import ast
from openqasm3.parser import (
    span,
    QASMNodeVisitor,
    _raise_from_context,
    parse as parse_qasm3,
)
from openqasm3.visitor import QASMVisitor

from ._antlr.openpulseLexer import openpulseLexer
from ._antlr.openpulseParser import openpulseParser
from ._antlr.openpulseParserVisitor import openpulseParserVisitor


class OpenPulseParsingError(Exception):
    """An error raised by the AST visitor during the AST-generation phase.  This is raised in cases where the
    given program could not be correctly parsed."""


def parse(input_: str, permissive: bool = False) -> ast.Program:
    """
    Parse a complete OpenPulse program from a string.

    :param input_: A string containing a complete OpenQASM 3 program.
    :param permissive: A Boolean controlling whether ANTLR should attempt to
        recover from incorrect input or not.  Defaults to ``False``; if set to
        ``True``, the reference AST produced may be invalid if ANTLR emits any
        warning messages during its parsing phase.
    :return: A complete :obj:`~ast.Program` node.
    """
    qasm3_ast = parse_qasm3(input_, permissive=permissive)
    CalParser(permissive=permissive).visit(qasm3_ast)
    return qasm3_ast


def parse_openpulse(
    input_: str, in_defcal: bool, permissive: bool = True
) -> openpulse_ast.CalibrationBlock:
    lexer = openpulseLexer(InputStream(input_))
    stream = CommonTokenStream(lexer)
    parser = openpulseParser(stream)
    if not permissive:
        # For some reason, the Python 3 runtime for ANTLR 4 is missing the
        # setter method `setErrorHandler`, so we have to set the attribute
        # directly.
        parser._errHandler = BailErrorStrategy()
    try:
        tree = parser.calibrationBlock()
    except (RecognitionException, ParseCancellationException) as exc:
        msg = ""
        # With BailErrorStrategy, we should be able to recover and report
        # information about the offending token.
        if isinstance(exc, ParseCancellationException) and exc.args:
            tok = getattr(exc.args[0], "offendingToken", None)
            if tok is not None:
                msg = f"Unexpected token '{tok.text}' at line {tok.line}, column {tok.start}."
        raise OpenPulseParsingError(msg) from exc
    result = (
        OpenPulseNodeVisitor(in_defcal).visitCalibrationBlock(tree)
        if tree.children
        else openpulse_ast.CalibrationBlock(body=[])
    )
    return result


class OpenPulseNodeVisitor(openpulseParserVisitor):
    """Base class for the visitor of the OpenPulse AST."""

    def __init__(self, in_defcal: bool):
        # A stack of "contexts", each of which is a stack of "scopes".  Contexts
        # are for the main program, gates and subroutines, while scopes are
        # loops, if/else and manual scoping constructs.  Each "context" always
        # contains at least one scope: the base ``ParserRuleContext`` that
        # opened it.
        self._contexts: List[List[ParserRuleContext]] = []
        self._in_defcal = in_defcal

    @contextmanager
    def _push_context(self, ctx: ParserRuleContext):
        self._contexts.append([ctx])
        yield
        self._contexts.pop()

    @contextmanager
    def _push_scope(self, ctx: ParserRuleContext):
        self._contexts[-1].append(ctx)
        yield
        self._contexts[-1].pop()

    def _current_context(self):
        return self._contexts[-1]

    def _current_scope(self):
        return self._contexts[-1][-1]

    def _current_base_scope(self):
        return self._contexts[-1][0]

    def _in_global_scope(self):
        return len(self._contexts) == 1 and len(self._contexts[0]) == 1

    def _in_gate(self):
        return isinstance(self._current_base_scope(), openpulseParser.GateStatementContext)

    def _in_subroutine(self):
        return isinstance(self._current_base_scope(), openpulseParser.DefStatementContext)

    def _in_loop(self):
        return any(
            isinstance(
                scope,
                (
                    openpulseParser.ForStatementContext,
                    openpulseParser.WhileStatementContext,
                ),
            )
            for scope in reversed(self._current_context())
        )

    def _parse_scoped_statements(
        self, node: Union[qasm3Parser.ScopeContext, qasm3Parser.StatementOrScopeContext]
    ) -> List[ast.Statement]:
        with self._push_scope(node.parentCtx):
            block = self.visit(node)
            return block.statements if isinstance(block, ast.CompoundStatement) else [block]

    @span
    def _visitPulseType(self, ctx: openpulseParser.ScalarTypeContext):
        if ctx.WAVEFORM():
            return openpulse_ast.WaveformType()
        if ctx.PORT():
            return openpulse_ast.PortType()
        if ctx.FRAME():
            return openpulse_ast.FrameType()

    @span
    def visitArrayLiteral(self, ctx: qasm3Parser.ArrayLiteralContext):
        array_literal_element = (
            openpulseParser.ExpressionContext,
            openpulseParser.ArrayLiteralContext,
        )

        def predicate(child):
            return isinstance(child, array_literal_element)

        return ast.ArrayLiteral(
            values=[self.visit(element) for element in ctx.getChildren(predicate=predicate)],
        )

    @span
    def visitCalibrationBlock(self, ctx: openpulseParser.CalibrationBlockContext):
        with self._push_context(ctx):
            return openpulse_ast.CalibrationBlock(
                body=[self.visit(statement) for statement in ctx.openpulseStatement()]
            )

    def visitScalarType(self, ctx: openpulseParser.ScalarTypeContext):
        if ctx.WAVEFORM() or ctx.PORT() or ctx.FRAME():
            return self._visitPulseType(ctx)
        else:
            return QASMNodeVisitor.visitScalarType(self, ctx)

    def visitIndexOperator(self, ctx: openpulseParser.IndexOperatorContext):
        if ctx.setExpression():
            return self.visit(ctx.setExpression())

        index_element = (
            openpulseParser.ExpressionContext,
            openpulseParser.RangeExpressionContext,
        )

        def predicate(child):
            return isinstance(child, index_element)

        return [self.visit(child) for child in ctx.getChildren(predicate=predicate)]

    @span
    def visitRangeExpression(self, ctx: openpulseParser.RangeExpressionContext):
        # start, end and step are all optional as in [:]
        # It could be [start:end] or [start:step:end]
        start = None
        end = None
        step = None
        colons_seen = 0

        for child in ctx.getChildren():
            if isinstance(child, openpulseParser.ExpressionContext):
                expression = self.visit(child)
                if colons_seen == 0:
                    start = expression
                elif colons_seen == 1:
                    end = expression
                else:
                    step = end
                    end = expression
            elif child.getText() == ":":
                colons_seen += 1

        return ast.RangeDefinition(start=start, end=end, step=step)

    @span
    def visitReturnStatement(self, ctx: qasm3Parser.ReturnStatementContext):
        if not (self._in_subroutine() or self._in_defcal):
            _raise_from_context(ctx, "'return' statement outside subroutine or defcal")

        if ctx.expression():
            expression = self.visit(ctx.expression())
        elif ctx.measureExpression():
            expression = self.visit(ctx.measureExpression())
        else:
            expression = None
        return ast.ReturnStatement(expression=expression)

    @span
    def visitOpenpulseStatement(self, ctx: openpulseParser.OpenpulseStatementContext):
        if ctx.pragma():
            return self.visit(ctx.pragma())
        out = self.visit(ctx.getChild(-1))
        out.annotations = [self.visit(annotation) for annotation in ctx.annotation()]
        return out


# Reuse some QASMNodeVisitor methods in OpenPulseNodeVisitor
# The following methods are overridden in OpenPulseNodeVisitor and thus not imported:
"""
    "visitArrayLiteral",
    "visitIndexOperator",
    "visitRangeExpression",
    "visitReturnStatement",
    "visitScalarType",
"""
OpenPulseNodeVisitor._visit_binary_expression = QASMNodeVisitor._visit_binary_expression
OpenPulseNodeVisitor.visitAdditiveExpression = QASMNodeVisitor.visitAdditiveExpression
OpenPulseNodeVisitor.visitAliasDeclarationStatement = QASMNodeVisitor.visitAliasDeclarationStatement
OpenPulseNodeVisitor.visitAliasExpression = QASMNodeVisitor.visitAliasExpression
OpenPulseNodeVisitor.visitAnnotation = QASMNodeVisitor.visitAnnotation
OpenPulseNodeVisitor.visitArgumentDefinition = QASMNodeVisitor.visitArgumentDefinition
OpenPulseNodeVisitor.visitArrayType = QASMNodeVisitor.visitArrayType
OpenPulseNodeVisitor.visitAssignmentStatement = QASMNodeVisitor.visitAssignmentStatement
OpenPulseNodeVisitor.visitBarrierStatement = QASMNodeVisitor.visitBarrierStatement
OpenPulseNodeVisitor.visitBitshiftExpression = QASMNodeVisitor.visitBitshiftExpression
OpenPulseNodeVisitor.visitBitwiseAndExpression = QASMNodeVisitor.visitBitwiseAndExpression
OpenPulseNodeVisitor.visitBitwiseOrExpression = QASMNodeVisitor.visitBitwiseOrExpression
OpenPulseNodeVisitor.visitBitwiseXorExpression = QASMNodeVisitor.visitBitwiseXorExpression
OpenPulseNodeVisitor.visitBoxStatement = QASMNodeVisitor.visitBoxStatement
OpenPulseNodeVisitor.visitBreakStatement = QASMNodeVisitor.visitBreakStatement
OpenPulseNodeVisitor.visitCallExpression = QASMNodeVisitor.visitCallExpression
OpenPulseNodeVisitor.visitCastExpression = QASMNodeVisitor.visitCastExpression
OpenPulseNodeVisitor.visitClassicalDeclarationStatement = (
    QASMNodeVisitor.visitClassicalDeclarationStatement
)
OpenPulseNodeVisitor.visitComparisonExpression = QASMNodeVisitor.visitComparisonExpression
OpenPulseNodeVisitor.visitConstDeclarationStatement = QASMNodeVisitor.visitConstDeclarationStatement
OpenPulseNodeVisitor.visitContinueStatement = QASMNodeVisitor.visitContinueStatement
OpenPulseNodeVisitor.visitDeclarationExpression = QASMNodeVisitor.visitDeclarationExpression
OpenPulseNodeVisitor.visitDefStatement = QASMNodeVisitor.visitDefStatement
OpenPulseNodeVisitor.visitDefcalArgumentDefinition = QASMNodeVisitor.visitDefcalArgumentDefinition
OpenPulseNodeVisitor.visitDefcalOperand = QASMNodeVisitor.visitDefcalOperand
OpenPulseNodeVisitor.visitDefcalTarget = QASMNodeVisitor.visitDefcalTarget
OpenPulseNodeVisitor.visitDelayStatement = QASMNodeVisitor.visitDelayStatement
OpenPulseNodeVisitor.visitDesignator = QASMNodeVisitor.visitDesignator
OpenPulseNodeVisitor.visitDurationofExpression = QASMNodeVisitor.visitDurationofExpression
OpenPulseNodeVisitor.visitEndStatement = QASMNodeVisitor.visitEndStatement
OpenPulseNodeVisitor.visitEqualityExpression = QASMNodeVisitor.visitEqualityExpression
OpenPulseNodeVisitor.visitExpressionStatement = QASMNodeVisitor.visitExpressionStatement
OpenPulseNodeVisitor.visitExternArgument = QASMNodeVisitor.visitExternArgument
OpenPulseNodeVisitor.visitExternStatement = QASMNodeVisitor.visitExternStatement
OpenPulseNodeVisitor.visitForStatement = QASMNodeVisitor.visitForStatement
OpenPulseNodeVisitor.visitGateCallStatement = QASMNodeVisitor.visitGateCallStatement
OpenPulseNodeVisitor.visitGateModifier = QASMNodeVisitor.visitGateModifier
OpenPulseNodeVisitor.visitGateOperand = QASMNodeVisitor.visitGateOperand
OpenPulseNodeVisitor.visitGateStatement = QASMNodeVisitor.visitGateStatement
OpenPulseNodeVisitor.visitIfStatement = QASMNodeVisitor.visitIfStatement
OpenPulseNodeVisitor.visitIncludeStatement = QASMNodeVisitor.visitIncludeStatement
OpenPulseNodeVisitor.visitIndexExpression = QASMNodeVisitor.visitIndexExpression
OpenPulseNodeVisitor.visitIndexedIdentifier = QASMNodeVisitor.visitIndexedIdentifier
OpenPulseNodeVisitor.visitIoDeclarationStatement = QASMNodeVisitor.visitIoDeclarationStatement
OpenPulseNodeVisitor.visitLiteralExpression = QASMNodeVisitor.visitLiteralExpression
OpenPulseNodeVisitor.visitLogicalAndExpression = QASMNodeVisitor.visitLogicalAndExpression
OpenPulseNodeVisitor.visitLogicalOrExpression = QASMNodeVisitor.visitLogicalOrExpression
OpenPulseNodeVisitor.visitMeasureArrowAssignmentStatement = (
    QASMNodeVisitor.visitMeasureArrowAssignmentStatement
)
OpenPulseNodeVisitor.visitMeasureExpression = QASMNodeVisitor.visitMeasureExpression
OpenPulseNodeVisitor.visitMultiplicativeExpression = QASMNodeVisitor.visitMultiplicativeExpression
OpenPulseNodeVisitor.visitOldStyleDeclarationStatement = (
    QASMNodeVisitor.visitOldStyleDeclarationStatement
)
OpenPulseNodeVisitor.visitParenthesisExpression = QASMNodeVisitor.visitParenthesisExpression
OpenPulseNodeVisitor.visitPowerExpression = QASMNodeVisitor.visitPowerExpression
OpenPulseNodeVisitor.visitPragma = QASMNodeVisitor.visitPragma
OpenPulseNodeVisitor.visitProgram = QASMNodeVisitor.visitProgram
OpenPulseNodeVisitor.visitQuantumDeclarationStatement = (
    QASMNodeVisitor.visitQuantumDeclarationStatement
)
OpenPulseNodeVisitor.visitResetStatement = QASMNodeVisitor.visitResetStatement
OpenPulseNodeVisitor.visitScope = QASMNodeVisitor.visitScope
OpenPulseNodeVisitor.visitSetExpression = QASMNodeVisitor.visitSetExpression
OpenPulseNodeVisitor.visitStatement = QASMNodeVisitor.visitStatement
OpenPulseNodeVisitor.visitStatementOrScope = QASMNodeVisitor.visitStatementOrScope
OpenPulseNodeVisitor.visitUnaryExpression = QASMNodeVisitor.visitUnaryExpression
OpenPulseNodeVisitor.visitWhileStatement = QASMNodeVisitor.visitWhileStatement
OpenPulseNodeVisitor.visitSwitchStatement = QASMNodeVisitor.visitSwitchStatement


class CalParser(QASMVisitor[None]):
    """Visit OpenQASM3 AST and parse calibration

    Attributes:
      permissive: should OpenPulse parsing be permissive? If True, ANTLR
        will attempt error recovery (although parsing may still fail elsewhere).
    """

    def __init__(self, permissive: bool = False):
        self.permissive = permissive

    def visit_CalibrationDefinition(
        self, node: ast.CalibrationDefinition
    ) -> openpulse_ast.CalibrationDefinition:
        node.__class__ = openpulse_ast.CalibrationDefinition
        node.body = parse_openpulse(node.body, in_defcal=True, permissive=self.permissive).body

    def visit_CalibrationStatement(
        self, node: ast.CalibrationStatement
    ) -> openpulse_ast.CalibrationStatement:
        node.__class__ = openpulse_ast.CalibrationStatement
        node.body = parse_openpulse(node.body, in_defcal=False, permissive=self.permissive).body
