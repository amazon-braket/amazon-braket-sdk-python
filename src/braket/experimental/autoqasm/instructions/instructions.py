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


"""Instructions that apply to qubits, including quantum gates, reset and measure.

Example of using a `h` gate and a `cnot` gate to create a Bell circuit:

.. code-block:: python

    @aq.function
    def bell():
        h(0)
        cnot(0, 1)
        measure([0, 1])
"""


from braket.experimental.autoqasm import program

from .qubits import QubitIdentifierType, _qubit


def reset(q: QubitIdentifierType) -> None:
    """Adds a reset instruction on a specified qubit.

    Args:
        q (QubitIdentifierType): The target qubit.
    """
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.gate(_qubit(q), "reset")
