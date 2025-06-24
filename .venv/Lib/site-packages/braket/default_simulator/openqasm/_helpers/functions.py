# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

"""
Evaluating expressions
"""

from ..parser.openqasm_ast import (
    ArrayLiteral,
    AssignmentOperator,
    BinaryOperator,
    BooleanLiteral,
    FloatLiteral,
    IntegerLiteral,
    SymbolLiteral,
    UnaryOperator,
)
from .builtins import BuiltinConstants, BuiltinFunctions
from .casting import LiteralType, convert_bool_array_to_string

operator_maps = {
    IntegerLiteral: {
        # returns int
        getattr(BinaryOperator, "+"): lambda x, y: IntegerLiteral(x.value + y.value),
        getattr(BinaryOperator, "-"): lambda x, y: IntegerLiteral(x.value - y.value),
        getattr(BinaryOperator, "*"): lambda x, y: IntegerLiteral(x.value * y.value),
        getattr(BinaryOperator, "/"): lambda x, y: IntegerLiteral(x.value // y.value),
        getattr(BinaryOperator, "%"): lambda x, y: IntegerLiteral(x.value % y.value),
        getattr(BinaryOperator, "**"): lambda x, y: IntegerLiteral(x.value**y.value),
        getattr(UnaryOperator, "-"): lambda x: IntegerLiteral(-x.value),
        # returns bool
        getattr(BinaryOperator, ">"): lambda x, y: BooleanLiteral(x.value > y.value),
        getattr(BinaryOperator, "<"): lambda x, y: BooleanLiteral(x.value < y.value),
        getattr(BinaryOperator, ">="): lambda x, y: BooleanLiteral(x.value >= y.value),
        getattr(BinaryOperator, "<="): lambda x, y: BooleanLiteral(x.value <= y.value),
        getattr(BinaryOperator, "=="): lambda x, y: BooleanLiteral(x.value == y.value),
        getattr(BinaryOperator, "!="): lambda x, y: BooleanLiteral(x.value != y.value),
    },
    FloatLiteral: {
        # returns real
        getattr(BinaryOperator, "+"): lambda x, y: FloatLiteral(x.value + y.value),
        getattr(BinaryOperator, "-"): lambda x, y: FloatLiteral(x.value - y.value),
        getattr(BinaryOperator, "*"): lambda x, y: FloatLiteral(x.value * y.value),
        getattr(BinaryOperator, "/"): lambda x, y: FloatLiteral(x.value / y.value),
        getattr(BinaryOperator, "**"): lambda x, y: FloatLiteral(x.value**y.value),
        getattr(UnaryOperator, "-"): lambda x: FloatLiteral(-x.value),
        # returns bool
        getattr(BinaryOperator, ">"): lambda x, y: BooleanLiteral(x.value > y.value),
        getattr(BinaryOperator, "<"): lambda x, y: BooleanLiteral(x.value < y.value),
        getattr(BinaryOperator, ">="): lambda x, y: BooleanLiteral(x.value >= y.value),
        getattr(BinaryOperator, "<="): lambda x, y: BooleanLiteral(x.value <= y.value),
        getattr(BinaryOperator, "=="): lambda x, y: BooleanLiteral(x.value == y.value),
        getattr(BinaryOperator, "!="): lambda x, y: BooleanLiteral(x.value != y.value),
    },
    SymbolLiteral: {
        # returns real
        getattr(BinaryOperator, "+"): lambda x, y: SymbolLiteral(x.value + y.value),
        getattr(BinaryOperator, "-"): lambda x, y: SymbolLiteral(x.value - y.value),
        getattr(BinaryOperator, "*"): lambda x, y: SymbolLiteral(x.value * y.value),
        getattr(BinaryOperator, "/"): lambda x, y: SymbolLiteral(x.value / y.value),
        getattr(BinaryOperator, "**"): lambda x, y: SymbolLiteral(x.value**y.value),
        getattr(UnaryOperator, "-"): lambda x: SymbolLiteral(-x.value),
    },
    BooleanLiteral: {
        # returns bool
        getattr(BinaryOperator, "&"): lambda x, y: BooleanLiteral(x.value and y.value),
        getattr(BinaryOperator, "|"): lambda x, y: BooleanLiteral(x.value or y.value),
        getattr(BinaryOperator, "^"): lambda x, y: BooleanLiteral(x.value ^ y.value),
        getattr(BinaryOperator, "&&"): lambda x, y: BooleanLiteral(x.value and y.value),
        getattr(BinaryOperator, "||"): lambda x, y: BooleanLiteral(x.value or y.value),
        getattr(BinaryOperator, ">"): lambda x, y: BooleanLiteral(x.value > y.value),
        getattr(BinaryOperator, "<"): lambda x, y: BooleanLiteral(x.value < y.value),
        getattr(BinaryOperator, ">="): lambda x, y: BooleanLiteral(x.value >= y.value),
        getattr(BinaryOperator, "<="): lambda x, y: BooleanLiteral(x.value <= y.value),
        getattr(BinaryOperator, "=="): lambda x, y: BooleanLiteral(x.value == y.value),
        getattr(BinaryOperator, "!="): lambda x, y: BooleanLiteral(x.value != y.value),
        getattr(UnaryOperator, "!"): lambda x: BooleanLiteral(not x.value),
    },
    # Array literals are only used to store bit registers
    ArrayLiteral: {
        # returns array
        getattr(BinaryOperator, "&"): lambda x, y: ArrayLiteral(
            [BooleanLiteral(xv.value and yv.value) for xv, yv in zip(x.values, y.values)]
        ),
        getattr(BinaryOperator, "|"): lambda x, y: ArrayLiteral(
            [BooleanLiteral(xv.value or yv.value) for xv, yv in zip(x.values, y.values)]
        ),
        getattr(BinaryOperator, "^"): lambda x, y: ArrayLiteral(
            [BooleanLiteral(xv.value ^ yv.value) for xv, yv in zip(x.values, y.values)]
        ),
        getattr(BinaryOperator, "<<"): lambda x, y: ArrayLiteral(
            x.values[y.value :] + [BooleanLiteral(False) for _ in range(y.value)]
        ),
        getattr(BinaryOperator, ">>"): lambda x, y: ArrayLiteral(
            [BooleanLiteral(False) for _ in range(y.value)] + x.values[: len(x.values) - y.value]
        ),
        getattr(UnaryOperator, "~"): lambda x: ArrayLiteral(
            [BooleanLiteral(not v.value) for v in x.values]
        ),
        # returns bool
        getattr(BinaryOperator, ">"): lambda x, y: BooleanLiteral(
            convert_bool_array_to_string(x) > convert_bool_array_to_string(y)
        ),
        getattr(BinaryOperator, "<"): lambda x, y: BooleanLiteral(
            convert_bool_array_to_string(x) < convert_bool_array_to_string(y)
        ),
        getattr(BinaryOperator, ">="): lambda x, y: BooleanLiteral(
            convert_bool_array_to_string(x) >= convert_bool_array_to_string(y)
        ),
        getattr(BinaryOperator, "<="): lambda x, y: BooleanLiteral(
            convert_bool_array_to_string(x) <= convert_bool_array_to_string(y)
        ),
        getattr(BinaryOperator, "=="): lambda x, y: BooleanLiteral(
            convert_bool_array_to_string(x) == convert_bool_array_to_string(y)
        ),
        getattr(BinaryOperator, "!="): lambda x, y: BooleanLiteral(
            convert_bool_array_to_string(x) != convert_bool_array_to_string(y)
        ),
        getattr(UnaryOperator, "!"): lambda x: BooleanLiteral(not any(v.value for v in x.values)),
    },
}

type_hierarchy = (
    BooleanLiteral,
    IntegerLiteral,
    FloatLiteral,
    ArrayLiteral,
    SymbolLiteral,
)


builtin_constants = {
    "pi": BuiltinConstants.PI.value,
    "π": BuiltinConstants.PI.value,
    "tau": BuiltinConstants.TAU.value,
    "τ": BuiltinConstants.TAU.value,
    "euler": BuiltinConstants.E.value,
    "ℇ": BuiltinConstants.E.value,
}


builtin_functions = {
    function_name: getattr(BuiltinFunctions, function_name)
    for function_name in dir(BuiltinFunctions)
    if not function_name.startswith("__")
}


def resolve_type_hierarchy(x: LiteralType, y: LiteralType) -> type[LiteralType]:
    """Determine output type of expression, for example: 1 + 1.0 == 2.0"""
    return max(type(x), type(y), key=type_hierarchy.index)


def evaluate_binary_expression(
    lhs: LiteralType, rhs: LiteralType, op: BinaryOperator
) -> LiteralType:
    """Evaluate a binary expression between two literals"""
    result_type = resolve_type_hierarchy(lhs, rhs)
    func = operator_maps[result_type].get(op)
    if not func:
        raise TypeError(f"Invalid operator {op.name} for {result_type.__name__}")
    return func(lhs, rhs)


def evaluate_unary_expression(expression: LiteralType, op: BinaryOperator) -> LiteralType:
    """Evaluate a unary expression on a literal"""
    expression_type = type(expression)
    func = operator_maps[expression_type].get(op)
    if not func:
        raise TypeError(f"Invalid operator {op.name} for {expression_type.__name__}")
    return func(expression)


def get_operator_of_assignment_operator(assignment_operator: AssignmentOperator) -> BinaryOperator:
    """Extract the binary operator related to an assignment operator, for example: += -> +"""
    return getattr(BinaryOperator, assignment_operator.name[:-1])
