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


"""Quantum gates, which are applied to qubits. Some gates take parameters as arguments in addition
to the qubits.

Example of using a `h` gate and a `cnot` gate to create a Bell circuit:

.. code-block:: python

    @aq.function
    def bell():
        h(0)
        cnot(0, 1)
"""


from braket.experimental.autoqasm import program

from .qubits import QubitIdentifier, _qubit


def h(q: QubitIdentifier) -> None:
    """Adds a Hadamard gate to the program on the specified qubit.

    Args:
        q (QubitIdentifier): The target qubit.
    """
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(_qubit(q), "h")


def x(q: QubitIdentifier) -> None:
    """Adds a pi rotation around the X axis on the specified qubit.

    Args:
        q (QubitIdentifier): The target qubit.
    """
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(_qubit(q), "x")


def rx(q: QubitIdentifier, angle: float) -> None:
    """Adds a rotation around the X axis by `angle` on the specified qubit.
    Args:
        q (QubitIdentifier): The target qubit.
        angle (float): Angle in radians.
    """
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(_qubit(q), "rx", angle)


def cnot(q_ctrl: QubitIdentifier, q_target: QubitIdentifier) -> None:
    """Adds a CNOT gate to the program on the specified qubits.

    Args:
        q_ctrl (QubitIdentifier): The control qubit.
        q_target (QubitIdentifier): The target qubit.
    """
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate([_qubit(q_ctrl), _qubit(q_target)], "cnot")
