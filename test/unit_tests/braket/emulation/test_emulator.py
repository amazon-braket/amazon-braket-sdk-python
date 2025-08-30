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

import re
from unittest.mock import Mock

import pytest

from braket.circuits import Circuit, Gate, Observable
from braket.circuits.noise_model import GateCriteria, NoiseModel, ObservableCriteria
from braket.circuits.noises import BitFlip
from braket.default_simulator import DensityMatrixSimulator, StateVectorSimulator
from braket.devices import local_simulator
from braket.emulation import Emulator
from braket.emulation.passes.circuit_passes import GateValidator, QubitCountValidator
from braket.devices.local_simulator import LocalSimulator


@pytest.fixture
def setup_local_simulator_devices():
    mock_circuit_entry = Mock()
    mock_circuit_dm_entry = Mock()
    mock_circuit_entry.load.return_value = StateVectorSimulator
    mock_circuit_dm_entry.load.return_value = DensityMatrixSimulator
    _simulator_devices = {"default": mock_circuit_entry, "braket_dm": mock_circuit_dm_entry}
    local_simulator._simulator_devices.update(_simulator_devices)


@pytest.fixture
def local_dm_simulator(setup_local_simulator_devices):
    return LocalSimulator("braket_dm", noise_model=NoiseModel())


@pytest.fixture
def empty_emulator(local_dm_simulator):
    return Emulator(local_dm_simulator)


@pytest.fixture
def noiseless_emulator(local_dm_simulator):
    qubit_count_validator = QubitCountValidator(4)
    return Emulator(local_dm_simulator, passes=[qubit_count_validator])


@pytest.fixture
def noisy_emulator(setup_local_simulator_devices):
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.1), GateCriteria(Gate.H))
    local_backend = LocalSimulator("braket_dm", noise_model=noise_model)
    qubit_count_validator = QubitCountValidator(4)
    return Emulator(local_backend, noise_model=noise_model, passes=[qubit_count_validator])


def test_empty_emulator_validation(empty_emulator):
    emulator = empty_emulator
    circuit = Circuit().h(0).cnot(0, 1)
    emulator.validate(circuit)


def test_noiseless_emulator(noiseless_emulator):
    """
    Should not error out when passed a valid circuit.
    """
    circuit = Circuit().cnot(0, 1)
    circuit = noiseless_emulator.transform(circuit)
    assert circuit == circuit


def test_basic_invalidate(noiseless_emulator):
    """
    Emulator should raise an error thrown by the QubitCountValidator.
    """
    circuit = Circuit().x(range(6))
    match_string = re.escape(
        f"Circuit must use at most 4 qubits, but uses {circuit.qubit_count} qubits."
    )
    with pytest.raises(Exception, match=match_string):
        noiseless_emulator.validate(circuit)


def test_apply_noise_model(noisy_emulator):
    circuit = Circuit().h(0)
    circuit = noisy_emulator.transform(circuit)

    noisy_circuit = Circuit().h(0).apply_gate_noise(BitFlip(0.1), Gate.H).measure(target_qubits=[0])
    assert circuit == noisy_circuit

    circuit = Circuit().h(0).measure(target_qubits=[0])
    circuit = noisy_emulator.transform(circuit, apply_noise_model=False)

    target_circ = Circuit().h(0).measure(target_qubits=[0])
    assert circuit == target_circ


def test_remove_verbatim_box(noiseless_emulator):
    circuit = Circuit().h(0)
    circuit = Circuit().add_verbatim_box(circuit).probability()
    circuit = noiseless_emulator._remove_verbatim_box(circuit)

    target_circuit = Circuit().h(0).probability()

    assert circuit == target_circuit


def test_noisy_run(noisy_emulator):
    circuit = Circuit().h(0)
    open_qasm_source = """OPENQASM 3.0;
bit[1] b;
qubit[1] q;
h q[0];
#pragma braket noise bit_flip(0.1) q[0]
b[0] = measure q[0];""".strip()

    result = noisy_emulator.run(circuit, shots=1).result()
    emulation_source = result.additional_metadata.action.source.strip()
    assert emulation_source == open_qasm_source
