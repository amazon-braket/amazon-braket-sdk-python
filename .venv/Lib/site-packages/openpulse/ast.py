"""

========================================
Abstract Syntax Tree (``openpulse.ast``)
========================================

.. currentmodule:: openpulse.ast

The reference abstract syntax tree (AST) for OpenPulse programs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union

# Re-export the existing AST classes from openqasm3
# This is everything _except_ CalibrationDefinition
# and CalibrationStatement, which get redefined below.
from openqasm3.ast import (
    AccessControl,
    AliasStatement,
    AngleType,
    Annotation,
    ArrayLiteral,
    ArrayReferenceType,
    ArrayType,
    AssignmentOperator,
    BinaryExpression,
    BinaryOperator,
    BitType,
    BitstringLiteral,
    BoolType,
    BooleanLiteral,
    Box,
    BranchingStatement,
    BreakStatement,
    CalibrationGrammarDeclaration,
    Cast,
    ClassicalArgument,
    ClassicalAssignment,
    ClassicalDeclaration,
    ClassicalType,
    ComplexType,
    Concatenation,
    ConstantDeclaration,
    ContinueStatement,
    DelayInstruction,
    DiscreteSet,
    DurationLiteral,
    DurationOf,
    DurationType,
    EndStatement,
    Expression,
    ExpressionStatement,
    ExternArgument,
    ExternDeclaration,
    FloatLiteral,
    FloatType,
    ForInLoop,
    FunctionCall,
    GateModifierName,
    IODeclaration,
    IOKeyword,
    Identifier,
    ImaginaryLiteral,
    Include,
    IndexExpression,
    IndexedIdentifier,
    IntType,
    IntegerLiteral,
    Pragma,
    Program,
    QASMNode,
    QuantumArgument,
    QuantumBarrier,
    QuantumGate,
    QuantumGateDefinition,
    QuantumGateModifier,
    QuantumMeasurement,
    QuantumMeasurementStatement,
    QuantumPhase,
    QuantumReset,
    QuantumStatement,
    QubitDeclaration,
    RangeDefinition,
    ReturnStatement,
    SizeOf,
    Span,
    Statement,
    SwitchStatement,
    CompoundStatement,
    StretchType,
    SubroutineDefinition,
    TimeUnit,
    UintType,
    UnaryExpression,
    UnaryOperator,
    WhileLoop,
)


# From Pulse grammar
@dataclass
class WaveformType(ClassicalType):
    """
    Leaf node representing the ``waveform`` type.
    """


@dataclass
class PortType(ClassicalType):
    """
    Leaf node representing the ``port`` type.
    """


@dataclass
class FrameType(ClassicalType):
    """
    Leaf node representing the ``frame`` type.
    """


@dataclass
class CalibrationBlock(QASMNode):
    """
    Node representing a calibration block.
    """

    body: List[Statement]


# Override the class from openqasm3
@dataclass
class CalibrationStatement(Statement):
    # pylint: disable=E0102
    """
    Cal block

    Example::

        cal {

            extern drag(complex[size], duration, duration, float[size]) -> waveform;
            extern gaussian_square(complex[size], duration, duration, duration) -> waveform;

            port q0 = getport("q", $0);
            port q1 = getport("q", $1);

            frame q0_frame = newframe(q0_freq, 0);
            frame q1_frame = newframe(q1_freq, 0);
        }
    """

    body: List[Union[Statement, Pragma]]


# Override the class from openqasm3
@dataclass
class CalibrationDefinition(Statement):
    # pylint: disable=E0102
    """
    Calibration definition

    Example::

        defcal rz(angle[20] theta) $q {
            shift_phase(drive($q), -theta);
        }
    """

    name: Identifier
    arguments: List[Union[ClassicalArgument, Expression]]
    qubits: List[Identifier]
    return_type: Optional[ClassicalType]
    body: List[Statement]


__all__ = [
    "AccessControl",
    "AliasStatement",
    "AngleType",
    "Annotation",
    "ArrayLiteral",
    "ArrayReferenceType",
    "ArrayType",
    "AssignmentOperator",
    "BinaryExpression",
    "BinaryOperator",
    "BitType",
    "BitstringLiteral",
    "BoolType",
    "BooleanLiteral",
    "Box",
    "BranchingStatement",
    "BreakStatement",
    "CalibrationBlock",
    "CalibrationDefinition",
    "CalibrationGrammarDeclaration",
    "CalibrationStatement",
    "Cast",
    "ClassicalArgument",
    "ClassicalAssignment",
    "ClassicalDeclaration",
    "ClassicalType",
    "ComplexType",
    "Concatenation",
    "ConstantDeclaration",
    "ContinueStatement",
    "DelayInstruction",
    "DiscreteSet",
    "DurationLiteral",
    "DurationOf",
    "DurationType",
    "EndStatement",
    "Expression",
    "ExpressionStatement",
    "ExternArgument",
    "ExternDeclaration",
    "FloatLiteral",
    "FloatType",
    "ForInLoop",
    "FrameType",
    "FunctionCall",
    "GateModifierName",
    "IODeclaration",
    "IOKeyword",
    "Identifier",
    "ImaginaryLiteral",
    "Include",
    "IndexExpression",
    "IndexedIdentifier",
    "IntType",
    "IntegerLiteral",
    "PortType",
    "Pragma",
    "Program",
    "QASMNode",
    "QuantumArgument",
    "QuantumBarrier",
    "QuantumGate",
    "QuantumGateDefinition",
    "QuantumGateModifier",
    "QuantumMeasurement",
    "QuantumMeasurementStatement",
    "QuantumPhase",
    "QuantumReset",
    "QuantumStatement",
    "QubitDeclaration",
    "RangeDefinition",
    "ReturnStatement",
    "SizeOf",
    "Span",
    "Statement",
    "SwitchStatement",
    "CompoundStatement",
    "StretchType",
    "SubroutineDefinition",
    "TimeUnit",
    "UintType",
    "UnaryExpression",
    "UnaryOperator",
    "WaveformType",
    "WhileLoop",
]
