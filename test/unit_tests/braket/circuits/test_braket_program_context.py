# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import pytest

from braket.circuits import Circuit, compiler_directives
from braket.circuits.braket_program_context import BraketProgramContext
from braket.circuits.qubit_set import QubitSet


@pytest.mark.parametrize(
    "target, expected_instruction_count",
    [
        ([0, 1], 3),
        ([], 3),
        (None, 3),
    ],
)
def test_add_barrier(target, expected_instruction_count):
    """Test BraketProgramContext.add_barrier with various target inputs."""
    circ = Circuit().h(0).h(1)
    context = BraketProgramContext(circ)
    context.add_barrier(target)

    assert len(circ.instructions) == expected_instruction_count

    if expected_instruction_count == 3:
        barrier_instr = circ.instructions[2]
        assert isinstance(barrier_instr.operator, compiler_directives.Barrier)
        if target is None or target == []:
            assert barrier_instr.target == QubitSet()
        else:
            assert barrier_instr.target == QubitSet(target)
