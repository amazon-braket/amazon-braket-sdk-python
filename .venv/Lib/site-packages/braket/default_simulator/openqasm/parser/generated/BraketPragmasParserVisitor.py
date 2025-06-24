# Generated from BraketPragmasParser.g4 by ANTLR 4.9.2
from antlr4 import ParseTreeVisitor

if __name__ is not None and "." in __name__:
    from .BraketPragmasParser import BraketPragmasParser
else:
    from BraketPragmasParser import BraketPragmasParser

# This class defines a complete generic visitor for a parse tree produced by BraketPragmasParser.


class BraketPragmasParserVisitor(ParseTreeVisitor):
    # Visit a parse tree produced by BraketPragmasParser#braketPragma.
    def visitBraketPragma(self, ctx: BraketPragmasParser.BraketPragmaContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#braketUnitaryPragma.
    def visitBraketUnitaryPragma(self, ctx: BraketPragmasParser.BraketUnitaryPragmaContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#braketVerbatimPragma.
    def visitBraketVerbatimPragma(self, ctx: BraketPragmasParser.BraketVerbatimPragmaContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#twoDimMatrix.
    def visitTwoDimMatrix(self, ctx: BraketPragmasParser.TwoDimMatrixContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#row.
    def visitRow(self, ctx: BraketPragmasParser.RowContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#braketResultPragma.
    def visitBraketResultPragma(self, ctx: BraketPragmasParser.BraketResultPragmaContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#resultType.
    def visitResultType(self, ctx: BraketPragmasParser.ResultTypeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#noArgResultType.
    def visitNoArgResultType(self, ctx: BraketPragmasParser.NoArgResultTypeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#noArgResultTypeName.
    def visitNoArgResultTypeName(self, ctx: BraketPragmasParser.NoArgResultTypeNameContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#optionalMultiTargetResultType.
    def visitOptionalMultiTargetResultType(
        self, ctx: BraketPragmasParser.OptionalMultiTargetResultTypeContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#optionalMultiTargetResultTypeName.
    def visitOptionalMultiTargetResultTypeName(
        self, ctx: BraketPragmasParser.OptionalMultiTargetResultTypeNameContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#MultiTargetIdentifiers.
    def visitMultiTargetIdentifiers(self, ctx: BraketPragmasParser.MultiTargetIdentifiersContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#MultiTargetAll.
    def visitMultiTargetAll(self, ctx: BraketPragmasParser.MultiTargetAllContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#multiStateResultType.
    def visitMultiStateResultType(self, ctx: BraketPragmasParser.MultiStateResultTypeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#multiStateResultTypeName.
    def visitMultiStateResultTypeName(
        self, ctx: BraketPragmasParser.MultiStateResultTypeNameContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#multiState.
    def visitMultiState(self, ctx: BraketPragmasParser.MultiStateContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#observableResultType.
    def visitObservableResultType(self, ctx: BraketPragmasParser.ObservableResultTypeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#observable.
    def visitObservable(self, ctx: BraketPragmasParser.ObservableContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#StandardObservableIdentifier.
    def visitStandardObservableIdentifier(
        self, ctx: BraketPragmasParser.StandardObservableIdentifierContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#StandardObservableAll.
    def visitStandardObservableAll(self, ctx: BraketPragmasParser.StandardObservableAllContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#tensorProductObservable.
    def visitTensorProductObservable(self, ctx: BraketPragmasParser.TensorProductObservableContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#hermitianObservable.
    def visitHermitianObservable(self, ctx: BraketPragmasParser.HermitianObservableContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#observableResultTypeName.
    def visitObservableResultTypeName(
        self, ctx: BraketPragmasParser.ObservableResultTypeNameContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#standardObservableName.
    def visitStandardObservableName(self, ctx: BraketPragmasParser.StandardObservableNameContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#complexOneValue.
    def visitComplexOneValue(self, ctx: BraketPragmasParser.ComplexOneValueContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#complexTwoValues.
    def visitComplexTwoValues(self, ctx: BraketPragmasParser.ComplexTwoValuesContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#braketNoisePragma.
    def visitBraketNoisePragma(self, ctx: BraketPragmasParser.BraketNoisePragmaContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#Noise.
    def visitNoise(self, ctx: BraketPragmasParser.NoiseContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#Kraus.
    def visitKraus(self, ctx: BraketPragmasParser.KrausContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#matrices.
    def visitMatrices(self, ctx: BraketPragmasParser.MatricesContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#probabilities.
    def visitProbabilities(self, ctx: BraketPragmasParser.ProbabilitiesContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#noiseInstructionName.
    def visitNoiseInstructionName(self, ctx: BraketPragmasParser.NoiseInstructionNameContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#program.
    def visitProgram(self, ctx: BraketPragmasParser.ProgramContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#version.
    def visitVersion(self, ctx: BraketPragmasParser.VersionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#statement.
    def visitStatement(self, ctx: BraketPragmasParser.StatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#annotation.
    def visitAnnotation(self, ctx: BraketPragmasParser.AnnotationContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#scope.
    def visitScope(self, ctx: BraketPragmasParser.ScopeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#pragma.
    def visitPragma(self, ctx: BraketPragmasParser.PragmaContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#statementOrScope.
    def visitStatementOrScope(self, ctx: BraketPragmasParser.StatementOrScopeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#calibrationGrammarStatement.
    def visitCalibrationGrammarStatement(
        self, ctx: BraketPragmasParser.CalibrationGrammarStatementContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#includeStatement.
    def visitIncludeStatement(self, ctx: BraketPragmasParser.IncludeStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#breakStatement.
    def visitBreakStatement(self, ctx: BraketPragmasParser.BreakStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#continueStatement.
    def visitContinueStatement(self, ctx: BraketPragmasParser.ContinueStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#endStatement.
    def visitEndStatement(self, ctx: BraketPragmasParser.EndStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#forStatement.
    def visitForStatement(self, ctx: BraketPragmasParser.ForStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#ifStatement.
    def visitIfStatement(self, ctx: BraketPragmasParser.IfStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#returnStatement.
    def visitReturnStatement(self, ctx: BraketPragmasParser.ReturnStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#whileStatement.
    def visitWhileStatement(self, ctx: BraketPragmasParser.WhileStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#barrierStatement.
    def visitBarrierStatement(self, ctx: BraketPragmasParser.BarrierStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#boxStatement.
    def visitBoxStatement(self, ctx: BraketPragmasParser.BoxStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#delayStatement.
    def visitDelayStatement(self, ctx: BraketPragmasParser.DelayStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#gateCallStatement.
    def visitGateCallStatement(self, ctx: BraketPragmasParser.GateCallStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#measureArrowAssignmentStatement.
    def visitMeasureArrowAssignmentStatement(
        self, ctx: BraketPragmasParser.MeasureArrowAssignmentStatementContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#resetStatement.
    def visitResetStatement(self, ctx: BraketPragmasParser.ResetStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#aliasDeclarationStatement.
    def visitAliasDeclarationStatement(
        self, ctx: BraketPragmasParser.AliasDeclarationStatementContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#classicalDeclarationStatement.
    def visitClassicalDeclarationStatement(
        self, ctx: BraketPragmasParser.ClassicalDeclarationStatementContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#constDeclarationStatement.
    def visitConstDeclarationStatement(
        self, ctx: BraketPragmasParser.ConstDeclarationStatementContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#ioDeclarationStatement.
    def visitIoDeclarationStatement(self, ctx: BraketPragmasParser.IoDeclarationStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#oldStyleDeclarationStatement.
    def visitOldStyleDeclarationStatement(
        self, ctx: BraketPragmasParser.OldStyleDeclarationStatementContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#quantumDeclarationStatement.
    def visitQuantumDeclarationStatement(
        self, ctx: BraketPragmasParser.QuantumDeclarationStatementContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#defStatement.
    def visitDefStatement(self, ctx: BraketPragmasParser.DefStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#externStatement.
    def visitExternStatement(self, ctx: BraketPragmasParser.ExternStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#gateStatement.
    def visitGateStatement(self, ctx: BraketPragmasParser.GateStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#assignmentStatement.
    def visitAssignmentStatement(self, ctx: BraketPragmasParser.AssignmentStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#expressionStatement.
    def visitExpressionStatement(self, ctx: BraketPragmasParser.ExpressionStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#defcalStatement.
    def visitDefcalStatement(self, ctx: BraketPragmasParser.DefcalStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#bitwiseXorExpression.
    def visitBitwiseXorExpression(self, ctx: BraketPragmasParser.BitwiseXorExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#additiveExpression.
    def visitAdditiveExpression(self, ctx: BraketPragmasParser.AdditiveExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#durationofExpression.
    def visitDurationofExpression(self, ctx: BraketPragmasParser.DurationofExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#parenthesisExpression.
    def visitParenthesisExpression(self, ctx: BraketPragmasParser.ParenthesisExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#comparisonExpression.
    def visitComparisonExpression(self, ctx: BraketPragmasParser.ComparisonExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#multiplicativeExpression.
    def visitMultiplicativeExpression(
        self, ctx: BraketPragmasParser.MultiplicativeExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#logicalOrExpression.
    def visitLogicalOrExpression(self, ctx: BraketPragmasParser.LogicalOrExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#castExpression.
    def visitCastExpression(self, ctx: BraketPragmasParser.CastExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#powerExpression.
    def visitPowerExpression(self, ctx: BraketPragmasParser.PowerExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#bitwiseOrExpression.
    def visitBitwiseOrExpression(self, ctx: BraketPragmasParser.BitwiseOrExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#callExpression.
    def visitCallExpression(self, ctx: BraketPragmasParser.CallExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#bitshiftExpression.
    def visitBitshiftExpression(self, ctx: BraketPragmasParser.BitshiftExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#bitwiseAndExpression.
    def visitBitwiseAndExpression(self, ctx: BraketPragmasParser.BitwiseAndExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#equalityExpression.
    def visitEqualityExpression(self, ctx: BraketPragmasParser.EqualityExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#logicalAndExpression.
    def visitLogicalAndExpression(self, ctx: BraketPragmasParser.LogicalAndExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#indexExpression.
    def visitIndexExpression(self, ctx: BraketPragmasParser.IndexExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#unaryExpression.
    def visitUnaryExpression(self, ctx: BraketPragmasParser.UnaryExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#literalExpression.
    def visitLiteralExpression(self, ctx: BraketPragmasParser.LiteralExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#aliasExpression.
    def visitAliasExpression(self, ctx: BraketPragmasParser.AliasExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#declarationExpression.
    def visitDeclarationExpression(self, ctx: BraketPragmasParser.DeclarationExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#measureExpression.
    def visitMeasureExpression(self, ctx: BraketPragmasParser.MeasureExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#rangeExpression.
    def visitRangeExpression(self, ctx: BraketPragmasParser.RangeExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#setExpression.
    def visitSetExpression(self, ctx: BraketPragmasParser.SetExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#arrayLiteral.
    def visitArrayLiteral(self, ctx: BraketPragmasParser.ArrayLiteralContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#indexOperator.
    def visitIndexOperator(self, ctx: BraketPragmasParser.IndexOperatorContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#indexedIdentifier.
    def visitIndexedIdentifier(self, ctx: BraketPragmasParser.IndexedIdentifierContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#returnSignature.
    def visitReturnSignature(self, ctx: BraketPragmasParser.ReturnSignatureContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#gateModifier.
    def visitGateModifier(self, ctx: BraketPragmasParser.GateModifierContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#scalarType.
    def visitScalarType(self, ctx: BraketPragmasParser.ScalarTypeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#qubitType.
    def visitQubitType(self, ctx: BraketPragmasParser.QubitTypeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#arrayType.
    def visitArrayType(self, ctx: BraketPragmasParser.ArrayTypeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#arrayReferenceType.
    def visitArrayReferenceType(self, ctx: BraketPragmasParser.ArrayReferenceTypeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#designator.
    def visitDesignator(self, ctx: BraketPragmasParser.DesignatorContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#gateOperand.
    def visitGateOperand(self, ctx: BraketPragmasParser.GateOperandContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#externArgument.
    def visitExternArgument(self, ctx: BraketPragmasParser.ExternArgumentContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#defcalArgument.
    def visitDefcalArgument(self, ctx: BraketPragmasParser.DefcalArgumentContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#argumentDefinition.
    def visitArgumentDefinition(self, ctx: BraketPragmasParser.ArgumentDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#argumentDefinitionList.
    def visitArgumentDefinitionList(self, ctx: BraketPragmasParser.ArgumentDefinitionListContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#expressionList.
    def visitExpressionList(self, ctx: BraketPragmasParser.ExpressionListContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#defcalArgumentList.
    def visitDefcalArgumentList(self, ctx: BraketPragmasParser.DefcalArgumentListContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#identifierList.
    def visitIdentifierList(self, ctx: BraketPragmasParser.IdentifierListContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#gateOperandList.
    def visitGateOperandList(self, ctx: BraketPragmasParser.GateOperandListContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by BraketPragmasParser#externArgumentList.
    def visitExternArgumentList(self, ctx: BraketPragmasParser.ExternArgumentListContext):
        return self.visitChildren(ctx)


del BraketPragmasParser
