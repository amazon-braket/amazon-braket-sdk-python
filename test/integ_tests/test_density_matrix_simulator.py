import math

import numpy as np
import pytest
from gate_model_device_testing_utils import get_tol

from braket.aws import AwsDevice
from braket.circuits import Circuit, Gate, Instruction, Noise, Observable

SHOTS = 1000
DM1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/dm1"
SIMULATOR_ARNS = [DM1_ARN]


@pytest.mark.parametrize("simulator_arn", SIMULATOR_ARNS)
@pytest.mark.parametrize("num_layers", [50, 100, 500, 1000])
def test_many_layers(simulator_arn, num_layers, aws_session, s3_destination_folder):
    num_qubits = 10
    circuit = _many_layers(num_qubits, num_layers)
    device = AwsDevice(simulator_arn, aws_session)

    tol = get_tol(SHOTS)
    result = device.run(circuit, shots=SHOTS, s3_destination_folder=s3_destination_folder).result()
    probabilities = result.measurement_probabilities
    probability_sum = 0
    for bitstring in probabilities:
        assert probabilities[bitstring] >= 0
        probability_sum += probabilities[bitstring]
    assert math.isclose(probability_sum, 1, rel_tol=tol["rtol"], abs_tol=tol["atol"])
    assert len(result.measurements) == SHOTS


@pytest.mark.parametrize("simulator_arn", SIMULATOR_ARNS)
def test_mixed_states(simulator_arn, aws_session, s3_destination_folder):
    num_qubits = 10
    circuit = _mixed_states(num_qubits)
    device = AwsDevice(simulator_arn, aws_session)

    tol = get_tol(SHOTS)
    result = device.run(circuit, shots=SHOTS, s3_destination_folder=s3_destination_folder).result()
    probabilities = result.measurement_probabilities
    probability_sum = 0
    for bitstring in probabilities:
        assert probabilities[bitstring] >= 0
        probability_sum += probabilities[bitstring]
    assert math.isclose(probability_sum, 1, rel_tol=tol["rtol"], abs_tol=tol["atol"])
    assert len(result.measurements) == SHOTS


def _many_layers(n_qubits: int, n_layers: int) -> Circuit:
    """
    Function to return circuit with many layers.

    :param int n_qubits: number of qubits
    :param int n_layers: number of layers
    :return: Constructed easy circuit
    :rtype: Circuit
    """
    qubits = range(n_qubits)
    circuit = Circuit()  # instantiate circuit object
    for q in range(n_qubits):
        circuit.h(q)
    for layer in range(n_layers):
        if (layer + 1) % 100 != 0:
            for qubit in range(len(qubits)):
                angle = np.random.uniform(0, 2 * math.pi)
                gate = np.random.choice(
                    [Gate.Rx(angle), Gate.Ry(angle), Gate.Rz(angle), Gate.H()], 1, replace=True
                )[0]
                circuit.add_instruction(Instruction(gate, qubit))
        else:
            for q in range(0, n_qubits, 2):
                circuit.cnot(q, q + 1)
            for q in range(1, n_qubits - 1, 2):
                circuit.cnot(q, q + 1)
    return circuit


def _mixed_states(n_qubits: int) -> Circuit:
    noise = Noise.PhaseFlip(probability=0.2)
    circ = Circuit()
    for qubit in range(0, n_qubits - 2, 3):
        circ.x(qubit).y(qubit + 1).cnot(qubit, qubit + 2).x(qubit + 1).z(qubit + 2)
        circ.apply_gate_noise(noise, target_qubits=[qubit, qubit + 2])

    # attach the result types
    circ.probability()
    circ.expectation(observable=Observable.Z(), target=0)

    return circ
