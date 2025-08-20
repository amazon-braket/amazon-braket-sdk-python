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
def local_dm_simulator():
    return LocalSimulator("braket_dm", noise_model=NoiseModel())


@pytest.fixture
def basic_emulator(local_dm_simulator):
    qubit_count_validator = QubitCountValidator(4)
    return Emulator(local_dm_simulator, passes=[qubit_count_validator])


@pytest.fixture
def empty_emulator(local_dm_simulator):
    return Emulator(local_dm_simulator)


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
        f"Circuit must use at most 4 qubits, but uses {circuit.qubit_count} qubits."
    )
    with pytest.raises(Exception, match=match_string):
        basic_emulator.validate(circuit)


def test_apply_noise_model():
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.1), GateCriteria(Gate.H))
    local_backend = LocalSimulator("braket_dm", noise_model=noise_model)
    emulator = Emulator(local_backend, noise_model=noise_model)

    circuit = Circuit().h(0)
    circuit = emulator.transform(circuit)

    noisy_circuit = Circuit().h(0).apply_gate_noise(BitFlip(0.1), Gate.H).measure(target_qubits=[0])
    assert circuit == noisy_circuit

    circuit = Circuit().h(0).measure(target_qubits=[0])
    circuit = emulator.transform(circuit, apply_noise_model=False)

    target_circ = Circuit().h(0).measure(target_qubits=[0])
    assert circuit == target_circ


def test_remove_verbatim_box(basic_emulator):
    circuit = Circuit().h(0)
    circuit = Circuit().add_verbatim_box(circuit).probability()
    circuit = basic_emulator._remove_verbatim_box(circuit)

    target_circuit = Circuit().h(0).probability()

    assert circuit == target_circuit


def test_noisy_run():
    noise_model = NoiseModel()
    noise_model.add_noise(BitFlip(0.1), GateCriteria(Gate.H))

    qubit_count_validator = QubitCountValidator(4)
    gate_validator = GateValidator(supported_gates=["H"])
    local_backend = LocalSimulator("braket_dm", noise_model=noise_model)
    emulator = Emulator(
        backend=local_backend,
        passes=[qubit_count_validator, gate_validator],
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
