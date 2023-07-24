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

"""Quantum measurement on qubits.

Example of measuring qubit 0:

.. code-block:: python

    @aq.function
    def my_program():
        measure(0)
"""


from typing import List, Union

from braket.experimental.autoqasm import program
from braket.experimental.autoqasm.gates.qubits import QubitIdentifierType, _qubit
from braket.experimental.autoqasm.types import BitVar


def measure(qubits: Union[QubitIdentifierType, List[QubitIdentifierType]]) -> BitVar:
    """Add qubit measurement statements to the program and assign the measurement
    results to bit variables.

    Args:
        qubits (Union[QubitIdentifierType, List[QubitIdentifierType]]): The target qubits
            to measure.

    Returns:
        BitVar: Bit variable the measurement results are assigned to.
    """
    if not isinstance(qubits, List):
        qubits = [qubits]

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()

    bit_var_size = len(qubits) if len(qubits) > 1 else None
    bit_var = BitVar(
        name=program.get_program_conversion_context().next_var_name(BitVar),
        size=bit_var_size,
        needs_declaration=True,
    )
    oqpy_program.declare(bit_var)

    qubits = [_qubit(qubit) for qubit in qubits]
    if len(qubits) == 1:
        oqpy_program.measure(qubits[0], bit_var)
    else:
        for idx, qubit in enumerate(qubits):
            oqpy_program.measure(qubit, bit_var[idx])

    return bit_var
