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

import re

import pytest
from botocore.exceptions import ClientError

from braket.aws.aws_device import AwsDevice
from braket.circuits.circuit import Circuit
from braket.devices import LocalSimulator

DEVICE = LocalSimulator()
SHOTS = 8000

IONQ_ARN = "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1"
SIMULATOR_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
IQM_ARN = "arn:aws:braket:eu-north-1::device/qpu/iqm/Garnet"


@pytest.mark.parametrize("arn", [(IONQ_ARN), (SIMULATOR_ARN)])
def test_unsupported_devices(arn):
    device = AwsDevice(arn)
    if device.status != "ONLINE":
        pytest.skip("Device not online")

    circ = Circuit().h(0).cnot(0, 1).h(2).measure([0, 1])
    error_string = re.escape(
        "An error occurred (ValidationException) when calling the "
        "CreateQuantumTask operation: Device requires all qubits in the program to be measured. "
        "This may be caused by declaring non-contiguous qubits or measuring partial qubits"
    )
    with pytest.raises(ClientError, match=error_string):
        device.run(circ, shots=1000)


@pytest.mark.parametrize("sim", [("braket_sv"), ("braket_dm")])
def test_measure_on_local_sim(sim):
    circ = Circuit().h(0).cnot(0, 1).h(2).measure([0, 1])
    device = LocalSimulator(sim)
    result = device.run(circ, SHOTS).result()
    assert len(result.measurements[0]) == 2
    assert result.measured_qubits == [0, 1]


@pytest.mark.parametrize("arn", [IQM_ARN])
def test_measure_on_supported_devices(arn):
    device = AwsDevice(arn)
    if not device.is_available:
        pytest.skip("Device offline")
    circ = Circuit().h(0).cnot(0, 1).measure([0])
    result = device.run(circ, SHOTS).result()
    assert len(result.measurements[0]) == 1
    assert result.measured_qubits == [0]


@pytest.mark.parametrize(
    "circuit, expected_measured_qubits",
    [
        (Circuit().h(0).cnot(0, 1).cnot(1, 2).cnot(2, 3).measure([0, 1, 3]), [0, 1, 3]),
        (Circuit().h(0).measure(0), [0]),
    ],
)
def test_measure_targets(circuit, expected_measured_qubits):
    result = DEVICE.run(circuit, SHOTS).result()
    assert result.measured_qubits == expected_measured_qubits
    assert len(result.measurements[0]) == len(expected_measured_qubits)


def test_measure_with_noise():
    device = LocalSimulator("braket_dm")
    circuit = Circuit().x(0).x(1).bit_flip(0, probability=0.1).measure(0)
    result = device.run(circuit, SHOTS).result()
    assert result.measured_qubits == [0]
    assert len(result.measurements[0]) == 1
