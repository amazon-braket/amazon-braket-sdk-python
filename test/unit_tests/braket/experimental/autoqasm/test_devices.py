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

"""AutoQASM tests exercising device-specific targeting functionality.
"""

import json
from unittest.mock import Mock, patch

import pytest

import braket.experimental.autoqasm as aq
from braket.aws import AwsDevice
from braket.device_schema import DeviceActionType
from braket.device_schema.simulators import GateModelSimulatorDeviceCapabilities
from braket.devices import Devices
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.instructions import cnot, cphaseshift00, h, rx, x
from braket.parametric import FreeParameter

RIGETTI_REGION = "us-west-1"

MOCK_DEFAULT_S3_DESTINATION_FOLDER = (
    "amazon-braket-us-test-1-00000000",
    "tasks",
)

MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES_JSON = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.simulators.gate_model_simulator_device_capabilities",
        "version": "1",
    },
    "service": {
        "executionWindows": [
            {
                "executionDay": "Everyday",
                "windowStartHour": "11:00",
                "windowEndHour": "12:00",
            }
        ],
        "shotsRange": [1, 10],
    },
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "version": ["1"],
            "supportedOperations": ["h"],
        }
    },
    "paradigm": {"qubitCount": 30},
    "deviceParameters": {},
}

MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES = GateModelSimulatorDeviceCapabilities.parse_obj(
    MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES_JSON
)

MOCK_GATE_MODEL_SIMULATOR = {
    "deviceName": "SV1",
    "deviceType": "SIMULATOR",
    "providerName": "provider1",
    "deviceStatus": "ONLINE",
    "deviceCapabilities": MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES.json(),
}


@pytest.fixture
def aws_session():
    _boto_session = Mock()
    _boto_session.region_name = RIGETTI_REGION
    _boto_session.profile_name = "test-profile"

    creds = Mock()
    creds.method = "other"
    _boto_session.get_credentials.return_value = creds

    _aws_session = Mock()
    _aws_session.boto_session = _boto_session
    _aws_session._default_bucket = MOCK_DEFAULT_S3_DESTINATION_FOLDER[0]
    _aws_session.default_bucket.return_value = _aws_session._default_bucket
    _aws_session._custom_default_bucket = False
    _aws_session.account_id = "00000000"
    _aws_session.region = RIGETTI_REGION
    _aws_session.get_device.return_value = MOCK_GATE_MODEL_SIMULATOR

    return _aws_session


@pytest.fixture
def aws_device():
    _aws_device = Mock()
    _aws_device.name = "Mock SV1 Device"
    _aws_device.properties.paradigm.qubitCount = 30
    _aws_device_action = Mock()
    _aws_device_action.supportedOperations = []
    _aws_device_action.supportedPragmas = []
    _aws_device.properties.action = {DeviceActionType.OPENQASM: _aws_device_action}
    return _aws_device


@patch("braket.aws.aws_device.AwsSession.copy_session")
@patch("braket.aws.aws_device.AwsSession")
@patch("braket.aws.aws_device.AwsDevice")
def test_device_parameter(
    aws_session_init: Mock,
    aws_device_init: Mock,
    mock_copy_session: Mock,
    aws_session: Mock,
    aws_device: Mock,
) -> None:
    aws_session_init.return_value = aws_session
    aws_device_init.return_value = aws_device
    mock_copy_session.return_value = aws_session

    devices = [None, Devices.Amazon.SV1, AwsDevice(Devices.Amazon.SV1)]

    for device in devices:

        @aq.main(device=device)
        def my_program():
            h(0)

        assert my_program.to_ir()


def test_insufficient_qubits(aws_device: Mock) -> None:
    aws_device.properties.paradigm.qubitCount = 9

    with pytest.raises(errors.InsufficientQubitCountError):

        @aq.main(device=aws_device, num_qubits=10)
        def my_program():
            pass


def test_unsupported_gate(aws_device: Mock) -> None:
    aws_device.properties.action[DeviceActionType.OPENQASM].supportedOperations = ["h"]

    with pytest.raises(errors.UnsupportedGate):

        @aq.main(device=aws_device)
        def my_program():
            cphaseshift00(0, 1, 0.123)


def test_unsupported_native_gate(aws_device: Mock) -> None:
    aws_device.properties.action[DeviceActionType.OPENQASM].supportedOperations = ["h, x"]
    aws_device.properties.action[DeviceActionType.OPENQASM].supportedPragmas = ["verbatim"]
    aws_device.properties.paradigm.nativeGateSet = ["x"]

    with pytest.raises(errors.UnsupportedNativeGate):

        @aq.main(device=aws_device)
        def my_program():
            with aq.verbatim():
                x("$0")
                h("$0")


