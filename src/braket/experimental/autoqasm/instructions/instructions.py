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


"""Non-unitary instructions that apply to qubits."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import oqpy

from braket.experimental.autoqasm import program as aq_program
from braket.experimental.autoqasm import types as aq_types
from braket.experimental.autoqasm.instructions.qubits import _qubit
from braket.experimental.autoqasm.types import QubitIdentifierType


def _qubit_instruction(
    name: str,
    qubits: Iterable[QubitIdentifierType],
    *args: Any,
    is_unitary: bool = True,
    control: QubitIdentifierType | Iterable[QubitIdentifierType] | None = None,
    control_state: str | None = None,
    power: float | None = None,
) -> None:
    program_conversion_context = aq_program.get_program_conversion_context()
    program_conversion_context.validate_gate_targets(qubits, args)

    # Add the instruction to the program.
    program_conversion_context.register_gate(name)
    program_conversion_context.register_args(args)
    program_mode = aq_program.ProgramMode.UNITARY if is_unitary else aq_program.ProgramMode.NONE
    pos_control, neg_control = _get_pos_neg_control(control, control_state)
    oqpy_program = program_conversion_context.get_oqpy_program(mode=program_mode)
    oqpy_program.gate(
        [_qubit(q) for q in qubits],
        name,
        *args,
        control=pos_control,
        neg_control=neg_control,
        exp=power,
    )


def _get_pos_neg_control(
    control: QubitIdentifierType | Iterable[QubitIdentifierType] | None = None,
    control_state: str | None = None,
) -> tuple[list[oqpy.Qubit], list[oqpy.Qubit]]:
    if control is None and control_state is not None:
        raise ValueError(control_state, "control_state provided without control qubits")

    if control is None:
        return None, None

    if aq_types.is_qubit_identifier_type(control):
        control = [control]

    if control_state is not None and len(control) != len(control_state):
        raise ValueError(control_state, "control and control_state must have same length")

    pos_control = [
        _qubit(q) for i, q in enumerate(control) if control_state is None or control_state[i] == "1"
    ]
    neg_control = [
        _qubit(q)
        for i, q in enumerate(control)
        if control_state is not None and control_state[i] == "0"
    ]
    return pos_control, neg_control


def reset(target: QubitIdentifierType) -> None:
    """Adds a reset instruction on a specified qubit.

    Args:
        target (QubitIdentifierType): The target qubit.
    """
    _qubit_instruction("reset", [target], is_unitary=False)
