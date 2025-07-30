import re
from unittest.mock import Mock

import numpy as np
import pytest

from braket.circuits import Circuit, Gate
from braket.circuits.noise_model import GateCriteria, NoiseModel
from braket.circuits.noises import BitFlip
from braket.default_simulator import DensityMatrixSimulator, StateVectorSimulator
from braket.devices import local_simulator
from braket.emulation import Emulator
from braket.passes import BasePass, ProgramType
from braket.passes.circuit_passes import GateValidator, QubitCountValidator


class AlwaysFailPass(BasePass[ProgramType]):
    def run(self, program: ProgramType):
        raise ValueError("This pass always raises an error.")


@pytest.fixture
def setup_local_simulator_devices():
    mock_circuit_entry = Mock()
    mock_circuit_dm_entry = Mock()
    mock_circuit_entry.load.return_value = StateVectorSimulator
    mock_circuit_dm_entry.load.return_value = DensityMatrixSimulator
    _simulator_devices = {"default": mock_circuit_entry, "braket_dm": mock_circuit_dm_entry}
    local_simulator._simulator_devices.update(_simulator_devices)


@pytest.fixture
def empty_emulator(setup_local_simulator_devices):
    return Emulator()


@pytest.fixture
def basic_emulator(empty_emulator):
    qubit_count_validator = QubitCountValidator(4)
    return empty_emulator.add_pass(emulator_pass=[qubit_count_validator])


def test_empty_emulator_validation(empty_emulator):
    emulator = empty_emulator
    circuit = Circuit().h(0).cnot(0, 1)
    emulator.validate(circuit)


def test_basic_emulator(basic_emulator):
    """
    Should not error out when passed a valid circuit.
    """
    circuit = Circuit().cnot(0, 1)
    circuit = basic_emulator.transform(circuit)
    assert circuit == circuit


def test_basic_invalidate(basic_emulator):
    """
    Emulator should raise an error thrown by the QubitCountValidator.
    """
    circuit = Circuit().x(range(6))
    match_string = re.escape(
        f"Circuit must use at most 4 qubits, \
but uses {circuit.qubit_count} qubits. (DeviceEmulator)"
    )
    with pytest.raises(Exception, match=match_string):
        basic_emulator.transform(circuit)


def test_add_pass_single(empty_emulator):
    emulator = empty_emulator
    qubit_count_validator = QubitCountValidator(4)
    emulator.add_pass(qubit_count_validator)

    assert emulator._emulator_passes == [qubit_count_validator]


def test_bad_add_pass(empty_emulator):
    emulator = empty_emulator
    with pytest.raises(TypeError):
        emulator.add_pass(None)


def test_add_pass_multiple(setup_local_simulator_devices):
    native_gate_validator = GateValidator(native_gates=["CZ", "PRx"])
    emulator = Emulator(emulator_passes=[native_gate_validator])
    qubit_count_validator = QubitCountValidator(4)
    gate_validator = GateValidator(supported_gates=["H", "CNot"])

    emulator.add_pass([qubit_count_validator, gate_validator])
    assert emulator._emulator_passes == [
        native_gate_validator,
        qubit_count_validator,
        gate_validator,
    ]


def test_use_correct_backend_if_noise_model(setup_local_simulator_devices):
    noise_model = NoiseModel()
    emulator = Emulator(noise_model=noise_model)
    assert emulator._backend.name == "DensityMatrixSimulator"


def test_update_noise_model(empty_emulator):
    emulator = empty_emulator
    assert emulator._backend.name == "StateVectorSimulator"
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.1), GateCriteria(Gate.H()))

    emulator.noise_model = noise_model
    assert emulator._backend.name == "DensityMatrixSimulator"
    assert emulator._backend._noise_model == noise_model
    assert emulator.noise_model == noise_model


def test_validation_only_pass(setup_local_simulator_devices):
    qubit_count_validator = QubitCountValidator(4)
    bad_pass = AlwaysFailPass()
    emulator = Emulator(emulator_passes=[bad_pass, qubit_count_validator])

    circuit = Circuit().h(range(5))
    match_string = re.escape(
        f"Circuit must use at most 4 qubits, \
but uses {circuit.qubit_count} qubits. (DeviceEmulator)"
    )
    with pytest.raises(Exception, match=match_string):
        emulator.validate(circuit)


def test_apply_noise_model(setup_local_simulator_devices):
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.1), GateCriteria(Gate.H))
    emulator = Emulator(noise_model=noise_model)

    circuit = Circuit().h(0)
    circuit = emulator.transform(circuit)

    noisy_circuit = Circuit().h(0).apply_gate_noise(BitFlip(0.1), Gate.H).measure(target_qubits=[0])
    assert circuit == noisy_circuit

    circuit = Circuit().h(0).measure(target_qubits=[0])
    circuit = emulator.transform(circuit, apply_noise_model=False)

    target_circ = Circuit().h(0).measure(target_qubits=[0])
    assert circuit == target_circ


def test_remove_verbatim_box(setup_local_simulator_devices):
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.1), GateCriteria(Gate.H))
    emulator = Emulator(noise_model=noise_model)

    circuit = Circuit().h(0)
    circuit = Circuit().add_verbatim_box(circuit).probability()
    circuit = emulator._remove_verbatim_box(circuit)

    target_circuit = Circuit().h(0).probability()

    assert circuit == target_circuit


def test_noisy_run(setup_local_simulator_devices):
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.1), GateCriteria(Gate.H))

    qubit_count_validator = QubitCountValidator(4)
    gate_validator = GateValidator(supported_gates=["H"])
    emulator = Emulator(
        backend="braket_dm",
        emulator_passes=[qubit_count_validator, gate_validator],
        noise_model=noise_model,
    )

    circuit = Circuit().h(0)
    open_qasm_source = """OPENQASM 3.0;
bit[1] b;
qubit[1] q;
h q[0];
#pragma braket noise bit_flip(0.1) q[0]
b[0] = measure q[0];""".strip()

    result = emulator.run(circuit, shots=1).result()
    emulation_source = result.additional_metadata.action.source.strip()
    assert emulation_source == open_qasm_source