def test_supported_native_gate_inside_gate_definition(aws_device: Mock) -> None:
    aws_device.properties.action[DeviceActionType.OPENQASM].supportedOperations = ["h, x"]
    aws_device.properties.action[DeviceActionType.OPENQASM].supportedPragmas = ["verbatim"]
    aws_device.properties.paradigm.nativeGateSet = ["x"]

    @aq.gate
    def my_gate(q: aq.Qubit):
        x(q)

    @aq.main(device=aws_device)
    def my_program():
        with aq.verbatim():
            x("$0")
            my_gate("$0")

    assert my_program.to_ir()


def test_unsupported_native_gate_inside_gate_definition(aws_device: Mock) -> None:
    aws_device.properties.action[DeviceActionType.OPENQASM].supportedOperations = ["h, x"]
    aws_device.properties.action[DeviceActionType.OPENQASM].supportedPragmas = ["verbatim"]
    aws_device.properties.paradigm.nativeGateSet = ["x"]

    @aq.gate
    def my_gate(q: aq.Qubit):
        h(q)

    with pytest.raises(errors.UnsupportedNativeGate):

        @aq.main(device=aws_device)
        def my_program():
            with aq.verbatim():
                my_gate("$0")


def test_unsupported_verbatim_block(aws_device: Mock) -> None:
    aws_device.properties.action[DeviceActionType.OPENQASM].supportedPragmas = []

    with pytest.raises(errors.VerbatimBlockNotAllowed):

        @aq.main(device=aws_device)
        def my_program():
            with aq.verbatim():
                h("$0")


def test_validate_connectivity(aws_device: Mock) -> None:
    aws_device.properties.action[DeviceActionType.OPENQASM].supportedOperations = ["rx, ry, rz"]
    aws_device.properties.action[DeviceActionType.OPENQASM].supportedPragmas = ["verbatim"]
    aws_device.properties.paradigm.nativeGateSet = ["H", "CNOT"]
    aws_device.properties.paradigm.connectivity.fullyConnected = False
    aws_device.properties.paradigm.connectivity.connectivityGraph = {"0": ["2"], "1": ["0"]}

    with pytest.raises(errors.InvalidTargetQubit):

        @aq.main(device=aws_device)
        def my_program_invalid():
            with aq.verbatim():
                h("$0")
                cnot("$0", "$1")

    @aq.main(device=aws_device)
    def my_program():
        with aq.verbatim():
            h("$0")
            cnot("$0", "$2")
            cnot("$1", "$0")

    assert my_program.to_ir()

    aws_device.properties.paradigm.connectivity.fullyConnected = True
    aws_device.properties.paradigm.connectivity.connectivityGraph = {}

    @aq.main(device=aws_device)
    def my_program():
        with aq.verbatim():
            h("$0")
            cnot("$0", "$7")
            cnot("$5", "$2")

    assert my_program.to_ir()


@pytest.mark.parametrize(
    "inputs,device_parameters",
    [
        (None, None),
        ({"angle": 0.123}, {"foo": "bar"}),
    ],
)
@patch("braket.aws.aws_device.AwsSession.copy_session")
@patch("braket.aws.aws_device.AwsSession")
def test_aws_device_run(
    aws_session_init: Mock,
    mock_copy_session: Mock,
    aws_session: Mock,
    inputs,
    device_parameters,
) -> None:
    """Tests AwsDevice.run with AutoQASM program."""
    aws_session_init.return_value = aws_session
    mock_copy_session.return_value = aws_session

    @aq.main
    def my_program():
        h(0)
        rx(0, FreeParameter("angle"))

    aws_device = AwsDevice(Devices.Amazon.SV1.value)
    _ = aws_device.run(my_program, shots=10, inputs=inputs, device_parameters=device_parameters)

    run_call_args = aws_session.create_quantum_task.mock_calls[0].kwargs
    run_call_args_action = json.loads(run_call_args["action"])

    expected_run_call_args = {
        "deviceArn": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        "outputS3Bucket": "amazon-braket-us-test-1-00000000",
        "outputS3KeyPrefix": "tasks",
        "shots": 10,
    }
    aws_session.create_quantum_task.assert_called_once()
    assert expected_run_call_args.items() <= run_call_args.items()
    assert run_call_args_action["source"] == my_program.to_ir()
    assert run_call_args_action["inputs"] == inputs
