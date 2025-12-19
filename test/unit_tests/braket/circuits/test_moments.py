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

from collections import OrderedDict

import numpy as np
import pytest

from braket.circuits import Gate, Instruction, Moments, MomentsKey, QubitSet
from braket.circuits.compiler_directives import Barrier
from braket.circuits.noises import Kraus


def cnot(q1, q2):
    return Instruction(Gate.CNot(), [q1, q2])


def h(q):
    return Instruction(Gate.H(), q)


@pytest.fixture
def moments():
    return Moments([h(0), h(0)])


def test_add():
    moments = Moments()
    moments.add([h(0)])
    moments.add([h(0)])

    expected = OrderedDict()
    expected[MomentsKey(0, QubitSet(0), "gate", 0)] = h(0)
    expected[MomentsKey(1, QubitSet(0), "gate", 0)] = h(0)
    assert OrderedDict(moments) == expected


def test_add_single_insturction():
    moments = Moments()
    moments.add(h(0))

    expected = OrderedDict()
    expected[MomentsKey(0, QubitSet(0), "gate", 0)] = h(0)
    assert OrderedDict(moments) == expected


def test_default_constructor():
    moments = Moments()
    assert OrderedDict(moments) == OrderedDict()
    assert moments.depth == 0
    assert moments.qubits == QubitSet()


def test_constructor_with_instructions():
    moments = Moments([h(0), h(1)])
    expected = Moments()
    expected.add([h(0)])
    expected.add([h(1)])
    assert moments == expected


def test_depth():
    moments = Moments([h(0), h(1)])
    assert moments.depth == 1

    moments.add([cnot(0, 2), h(3)])
    assert moments.depth == 2


def test_depth_setter(moments):
    with pytest.raises(AttributeError):
        moments.depth = 5


def test_overlaping_qubits():
    moments = Moments([h(0), h(0)])
    assert moments.depth == 2

    moments.add([cnot(0, 3), h(1)])
    assert moments.depth == 3

    moments.add([cnot(2, 4)])
    assert moments.depth == 3


def test_qubits():
    moments = Moments([h(0), h(10), h(5)])
    expected = QubitSet([0, 10, 5])
    assert moments.qubits == expected
    assert moments.qubit_count == len(expected)


def test_qubits_setter(moments):
    with pytest.raises(AttributeError):
        moments.qubits = QubitSet(1)


def test_qubit_count_setter(moments):
    with pytest.raises(AttributeError):
        moments.qubit_count = 1


def test_time_slices():
    moments = Moments([h(0), h(1), cnot(0, 1)])
    expected = {0: [h(0), h(1)], 1: [cnot(0, 1)]}
    assert moments.time_slices() == expected


def test_keys():
    moments = Moments([h(0), h(0), h(1)])
    expected = [
        MomentsKey(0, QubitSet(0), "gate", 0),
        MomentsKey(1, QubitSet(0), "gate", 0),
        MomentsKey(0, QubitSet(1), "gate", 0),
    ]
    assert list(moments.keys()) == expected


def test_items():
    moments = Moments([h(0), h(0), h(1)])
    expected = [
        (MomentsKey(0, QubitSet(0), "gate", 0), h(0)),
        (MomentsKey(1, QubitSet(0), "gate", 0), h(0)),
        (MomentsKey(0, QubitSet(1), "gate", 0), h(1)),
    ]
    assert list(moments.items()) == expected


def test_values():
    moments = Moments([h(0), h(0), h(1)])
    expected = [h(0), h(0), h(1)]
    assert list(moments.values()) == expected


def test_get():
    moments = Moments([h(0)])
    unknown_key = MomentsKey(100, QubitSet(100), "gate", 0)
    assert moments.get(MomentsKey(0, QubitSet(0), "gate", 0)) == h(0)
    assert moments.get(unknown_key) is None
    assert moments.get(unknown_key, h(0)) == h(0)


def test_getitem():
    moments = Moments([h(0)])
    assert moments[MomentsKey(0, QubitSet(0), "gate", 0)] == h(0)


def test_iter(moments):
    assert list(moments) == list(moments.keys())


def test_len():
    moments = Moments([h(0), h(0)])
    assert len(moments) == 2


def test_contains():
    moments = Moments([h(0), h(0)])
    assert MomentsKey(0, QubitSet(0), "gate", 0) in moments
    assert MomentsKey(0, QubitSet(100), "gate", 0) not in moments


def test_equals():
    moments_1 = Moments([h(0)])
    moments_2 = Moments([h(0)])
    other_moments = Moments([h(1)])
    non_moments = "non moments"

    assert moments_1 == moments_2
    assert moments_1 is not moments_2
    assert moments_1 != other_moments
    assert moments_1 != non_moments


def test_repr(moments):
    assert repr(moments) == repr(OrderedDict(moments))


def test_str(moments):
    assert str(moments) == str(OrderedDict(moments))


def test_barrier_with_qubits():
    """Test barrier with specific qubits."""
    moments = Moments([h(0), h(1)])
    moments.add(Instruction(Barrier([0]), [0]))
    assert moments.depth == 2


def test_barrier_without_qubits():
    """Test barrier without qubits (global)."""
    moments = Moments([h(0), h(1)])
    moments.add(Instruction(Barrier([]), []))
    assert moments.depth == 2


def test_multi_qubit_noise_blocks_subsequent_gates():
    """Test that multi-qubit noise channels block subsequent gates on affected qubits.

    Regression test for GitHub issue #1091: gates should not visually commute
    through multi-qubit Kraus operators in circuit visualization.
    """
    moments = Moments()
    # Add X gate on qubit 0
    moments.add(Instruction(Gate.X(), 0))
    # Add 2-qubit Kraus channel on qubits [1, 0]
    cx_matrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
    moments.add(Instruction(Kraus([cx_matrix]), [1, 0]))
    # Add H gate on qubit 1 - should be AFTER the Kraus, not at same time
    moments.add(Instruction(Gate.H(), 1))

    # Get the times for each instruction
    times = {instr.operator.name: key.time for key, instr in moments.items()}

    # H should be at time 1, after Kraus at time 0
    assert times["X"] == 0
    assert times["Kraus"] == 0
    assert times["H"] == 1, "H gate should be placed after multi-qubit Kraus channel"


def test_single_qubit_noise_does_not_block_other_qubits():
    """Test that single-qubit noise channels don't block gates on other qubits."""
    moments = Moments()
    # Add X gate on qubit 0
    moments.add(Instruction(Gate.X(), 0))
    # Add single-qubit Kraus on qubit 0 only
    moments.add(Instruction(Kraus([np.eye(2)]), [0]))
    # Add H gate on qubit 1 - should be at time 0 (independent of qubit 0)
    moments.add(Instruction(Gate.H(), 1))

    times = {}
    for key, instr in moments.items():
        times[f"{instr.operator.name}_{key.qubits}"] = key.time

    # H on qubit 1 should be at time 0 (not blocked by Kraus on qubit 0)
    assert times[f"H_{QubitSet(1)}"] == 0
