# Generated from qasm3Parser.g4 by ANTLR 4.11.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .qasm3Parser import qasm3Parser
else:
    from qasm3Parser import qasm3Parser

# This class defines a complete listener for a parse tree produced by qasm3Parser.
class qasm3ParserListener(ParseTreeListener):

    # Enter a parse tree produced by qasm3Parser#program.
    def enterProgram(self, ctx:qasm3Parser.ProgramContext):
        pass

    # Exit a parse tree produced by qasm3Parser#program.
    def exitProgram(self, ctx:qasm3Parser.ProgramContext):
        pass


    # Enter a parse tree produced by qasm3Parser#version.
    def enterVersion(self, ctx:qasm3Parser.VersionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#version.
    def exitVersion(self, ctx:qasm3Parser.VersionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#statement.
    def enterStatement(self, ctx:qasm3Parser.StatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#statement.
    def exitStatement(self, ctx:qasm3Parser.StatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#annotation.
    def enterAnnotation(self, ctx:qasm3Parser.AnnotationContext):
        pass

    # Exit a parse tree produced by qasm3Parser#annotation.
    def exitAnnotation(self, ctx:qasm3Parser.AnnotationContext):
        pass


    # Enter a parse tree produced by qasm3Parser#scope.
    def enterScope(self, ctx:qasm3Parser.ScopeContext):
        pass

    # Exit a parse tree produced by qasm3Parser#scope.
    def exitScope(self, ctx:qasm3Parser.ScopeContext):
        pass


    # Enter a parse tree produced by qasm3Parser#pragma.
    def enterPragma(self, ctx:qasm3Parser.PragmaContext):
        pass

    # Exit a parse tree produced by qasm3Parser#pragma.
    def exitPragma(self, ctx:qasm3Parser.PragmaContext):
        pass


    # Enter a parse tree produced by qasm3Parser#statementOrScope.
    def enterStatementOrScope(self, ctx:qasm3Parser.StatementOrScopeContext):
        pass

    # Exit a parse tree produced by qasm3Parser#statementOrScope.
    def exitStatementOrScope(self, ctx:qasm3Parser.StatementOrScopeContext):
        pass


    # Enter a parse tree produced by qasm3Parser#calibrationGrammarStatement.
    def enterCalibrationGrammarStatement(self, ctx:qasm3Parser.CalibrationGrammarStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#calibrationGrammarStatement.
    def exitCalibrationGrammarStatement(self, ctx:qasm3Parser.CalibrationGrammarStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#includeStatement.
    def enterIncludeStatement(self, ctx:qasm3Parser.IncludeStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#includeStatement.
    def exitIncludeStatement(self, ctx:qasm3Parser.IncludeStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#breakStatement.
    def enterBreakStatement(self, ctx:qasm3Parser.BreakStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#breakStatement.
    def exitBreakStatement(self, ctx:qasm3Parser.BreakStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#continueStatement.
    def enterContinueStatement(self, ctx:qasm3Parser.ContinueStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#continueStatement.
    def exitContinueStatement(self, ctx:qasm3Parser.ContinueStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#endStatement.
    def enterEndStatement(self, ctx:qasm3Parser.EndStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#endStatement.
    def exitEndStatement(self, ctx:qasm3Parser.EndStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#forStatement.
    def enterForStatement(self, ctx:qasm3Parser.ForStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#forStatement.
    def exitForStatement(self, ctx:qasm3Parser.ForStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#ifStatement.
    def enterIfStatement(self, ctx:qasm3Parser.IfStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#ifStatement.
    def exitIfStatement(self, ctx:qasm3Parser.IfStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#returnStatement.
    def enterReturnStatement(self, ctx:qasm3Parser.ReturnStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#returnStatement.
    def exitReturnStatement(self, ctx:qasm3Parser.ReturnStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#whileStatement.
    def enterWhileStatement(self, ctx:qasm3Parser.WhileStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#whileStatement.
    def exitWhileStatement(self, ctx:qasm3Parser.WhileStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#switchStatement.
    def enterSwitchStatement(self, ctx:qasm3Parser.SwitchStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#switchStatement.
    def exitSwitchStatement(self, ctx:qasm3Parser.SwitchStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#switchCaseItem.
    def enterSwitchCaseItem(self, ctx:qasm3Parser.SwitchCaseItemContext):
        pass

    # Exit a parse tree produced by qasm3Parser#switchCaseItem.
    def exitSwitchCaseItem(self, ctx:qasm3Parser.SwitchCaseItemContext):
        pass


    # Enter a parse tree produced by qasm3Parser#barrierStatement.
    def enterBarrierStatement(self, ctx:qasm3Parser.BarrierStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#barrierStatement.
    def exitBarrierStatement(self, ctx:qasm3Parser.BarrierStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#boxStatement.
    def enterBoxStatement(self, ctx:qasm3Parser.BoxStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#boxStatement.
    def exitBoxStatement(self, ctx:qasm3Parser.BoxStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#delayStatement.
    def enterDelayStatement(self, ctx:qasm3Parser.DelayStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#delayStatement.
    def exitDelayStatement(self, ctx:qasm3Parser.DelayStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#gateCallStatement.
    def enterGateCallStatement(self, ctx:qasm3Parser.GateCallStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#gateCallStatement.
    def exitGateCallStatement(self, ctx:qasm3Parser.GateCallStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#measureArrowAssignmentStatement.
    def enterMeasureArrowAssignmentStatement(self, ctx:qasm3Parser.MeasureArrowAssignmentStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#measureArrowAssignmentStatement.
    def exitMeasureArrowAssignmentStatement(self, ctx:qasm3Parser.MeasureArrowAssignmentStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#resetStatement.
    def enterResetStatement(self, ctx:qasm3Parser.ResetStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#resetStatement.
    def exitResetStatement(self, ctx:qasm3Parser.ResetStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#aliasDeclarationStatement.
    def enterAliasDeclarationStatement(self, ctx:qasm3Parser.AliasDeclarationStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#aliasDeclarationStatement.
    def exitAliasDeclarationStatement(self, ctx:qasm3Parser.AliasDeclarationStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#classicalDeclarationStatement.
    def enterClassicalDeclarationStatement(self, ctx:qasm3Parser.ClassicalDeclarationStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#classicalDeclarationStatement.
    def exitClassicalDeclarationStatement(self, ctx:qasm3Parser.ClassicalDeclarationStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#constDeclarationStatement.
    def enterConstDeclarationStatement(self, ctx:qasm3Parser.ConstDeclarationStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#constDeclarationStatement.
    def exitConstDeclarationStatement(self, ctx:qasm3Parser.ConstDeclarationStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#ioDeclarationStatement.
    def enterIoDeclarationStatement(self, ctx:qasm3Parser.IoDeclarationStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#ioDeclarationStatement.
    def exitIoDeclarationStatement(self, ctx:qasm3Parser.IoDeclarationStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#oldStyleDeclarationStatement.
    def enterOldStyleDeclarationStatement(self, ctx:qasm3Parser.OldStyleDeclarationStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#oldStyleDeclarationStatement.
    def exitOldStyleDeclarationStatement(self, ctx:qasm3Parser.OldStyleDeclarationStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#quantumDeclarationStatement.
    def enterQuantumDeclarationStatement(self, ctx:qasm3Parser.QuantumDeclarationStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#quantumDeclarationStatement.
    def exitQuantumDeclarationStatement(self, ctx:qasm3Parser.QuantumDeclarationStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#defStatement.
    def enterDefStatement(self, ctx:qasm3Parser.DefStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#defStatement.
    def exitDefStatement(self, ctx:qasm3Parser.DefStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#externStatement.
    def enterExternStatement(self, ctx:qasm3Parser.ExternStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#externStatement.
    def exitExternStatement(self, ctx:qasm3Parser.ExternStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#gateStatement.
    def enterGateStatement(self, ctx:qasm3Parser.GateStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#gateStatement.
    def exitGateStatement(self, ctx:qasm3Parser.GateStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#assignmentStatement.
    def enterAssignmentStatement(self, ctx:qasm3Parser.AssignmentStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#assignmentStatement.
    def exitAssignmentStatement(self, ctx:qasm3Parser.AssignmentStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#expressionStatement.
    def enterExpressionStatement(self, ctx:qasm3Parser.ExpressionStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#expressionStatement.
    def exitExpressionStatement(self, ctx:qasm3Parser.ExpressionStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#calStatement.
    def enterCalStatement(self, ctx:qasm3Parser.CalStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#calStatement.
    def exitCalStatement(self, ctx:qasm3Parser.CalStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#defcalStatement.
    def enterDefcalStatement(self, ctx:qasm3Parser.DefcalStatementContext):
        pass

    # Exit a parse tree produced by qasm3Parser#defcalStatement.
    def exitDefcalStatement(self, ctx:qasm3Parser.DefcalStatementContext):
        pass


    # Enter a parse tree produced by qasm3Parser#bitwiseXorExpression.
    def enterBitwiseXorExpression(self, ctx:qasm3Parser.BitwiseXorExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#bitwiseXorExpression.
    def exitBitwiseXorExpression(self, ctx:qasm3Parser.BitwiseXorExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#additiveExpression.
    def enterAdditiveExpression(self, ctx:qasm3Parser.AdditiveExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#additiveExpression.
    def exitAdditiveExpression(self, ctx:qasm3Parser.AdditiveExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#durationofExpression.
    def enterDurationofExpression(self, ctx:qasm3Parser.DurationofExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#durationofExpression.
    def exitDurationofExpression(self, ctx:qasm3Parser.DurationofExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#parenthesisExpression.
    def enterParenthesisExpression(self, ctx:qasm3Parser.ParenthesisExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#parenthesisExpression.
    def exitParenthesisExpression(self, ctx:qasm3Parser.ParenthesisExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#comparisonExpression.
    def enterComparisonExpression(self, ctx:qasm3Parser.ComparisonExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#comparisonExpression.
    def exitComparisonExpression(self, ctx:qasm3Parser.ComparisonExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#multiplicativeExpression.
    def enterMultiplicativeExpression(self, ctx:qasm3Parser.MultiplicativeExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#multiplicativeExpression.
    def exitMultiplicativeExpression(self, ctx:qasm3Parser.MultiplicativeExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#logicalOrExpression.
    def enterLogicalOrExpression(self, ctx:qasm3Parser.LogicalOrExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#logicalOrExpression.
    def exitLogicalOrExpression(self, ctx:qasm3Parser.LogicalOrExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#castExpression.
    def enterCastExpression(self, ctx:qasm3Parser.CastExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#castExpression.
    def exitCastExpression(self, ctx:qasm3Parser.CastExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#powerExpression.
    def enterPowerExpression(self, ctx:qasm3Parser.PowerExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#powerExpression.
    def exitPowerExpression(self, ctx:qasm3Parser.PowerExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#bitwiseOrExpression.
    def enterBitwiseOrExpression(self, ctx:qasm3Parser.BitwiseOrExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#bitwiseOrExpression.
    def exitBitwiseOrExpression(self, ctx:qasm3Parser.BitwiseOrExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#callExpression.
    def enterCallExpression(self, ctx:qasm3Parser.CallExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#callExpression.
    def exitCallExpression(self, ctx:qasm3Parser.CallExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#bitshiftExpression.
    def enterBitshiftExpression(self, ctx:qasm3Parser.BitshiftExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#bitshiftExpression.
    def exitBitshiftExpression(self, ctx:qasm3Parser.BitshiftExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#bitwiseAndExpression.
    def enterBitwiseAndExpression(self, ctx:qasm3Parser.BitwiseAndExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#bitwiseAndExpression.
    def exitBitwiseAndExpression(self, ctx:qasm3Parser.BitwiseAndExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#equalityExpression.
    def enterEqualityExpression(self, ctx:qasm3Parser.EqualityExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#equalityExpression.
    def exitEqualityExpression(self, ctx:qasm3Parser.EqualityExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#logicalAndExpression.
    def enterLogicalAndExpression(self, ctx:qasm3Parser.LogicalAndExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#logicalAndExpression.
    def exitLogicalAndExpression(self, ctx:qasm3Parser.LogicalAndExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#indexExpression.
    def enterIndexExpression(self, ctx:qasm3Parser.IndexExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#indexExpression.
    def exitIndexExpression(self, ctx:qasm3Parser.IndexExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#unaryExpression.
    def enterUnaryExpression(self, ctx:qasm3Parser.UnaryExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#unaryExpression.
    def exitUnaryExpression(self, ctx:qasm3Parser.UnaryExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#literalExpression.
    def enterLiteralExpression(self, ctx:qasm3Parser.LiteralExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#literalExpression.
    def exitLiteralExpression(self, ctx:qasm3Parser.LiteralExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#aliasExpression.
    def enterAliasExpression(self, ctx:qasm3Parser.AliasExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#aliasExpression.
    def exitAliasExpression(self, ctx:qasm3Parser.AliasExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#declarationExpression.
    def enterDeclarationExpression(self, ctx:qasm3Parser.DeclarationExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#declarationExpression.
    def exitDeclarationExpression(self, ctx:qasm3Parser.DeclarationExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#measureExpression.
    def enterMeasureExpression(self, ctx:qasm3Parser.MeasureExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#measureExpression.
    def exitMeasureExpression(self, ctx:qasm3Parser.MeasureExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#rangeExpression.
    def enterRangeExpression(self, ctx:qasm3Parser.RangeExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#rangeExpression.
    def exitRangeExpression(self, ctx:qasm3Parser.RangeExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#setExpression.
    def enterSetExpression(self, ctx:qasm3Parser.SetExpressionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#setExpression.
    def exitSetExpression(self, ctx:qasm3Parser.SetExpressionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#arrayLiteral.
    def enterArrayLiteral(self, ctx:qasm3Parser.ArrayLiteralContext):
        pass

    # Exit a parse tree produced by qasm3Parser#arrayLiteral.
    def exitArrayLiteral(self, ctx:qasm3Parser.ArrayLiteralContext):
        pass


    # Enter a parse tree produced by qasm3Parser#indexOperator.
    def enterIndexOperator(self, ctx:qasm3Parser.IndexOperatorContext):
        pass

    # Exit a parse tree produced by qasm3Parser#indexOperator.
    def exitIndexOperator(self, ctx:qasm3Parser.IndexOperatorContext):
        pass


    # Enter a parse tree produced by qasm3Parser#indexedIdentifier.
    def enterIndexedIdentifier(self, ctx:qasm3Parser.IndexedIdentifierContext):
        pass

    # Exit a parse tree produced by qasm3Parser#indexedIdentifier.
    def exitIndexedIdentifier(self, ctx:qasm3Parser.IndexedIdentifierContext):
        pass


    # Enter a parse tree produced by qasm3Parser#returnSignature.
    def enterReturnSignature(self, ctx:qasm3Parser.ReturnSignatureContext):
        pass

    # Exit a parse tree produced by qasm3Parser#returnSignature.
    def exitReturnSignature(self, ctx:qasm3Parser.ReturnSignatureContext):
        pass


    # Enter a parse tree produced by qasm3Parser#gateModifier.
    def enterGateModifier(self, ctx:qasm3Parser.GateModifierContext):
        pass

    # Exit a parse tree produced by qasm3Parser#gateModifier.
    def exitGateModifier(self, ctx:qasm3Parser.GateModifierContext):
        pass


    # Enter a parse tree produced by qasm3Parser#scalarType.
    def enterScalarType(self, ctx:qasm3Parser.ScalarTypeContext):
        pass

    # Exit a parse tree produced by qasm3Parser#scalarType.
    def exitScalarType(self, ctx:qasm3Parser.ScalarTypeContext):
        pass


    # Enter a parse tree produced by qasm3Parser#qubitType.
    def enterQubitType(self, ctx:qasm3Parser.QubitTypeContext):
        pass

    # Exit a parse tree produced by qasm3Parser#qubitType.
    def exitQubitType(self, ctx:qasm3Parser.QubitTypeContext):
        pass


    # Enter a parse tree produced by qasm3Parser#arrayType.
    def enterArrayType(self, ctx:qasm3Parser.ArrayTypeContext):
        pass

    # Exit a parse tree produced by qasm3Parser#arrayType.
    def exitArrayType(self, ctx:qasm3Parser.ArrayTypeContext):
        pass


    # Enter a parse tree produced by qasm3Parser#arrayReferenceType.
    def enterArrayReferenceType(self, ctx:qasm3Parser.ArrayReferenceTypeContext):
        pass

    # Exit a parse tree produced by qasm3Parser#arrayReferenceType.
    def exitArrayReferenceType(self, ctx:qasm3Parser.ArrayReferenceTypeContext):
        pass


    # Enter a parse tree produced by qasm3Parser#designator.
    def enterDesignator(self, ctx:qasm3Parser.DesignatorContext):
        pass

    # Exit a parse tree produced by qasm3Parser#designator.
    def exitDesignator(self, ctx:qasm3Parser.DesignatorContext):
        pass


    # Enter a parse tree produced by qasm3Parser#defcalTarget.
    def enterDefcalTarget(self, ctx:qasm3Parser.DefcalTargetContext):
        pass

    # Exit a parse tree produced by qasm3Parser#defcalTarget.
    def exitDefcalTarget(self, ctx:qasm3Parser.DefcalTargetContext):
        pass


    # Enter a parse tree produced by qasm3Parser#defcalArgumentDefinition.
    def enterDefcalArgumentDefinition(self, ctx:qasm3Parser.DefcalArgumentDefinitionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#defcalArgumentDefinition.
    def exitDefcalArgumentDefinition(self, ctx:qasm3Parser.DefcalArgumentDefinitionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#defcalOperand.
    def enterDefcalOperand(self, ctx:qasm3Parser.DefcalOperandContext):
        pass

    # Exit a parse tree produced by qasm3Parser#defcalOperand.
    def exitDefcalOperand(self, ctx:qasm3Parser.DefcalOperandContext):
        pass


    # Enter a parse tree produced by qasm3Parser#gateOperand.
    def enterGateOperand(self, ctx:qasm3Parser.GateOperandContext):
        pass

    # Exit a parse tree produced by qasm3Parser#gateOperand.
    def exitGateOperand(self, ctx:qasm3Parser.GateOperandContext):
        pass


    # Enter a parse tree produced by qasm3Parser#externArgument.
    def enterExternArgument(self, ctx:qasm3Parser.ExternArgumentContext):
        pass

    # Exit a parse tree produced by qasm3Parser#externArgument.
    def exitExternArgument(self, ctx:qasm3Parser.ExternArgumentContext):
        pass


    # Enter a parse tree produced by qasm3Parser#argumentDefinition.
    def enterArgumentDefinition(self, ctx:qasm3Parser.ArgumentDefinitionContext):
        pass

    # Exit a parse tree produced by qasm3Parser#argumentDefinition.
    def exitArgumentDefinition(self, ctx:qasm3Parser.ArgumentDefinitionContext):
        pass


    # Enter a parse tree produced by qasm3Parser#argumentDefinitionList.
    def enterArgumentDefinitionList(self, ctx:qasm3Parser.ArgumentDefinitionListContext):
        pass

    # Exit a parse tree produced by qasm3Parser#argumentDefinitionList.
    def exitArgumentDefinitionList(self, ctx:qasm3Parser.ArgumentDefinitionListContext):
        pass


    # Enter a parse tree produced by qasm3Parser#defcalArgumentDefinitionList.
    def enterDefcalArgumentDefinitionList(self, ctx:qasm3Parser.DefcalArgumentDefinitionListContext):
        pass

    # Exit a parse tree produced by qasm3Parser#defcalArgumentDefinitionList.
    def exitDefcalArgumentDefinitionList(self, ctx:qasm3Parser.DefcalArgumentDefinitionListContext):
        pass


    # Enter a parse tree produced by qasm3Parser#defcalOperandList.
    def enterDefcalOperandList(self, ctx:qasm3Parser.DefcalOperandListContext):
        pass

    # Exit a parse tree produced by qasm3Parser#defcalOperandList.
    def exitDefcalOperandList(self, ctx:qasm3Parser.DefcalOperandListContext):
        pass


    # Enter a parse tree produced by qasm3Parser#expressionList.
    def enterExpressionList(self, ctx:qasm3Parser.ExpressionListContext):
        pass

    # Exit a parse tree produced by qasm3Parser#expressionList.
    def exitExpressionList(self, ctx:qasm3Parser.ExpressionListContext):
        pass


    # Enter a parse tree produced by qasm3Parser#identifierList.
    def enterIdentifierList(self, ctx:qasm3Parser.IdentifierListContext):
        pass

    # Exit a parse tree produced by qasm3Parser#identifierList.
    def exitIdentifierList(self, ctx:qasm3Parser.IdentifierListContext):
        pass


    # Enter a parse tree produced by qasm3Parser#gateOperandList.
    def enterGateOperandList(self, ctx:qasm3Parser.GateOperandListContext):
        pass

    # Exit a parse tree produced by qasm3Parser#gateOperandList.
    def exitGateOperandList(self, ctx:qasm3Parser.GateOperandListContext):
        pass


    # Enter a parse tree produced by qasm3Parser#externArgumentList.
    def enterExternArgumentList(self, ctx:qasm3Parser.ExternArgumentListContext):
        pass

    # Exit a parse tree produced by qasm3Parser#externArgumentList.
    def exitExternArgumentList(self, ctx:qasm3Parser.ExternArgumentListContext):
        pass



del qasm3Parser