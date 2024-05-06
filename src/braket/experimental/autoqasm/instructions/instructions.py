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

from braket.circuits.basis_state import BasisState, BasisStateInput
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
    control_state: BasisStateInput | None = None,
    power: float | None = None,
) -> None:
    """Adds an instruction to the program which acts on a specified set of qubits.

    Args:
        name (str): The name of the instruction.
        qubits (Iterable[QubitIdentifierType]): The qubits on which the instruction acts.
        is_unitary (bool): Whether the instruction represents a unitary operation. Defaults to True.
        control (QubitIdentifierType | Iterable[QubitIdentifierType] | None): The qubit or
            list of qubits which are being used as the control qubits. If None, an empty list is
            used, and the gate will not be controlled on any qubits. Defaults to None.
        control_state (BasisStateInput | None): The basis state of the control qubits
            that is required in order for the controlled gate to be performed. The order of the
            bits in this basis state corresponds to the order of the qubits provided in `control`.
            If None, the control state is assumed to be a bitstring of all 1s. Defaults to None.
        power (float | None): The power to which the gate should be raised. If None, the gate
            will not be raised to any power. Defaults to None.

    Note:
        The params `control`, `control_state`, and `power` are frequently passed as kwargs
        to this function from built-in gates defined in the `gates` module. This allows the
        signatures and docstrings for each built-in gate to be more concise, though at the cost
        of not having these gate modifier params explicitly documented for each gate.
    """
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
    control_state: BasisStateInput | None = None,
) -> tuple[list[oqpy.Qubit], list[oqpy.Qubit]]:
    """Constructs the list of positive-control and negative-control qubits given
    the list of control qubits and the corresponding control state. For the controlled gate
    to be performed, all of the positive-control qubits must be in the 1 state, and all of the
    negative-control qubits must be in the 0 state.

    Args:
        control (QubitIdentifierType | Iterable[QubitIdentifierType] | None): The qubit
            or list of qubits which are being used as the control qubits. If None, an empty list is
            used. Defaults to None.
        control_state (BasisStateInput | None): The basis state of the control qubits
            that is required in order for the controlled gate to be performed. The order of the
            bits in this basis state corresponds to the order of the qubits provided in `control`.
            If None, the control state is assumed to be a bitstring of all 1s. Defaults to None.

    Returns:
        tuple[list[Qubit], list[Qubit]]: A tuple of lists of `Qubit` objects, where the first list
        contains the positive-control qubits, and the second list contains the negative-control
        qubits. The union of the two lists is the same as the list of control qubits.
    """
    if control is None:
        control = []
    elif aq_types.is_qubit_identifier_type(control):
        control = [control]

    if control_state is None:
        control_state = [1] * len(control)
    else:
        control_state = BasisState(control_state, len(control)).as_tuple

    pos_control = [_qubit(q) for i, q in enumerate(control) if control_state[i] == 1]
    neg_control = [_qubit(q) for i, q in enumerate(control) if control_state[i] == 0]
    return pos_control, neg_control


def reset(target: QubitIdentifierType) -> None:
    """Adds a reset instruction on a specified qubit.

    Args:
        target (QubitIdentifierType): The target qubit.
    """
    _qubit_instruction("reset", [target], is_unitary=False)
