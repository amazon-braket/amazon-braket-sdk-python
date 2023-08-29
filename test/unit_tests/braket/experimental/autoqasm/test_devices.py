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

from unittest.mock import Mock, patch

import pytest

import braket.experimental.autoqasm as aq
from braket.aws import AwsDevice
from braket.device_schema.simulators import GateModelSimulatorDeviceCapabilities
from braket.devices import Devices
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.instructions import h

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
        "braket.ir.jaqcd.program": {
            "actionType": "braket.ir.jaqcd.program",
            "version": ["1"],
            "supportedOperations": ["H"],
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
    _aws_device.properties.paradigm.qubitCount = 34
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

        program = my_program()
        assert program.to_ir()


def test_insufficient_qubits(aws_device: Mock) -> None:
    @aq.main(device=aws_device, num_qubits=35)
    def my_program():
        pass

    with pytest.raises(errors.InsufficientQubitCountError):
        my_program()
