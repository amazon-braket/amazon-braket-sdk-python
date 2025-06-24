# Generated from qasm3Parser.g4 by ANTLR 4.8
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .qasm3Parser import qasm3Parser
else:
    from qasm3Parser import qasm3Parser

# This class defines a complete generic visitor for a parse tree produced by qasm3Parser.

class qasm3ParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by qasm3Parser#program.
    def visitProgram(self, ctx:qasm3Parser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#version.
    def visitVersion(self, ctx:qasm3Parser.VersionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#statement.
    def visitStatement(self, ctx:qasm3Parser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#annotation.
    def visitAnnotation(self, ctx:qasm3Parser.AnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#scope.
    def visitScope(self, ctx:qasm3Parser.ScopeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#pragma.
    def visitPragma(self, ctx:qasm3Parser.PragmaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#statementOrScope.
    def visitStatementOrScope(self, ctx:qasm3Parser.StatementOrScopeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#calibrationGrammarStatement.
    def visitCalibrationGrammarStatement(self, ctx:qasm3Parser.CalibrationGrammarStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#includeStatement.
    def visitIncludeStatement(self, ctx:qasm3Parser.IncludeStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#breakStatement.
    def visitBreakStatement(self, ctx:qasm3Parser.BreakStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#continueStatement.
    def visitContinueStatement(self, ctx:qasm3Parser.ContinueStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#endStatement.
    def visitEndStatement(self, ctx:qasm3Parser.EndStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#forStatement.
    def visitForStatement(self, ctx:qasm3Parser.ForStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#ifStatement.
    def visitIfStatement(self, ctx:qasm3Parser.IfStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#returnStatement.
    def visitReturnStatement(self, ctx:qasm3Parser.ReturnStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#whileStatement.
    def visitWhileStatement(self, ctx:qasm3Parser.WhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#switchStatement.
    def visitSwitchStatement(self, ctx:qasm3Parser.SwitchStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#switchCaseItem.
    def visitSwitchCaseItem(self, ctx:qasm3Parser.SwitchCaseItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#barrierStatement.
    def visitBarrierStatement(self, ctx:qasm3Parser.BarrierStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#boxStatement.
    def visitBoxStatement(self, ctx:qasm3Parser.BoxStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#delayStatement.
    def visitDelayStatement(self, ctx:qasm3Parser.DelayStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#gateCallStatement.
    def visitGateCallStatement(self, ctx:qasm3Parser.GateCallStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#measureArrowAssignmentStatement.
    def visitMeasureArrowAssignmentStatement(self, ctx:qasm3Parser.MeasureArrowAssignmentStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#resetStatement.
    def visitResetStatement(self, ctx:qasm3Parser.ResetStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#aliasDeclarationStatement.
    def visitAliasDeclarationStatement(self, ctx:qasm3Parser.AliasDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#classicalDeclarationStatement.
    def visitClassicalDeclarationStatement(self, ctx:qasm3Parser.ClassicalDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#constDeclarationStatement.
    def visitConstDeclarationStatement(self, ctx:qasm3Parser.ConstDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#ioDeclarationStatement.
    def visitIoDeclarationStatement(self, ctx:qasm3Parser.IoDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#oldStyleDeclarationStatement.
    def visitOldStyleDeclarationStatement(self, ctx:qasm3Parser.OldStyleDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#quantumDeclarationStatement.
    def visitQuantumDeclarationStatement(self, ctx:qasm3Parser.QuantumDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#defStatement.
    def visitDefStatement(self, ctx:qasm3Parser.DefStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#externStatement.
    def visitExternStatement(self, ctx:qasm3Parser.ExternStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#gateStatement.
    def visitGateStatement(self, ctx:qasm3Parser.GateStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#assignmentStatement.
    def visitAssignmentStatement(self, ctx:qasm3Parser.AssignmentStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#expressionStatement.
    def visitExpressionStatement(self, ctx:qasm3Parser.ExpressionStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#calStatement.
    def visitCalStatement(self, ctx:qasm3Parser.CalStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#defcalStatement.
    def visitDefcalStatement(self, ctx:qasm3Parser.DefcalStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#bitwiseXorExpression.
    def visitBitwiseXorExpression(self, ctx:qasm3Parser.BitwiseXorExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#additiveExpression.
    def visitAdditiveExpression(self, ctx:qasm3Parser.AdditiveExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#durationofExpression.
    def visitDurationofExpression(self, ctx:qasm3Parser.DurationofExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#parenthesisExpression.
    def visitParenthesisExpression(self, ctx:qasm3Parser.ParenthesisExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#comparisonExpression.
    def visitComparisonExpression(self, ctx:qasm3Parser.ComparisonExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#multiplicativeExpression.
    def visitMultiplicativeExpression(self, ctx:qasm3Parser.MultiplicativeExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#logicalOrExpression.
    def visitLogicalOrExpression(self, ctx:qasm3Parser.LogicalOrExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#castExpression.
    def visitCastExpression(self, ctx:qasm3Parser.CastExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#powerExpression.
    def visitPowerExpression(self, ctx:qasm3Parser.PowerExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#bitwiseOrExpression.
    def visitBitwiseOrExpression(self, ctx:qasm3Parser.BitwiseOrExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#callExpression.
    def visitCallExpression(self, ctx:qasm3Parser.CallExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#bitshiftExpression.
    def visitBitshiftExpression(self, ctx:qasm3Parser.BitshiftExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#bitwiseAndExpression.
    def visitBitwiseAndExpression(self, ctx:qasm3Parser.BitwiseAndExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#equalityExpression.
    def visitEqualityExpression(self, ctx:qasm3Parser.EqualityExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#logicalAndExpression.
    def visitLogicalAndExpression(self, ctx:qasm3Parser.LogicalAndExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#indexExpression.
    def visitIndexExpression(self, ctx:qasm3Parser.IndexExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#unaryExpression.
    def visitUnaryExpression(self, ctx:qasm3Parser.UnaryExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#literalExpression.
    def visitLiteralExpression(self, ctx:qasm3Parser.LiteralExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#aliasExpression.
    def visitAliasExpression(self, ctx:qasm3Parser.AliasExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#declarationExpression.
    def visitDeclarationExpression(self, ctx:qasm3Parser.DeclarationExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#measureExpression.
    def visitMeasureExpression(self, ctx:qasm3Parser.MeasureExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#rangeExpression.
    def visitRangeExpression(self, ctx:qasm3Parser.RangeExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#setExpression.
    def visitSetExpression(self, ctx:qasm3Parser.SetExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#arrayLiteral.
    def visitArrayLiteral(self, ctx:qasm3Parser.ArrayLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#indexOperator.
    def visitIndexOperator(self, ctx:qasm3Parser.IndexOperatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#indexedIdentifier.
    def visitIndexedIdentifier(self, ctx:qasm3Parser.IndexedIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#returnSignature.
    def visitReturnSignature(self, ctx:qasm3Parser.ReturnSignatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#gateModifier.
    def visitGateModifier(self, ctx:qasm3Parser.GateModifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#scalarType.
    def visitScalarType(self, ctx:qasm3Parser.ScalarTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#qubitType.
    def visitQubitType(self, ctx:qasm3Parser.QubitTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#arrayType.
    def visitArrayType(self, ctx:qasm3Parser.ArrayTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#arrayReferenceType.
    def visitArrayReferenceType(self, ctx:qasm3Parser.ArrayReferenceTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#designator.
    def visitDesignator(self, ctx:qasm3Parser.DesignatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#defcalTarget.
    def visitDefcalTarget(self, ctx:qasm3Parser.DefcalTargetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#defcalArgumentDefinition.
    def visitDefcalArgumentDefinition(self, ctx:qasm3Parser.DefcalArgumentDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#defcalOperand.
    def visitDefcalOperand(self, ctx:qasm3Parser.DefcalOperandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#gateOperand.
    def visitGateOperand(self, ctx:qasm3Parser.GateOperandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#externArgument.
    def visitExternArgument(self, ctx:qasm3Parser.ExternArgumentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#argumentDefinition.
    def visitArgumentDefinition(self, ctx:qasm3Parser.ArgumentDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#argumentDefinitionList.
    def visitArgumentDefinitionList(self, ctx:qasm3Parser.ArgumentDefinitionListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#defcalArgumentDefinitionList.
    def visitDefcalArgumentDefinitionList(self, ctx:qasm3Parser.DefcalArgumentDefinitionListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#defcalOperandList.
    def visitDefcalOperandList(self, ctx:qasm3Parser.DefcalOperandListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#expressionList.
    def visitExpressionList(self, ctx:qasm3Parser.ExpressionListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#identifierList.
    def visitIdentifierList(self, ctx:qasm3Parser.IdentifierListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#gateOperandList.
    def visitGateOperandList(self, ctx:qasm3Parser.GateOperandListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by qasm3Parser#externArgumentList.
    def visitExternArgumentList(self, ctx:qasm3Parser.ExternArgumentListContext):
        return self.visitChildren(ctx)



del qasm3Parser