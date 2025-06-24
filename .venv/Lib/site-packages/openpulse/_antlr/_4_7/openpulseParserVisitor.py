# Generated from openpulseParser.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .openpulseParser import openpulseParser
else:
    from openpulseParser import openpulseParser

# This class defines a complete generic visitor for a parse tree produced by openpulseParser.

class openpulseParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by openpulseParser#calibrationBlock.
    def visitCalibrationBlock(self, ctx:openpulseParser.CalibrationBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#openpulseStatement.
    def visitOpenpulseStatement(self, ctx:openpulseParser.OpenpulseStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#scalarType.
    def visitScalarType(self, ctx:openpulseParser.ScalarTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#program.
    def visitProgram(self, ctx:openpulseParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#version.
    def visitVersion(self, ctx:openpulseParser.VersionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#statement.
    def visitStatement(self, ctx:openpulseParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#annotation.
    def visitAnnotation(self, ctx:openpulseParser.AnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#scope.
    def visitScope(self, ctx:openpulseParser.ScopeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#pragma.
    def visitPragma(self, ctx:openpulseParser.PragmaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#statementOrScope.
    def visitStatementOrScope(self, ctx:openpulseParser.StatementOrScopeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#calibrationGrammarStatement.
    def visitCalibrationGrammarStatement(self, ctx:openpulseParser.CalibrationGrammarStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#includeStatement.
    def visitIncludeStatement(self, ctx:openpulseParser.IncludeStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#breakStatement.
    def visitBreakStatement(self, ctx:openpulseParser.BreakStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#continueStatement.
    def visitContinueStatement(self, ctx:openpulseParser.ContinueStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#endStatement.
    def visitEndStatement(self, ctx:openpulseParser.EndStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#forStatement.
    def visitForStatement(self, ctx:openpulseParser.ForStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#ifStatement.
    def visitIfStatement(self, ctx:openpulseParser.IfStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#returnStatement.
    def visitReturnStatement(self, ctx:openpulseParser.ReturnStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#whileStatement.
    def visitWhileStatement(self, ctx:openpulseParser.WhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#switchStatement.
    def visitSwitchStatement(self, ctx:openpulseParser.SwitchStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#switchCaseItem.
    def visitSwitchCaseItem(self, ctx:openpulseParser.SwitchCaseItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#barrierStatement.
    def visitBarrierStatement(self, ctx:openpulseParser.BarrierStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#boxStatement.
    def visitBoxStatement(self, ctx:openpulseParser.BoxStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#delayStatement.
    def visitDelayStatement(self, ctx:openpulseParser.DelayStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#gateCallStatement.
    def visitGateCallStatement(self, ctx:openpulseParser.GateCallStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#measureArrowAssignmentStatement.
    def visitMeasureArrowAssignmentStatement(self, ctx:openpulseParser.MeasureArrowAssignmentStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#resetStatement.
    def visitResetStatement(self, ctx:openpulseParser.ResetStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#aliasDeclarationStatement.
    def visitAliasDeclarationStatement(self, ctx:openpulseParser.AliasDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#classicalDeclarationStatement.
    def visitClassicalDeclarationStatement(self, ctx:openpulseParser.ClassicalDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#constDeclarationStatement.
    def visitConstDeclarationStatement(self, ctx:openpulseParser.ConstDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#ioDeclarationStatement.
    def visitIoDeclarationStatement(self, ctx:openpulseParser.IoDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#oldStyleDeclarationStatement.
    def visitOldStyleDeclarationStatement(self, ctx:openpulseParser.OldStyleDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#quantumDeclarationStatement.
    def visitQuantumDeclarationStatement(self, ctx:openpulseParser.QuantumDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#defStatement.
    def visitDefStatement(self, ctx:openpulseParser.DefStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#externStatement.
    def visitExternStatement(self, ctx:openpulseParser.ExternStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#gateStatement.
    def visitGateStatement(self, ctx:openpulseParser.GateStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#assignmentStatement.
    def visitAssignmentStatement(self, ctx:openpulseParser.AssignmentStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#expressionStatement.
    def visitExpressionStatement(self, ctx:openpulseParser.ExpressionStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#calStatement.
    def visitCalStatement(self, ctx:openpulseParser.CalStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#defcalStatement.
    def visitDefcalStatement(self, ctx:openpulseParser.DefcalStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#bitwiseXorExpression.
    def visitBitwiseXorExpression(self, ctx:openpulseParser.BitwiseXorExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#additiveExpression.
    def visitAdditiveExpression(self, ctx:openpulseParser.AdditiveExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#durationofExpression.
    def visitDurationofExpression(self, ctx:openpulseParser.DurationofExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#parenthesisExpression.
    def visitParenthesisExpression(self, ctx:openpulseParser.ParenthesisExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#comparisonExpression.
    def visitComparisonExpression(self, ctx:openpulseParser.ComparisonExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#multiplicativeExpression.
    def visitMultiplicativeExpression(self, ctx:openpulseParser.MultiplicativeExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#logicalOrExpression.
    def visitLogicalOrExpression(self, ctx:openpulseParser.LogicalOrExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#castExpression.
    def visitCastExpression(self, ctx:openpulseParser.CastExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#powerExpression.
    def visitPowerExpression(self, ctx:openpulseParser.PowerExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#bitwiseOrExpression.
    def visitBitwiseOrExpression(self, ctx:openpulseParser.BitwiseOrExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#callExpression.
    def visitCallExpression(self, ctx:openpulseParser.CallExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#bitshiftExpression.
    def visitBitshiftExpression(self, ctx:openpulseParser.BitshiftExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#bitwiseAndExpression.
    def visitBitwiseAndExpression(self, ctx:openpulseParser.BitwiseAndExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#equalityExpression.
    def visitEqualityExpression(self, ctx:openpulseParser.EqualityExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#logicalAndExpression.
    def visitLogicalAndExpression(self, ctx:openpulseParser.LogicalAndExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#indexExpression.
    def visitIndexExpression(self, ctx:openpulseParser.IndexExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#unaryExpression.
    def visitUnaryExpression(self, ctx:openpulseParser.UnaryExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#literalExpression.
    def visitLiteralExpression(self, ctx:openpulseParser.LiteralExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#aliasExpression.
    def visitAliasExpression(self, ctx:openpulseParser.AliasExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#declarationExpression.
    def visitDeclarationExpression(self, ctx:openpulseParser.DeclarationExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#measureExpression.
    def visitMeasureExpression(self, ctx:openpulseParser.MeasureExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#rangeExpression.
    def visitRangeExpression(self, ctx:openpulseParser.RangeExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#setExpression.
    def visitSetExpression(self, ctx:openpulseParser.SetExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#arrayLiteral.
    def visitArrayLiteral(self, ctx:openpulseParser.ArrayLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#indexOperator.
    def visitIndexOperator(self, ctx:openpulseParser.IndexOperatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#indexedIdentifier.
    def visitIndexedIdentifier(self, ctx:openpulseParser.IndexedIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#returnSignature.
    def visitReturnSignature(self, ctx:openpulseParser.ReturnSignatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#gateModifier.
    def visitGateModifier(self, ctx:openpulseParser.GateModifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#qubitType.
    def visitQubitType(self, ctx:openpulseParser.QubitTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#arrayType.
    def visitArrayType(self, ctx:openpulseParser.ArrayTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#arrayReferenceType.
    def visitArrayReferenceType(self, ctx:openpulseParser.ArrayReferenceTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#designator.
    def visitDesignator(self, ctx:openpulseParser.DesignatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#defcalTarget.
    def visitDefcalTarget(self, ctx:openpulseParser.DefcalTargetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#defcalArgumentDefinition.
    def visitDefcalArgumentDefinition(self, ctx:openpulseParser.DefcalArgumentDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#defcalOperand.
    def visitDefcalOperand(self, ctx:openpulseParser.DefcalOperandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#gateOperand.
    def visitGateOperand(self, ctx:openpulseParser.GateOperandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#externArgument.
    def visitExternArgument(self, ctx:openpulseParser.ExternArgumentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#argumentDefinition.
    def visitArgumentDefinition(self, ctx:openpulseParser.ArgumentDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#argumentDefinitionList.
    def visitArgumentDefinitionList(self, ctx:openpulseParser.ArgumentDefinitionListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#defcalArgumentDefinitionList.
    def visitDefcalArgumentDefinitionList(self, ctx:openpulseParser.DefcalArgumentDefinitionListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#defcalOperandList.
    def visitDefcalOperandList(self, ctx:openpulseParser.DefcalOperandListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#expressionList.
    def visitExpressionList(self, ctx:openpulseParser.ExpressionListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#identifierList.
    def visitIdentifierList(self, ctx:openpulseParser.IdentifierListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#gateOperandList.
    def visitGateOperandList(self, ctx:openpulseParser.GateOperandListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by openpulseParser#externArgumentList.
    def visitExternArgumentList(self, ctx:openpulseParser.ExternArgumentListContext):
        return self.visitChildren(ctx)



del openpulseParser