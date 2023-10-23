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


"""Non-unitary instructions that apply to qubits.
"""

from typing import Any

from braket.experimental.autoqasm import program as aq_program

from .qubits import QubitIdentifierType, _qubit


def _qubit_instruction(
    name: str, qubits: list[QubitIdentifierType], *args: Any, is_unitary: bool = True
) -> None:
    program_conversion_context = aq_program.get_program_conversion_context()
    program_conversion_context.validate_gate_targets(qubits, args)

    # Add the instruction to the program.
    program_conversion_context.register_gate(name)
    program_mode = aq_program.ProgramMode.UNITARY if is_unitary else aq_program.ProgramMode.NONE
    oqpy_program = program_conversion_context.get_oqpy_program(mode=program_mode)
    oqpy_program.gate([_qubit(q) for q in qubits], name, *args)


def reset(target: QubitIdentifierType) -> None:
    """Adds a reset instruction on a specified qubit.

    Args:
        target (QubitIdentifierType): The target qubit.
    """
    _qubit_instruction("reset", [target], is_unitary=False)
