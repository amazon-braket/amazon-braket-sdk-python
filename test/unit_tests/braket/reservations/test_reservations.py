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

import os
from unittest.mock import MagicMock, patch

import pytest

from braket.aws import AwsDevice, AwsSession
from braket.reservations.reservations import DirectReservation


@pytest.fixture
def aws_device():
    mock_device = MagicMock(spec=AwsDevice)
    mock_device._arn = "device_arn_example"
    return mock_device


def test_direct_reservation_with_device_object(aws_device):
    reservation = DirectReservation(aws_device, "reservation_arn_example")
    assert reservation.device_arn == "device_arn_example"
    assert reservation.reservation_arn == "reservation_arn_example"


def test_direct_reservation_with_string():
    reservation = DirectReservation("my:string:arn", "reservation_arn_example")
    assert reservation.device_arn == "my:string:arn"
    assert reservation.reservation_arn == "reservation_arn_example"


def test_direct_reservation_with_invalid_type():
    """Test initialization with an invalid type should raise ValueError."""
    with pytest.raises(ValueError):
        DirectReservation(123, "reservation_arn_example")


def test_context_management(aws_device):
    """Test the context manager functionality."""
    with DirectReservation(aws_device, "reservation_arn_example"):
        assert os.getenv("AMZN_BRAKET_DEVICE_ARN_TEMP") == "device_arn_example"
        assert os.getenv("AMZN_BRAKET_RESERVATION_ARN_TEMP") == "reservation_arn_example"
    assert os.getenv("AMZN_BRAKET_DEVICE_ARN_TEMP") is None
    assert os.getenv("AMZN_BRAKET_RESERVATION_ARN_TEMP") is None


def test_start_reservation_already_active(aws_device):
    """Test starting an already active context raises RuntimeError."""
    reservation = DirectReservation(aws_device, "reservation_arn_example")
    reservation.start()
    with pytest.raises(RuntimeError):
        reservation.start()
    reservation.stop()


def test_stop_reservation_not_active(aws_device):
    """Test stopping a non-active context raises RuntimeError."""
    reservation = DirectReservation(aws_device, "reservation_arn_example")
    with pytest.raises(RuntimeError):
        reservation.stop()


def test_start_without_device_arn():
    with pytest.raises(ValueError, match="Device ARN must be a device or string."):
        DirectReservation(None, "reservation_arn_example")


def test_multiple_start_stop_cycles(aws_device):
    reservation = DirectReservation(aws_device, "reservation_arn_example")
    reservation.start()
    reservation.stop()
    reservation.start()
    reservation.stop()
    assert os.getenv("AMZN_BRAKET_DEVICE_ARN_TEMP") is None
    assert os.getenv("AMZN_BRAKET_RESERVATION_ARN_TEMP") is None


def test_create_quantum_task_with_correct_device_and_reservation():
    device_arn = "foo:bar:device_arn"
    reservation_arn = "my:reservation_arn:example"
    kwargs = {
        "backendArn": "arn:aws:us-west-2:abc:xyz:abc",
        "cwLogGroupArn": "arn:aws:us-west-2:abc:xyz:abc",
        "destinationUrl": "http://s3-us-west-2.amazonaws.com/task-output-bar-1/output.json",
        "program": {"ir": '{"instructions":[]}', "qubitCount": 4},
        "shots": 1,
        "deviceArn": device_arn,
    }
    "example_quantum_task_arn"

    with patch("boto3.client"):
        mock_client = MagicMock()
        aws_session = AwsSession(braket_client=mock_client)

        with DirectReservation(device_arn, reservation_arn):
            aws_session.create_quantum_task(**kwargs)

            kwargs["reservation_arn"] = reservation_arn
            mock_client.create_quantum_task.assert_called_once_with(**kwargs)
