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

"""AutoQASM types and type utilities."""

from __future__ import annotations

from typing import Any, Iterable, Optional

import oqpy
import oqpy.base
from openpulse import ast

from braket.circuits import FreeParameterExpression
from braket.experimental.autoqasm import errors, program


def is_qasm_type(val: Any) -> bool:
    """Returns whether the provided object is of a QASM type or is itself a QASM type
    which receives special treatment by AutoQASM.

    Args:
        val (Any): The object of which to check the type.

    Returns:
        bool: Whether the object is a QASM type.
    """
    qasm_types = (oqpy.Range, oqpy._ClassicalVar, oqpy.base.OQPyExpression, FreeParameterExpression)
    # The input can either be a class, like oqpy.Range ...
    if type(val) is type:
        return issubclass(val, qasm_types)
    # ... or an instance of a class, like oqpy.Range(10)
    return isinstance(val, qasm_types)


class QasmRange(oqpy.Range):
    def __init__(
        self,
        start: int,
        stop: Optional[int] = None,
        step: Optional[int] = 1,
        annotations: Optional[Iterable[str | tuple[str, str]]] = None,
    ):
        """Creates a range definition.

        Args:
            start (int): Start of the range.
            stop (Optional[int]): End of the range. Defaults to None.
            step (Optional[int]): Step of the range. Defaults to 1.
            annotations (Optional[Iterable[str | tuple[str, str]]]): Annotations for the range.
                The annotations can be either a string or a tuple of the form
                (annotation_name, annotation_value).
        """
        if stop is None:
            stop = start
            start = 0
        super(QasmRange, self).__init__(start, stop, step)
        self.annotations = annotations or []


class ArrayVar(oqpy.ArrayVar):
    def __init__(self, *args, **kwargs):
        if (
            program.get_program_conversion_context().subroutines_processing
            or not program.get_program_conversion_context().at_function_root_scope
        ):
            raise errors.InvalidArrayDeclaration(
                "Arrays may only be declared at the root scope of an AutoQASM main function."
            )
        super(ArrayVar, self).__init__(*args, **kwargs)
        self.name = program.get_program_conversion_context().next_var_name(oqpy.ArrayVar)


class BitVar(oqpy.BitVar):
    def __init__(self, *args, **kwargs):
        super(BitVar, self).__init__(*args, **kwargs)
        self.name = program.get_program_conversion_context().next_var_name(oqpy.BitVar)
        if self.size:
            value = self.init_expression or 0
            self.init_expression = ast.BitstringLiteral(value, self.size)


class BoolVar(oqpy.BoolVar):
    def __init__(self, *args, **kwargs):
        super(BoolVar, self).__init__(*args, **kwargs)
        self.name = program.get_program_conversion_context().next_var_name(oqpy.BoolVar)


class FloatVar(oqpy.FloatVar):
    def __init__(self, *args, **kwargs):
        super(FloatVar, self).__init__(*args, **kwargs)
        self.name = program.get_program_conversion_context().next_var_name(oqpy.FloatVar)


class IntVar(oqpy.IntVar):
    def __init__(self, *args, **kwargs):
        super(IntVar, self).__init__(*args, **kwargs)
        self.name = program.get_program_conversion_context().next_var_name(oqpy.IntVar)
