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

import numpy as np
import pytest

from braket.circuits import Circuit
from braket.emulation.passes.circuit_passes import QubitCountValidator


@pytest.mark.parametrize(
    "qubit_count,circuit",
    [
        (1, Circuit()),
        (10, Circuit().add_verbatim_box(Circuit())),
        (1, Circuit().z(0)),
        (1, Circuit().z(3).x(3)),
        (2, Circuit().cnot(0, 1).swap(1, 0)),
        (2, Circuit().z(0).add_verbatim_box(Circuit().cnot(0, 4)).yy(0, 4, np.pi / 4)),
        (50, Circuit().i(range(50)).measure(range(50))),
    ],
)
def test_valid_circuits(qubit_count, circuit):
    """
    QubitCountValidator should not raise any errors when validating these circuits.
    """
    QubitCountValidator(qubit_count=qubit_count).__call__(circuit)


@pytest.mark.parametrize("qubit_count", [0, -1])
def test_invalid_instantiation(qubit_count):
    with pytest.raises(ValueError):
        QubitCountValidator(qubit_count)


@pytest.mark.parametrize(
    "qubit_count,circuit",
    [
        (1, Circuit().cnot(0, 1)),
        (2, Circuit().cnot(0, 1).x(2)),
        (50, Circuit().i(range(50)).measure(range(50)).measure(50)),
    ],
)
def test_invalid_circuits(qubit_count, circuit):
    with pytest.raises(
        ValueError,
        match=f"Circuit must use at most {qubit_count} qubits, \
but uses {circuit.qubit_count} qubits.",
    ):
        QubitCountValidator(qubit_count).validate(circuit)
