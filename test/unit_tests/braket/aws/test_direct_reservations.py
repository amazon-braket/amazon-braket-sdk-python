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

from braket.aws import AwsDevice, AwsSession, DirectReservation
from braket.devices import LocalSimulator

RESERVATION_ARN = "arn:aws:braket:us-east-1:123456789:reservation/uuid"
DEVICE_ARN = "arn:aws:braket:us-east-1:123456789:device/qpu/ionq/Forte-1"
VALUE_ERROR_MESSAGE = "Device must be an AwsDevice or its ARN, or a local simulator device."
RUNTIME_ERROR_MESSAGE = "Another reservation is already active."


@pytest.fixture
def aws_device():
    mock_device = MagicMock(spec=AwsDevice)
    mock_device._arn = DEVICE_ARN
    type(mock_device).arn = property(lambda x: DEVICE_ARN)
    return mock_device


def test_direct_reservation_aws_device(aws_device):
    with DirectReservation(aws_device, RESERVATION_ARN) as reservation:
        assert reservation.device_arn == DEVICE_ARN
        assert reservation.reservation_arn == RESERVATION_ARN
        assert reservation._is_active


def test_direct_reservation_device_str(aws_device):
    with patch(
        "braket.aws.AwsDevice.__init__",
        side_effect=lambda self, *args, **kwargs: setattr(self, "_arn", DEVICE_ARN),
        autospec=True,
    ):
        with patch("braket.aws.AwsDevice", return_value=aws_device, autospec=True):
            with DirectReservation(DEVICE_ARN, RESERVATION_ARN) as reservation:
                assert reservation.device_arn == DEVICE_ARN
                assert reservation.reservation_arn == RESERVATION_ARN
                assert reservation._is_active


def test_direct_reservation_local_simulator():
    mock_device = MagicMock(spec=LocalSimulator)
    with pytest.warns(UserWarning):
        with DirectReservation(mock_device, RESERVATION_ARN) as reservation:
            assert os.environ["AMZN_BRAKET_RESERVATION_DEVICE_ARN"] == ""
            assert os.environ["AMZN_BRAKET_RESERVATION_TIME_WINDOW_ARN"] == RESERVATION_ARN
            assert reservation._is_active is True


@pytest.mark.parametrize("device", [123, False, [aws_device], {"a": 1}])
def test_direct_reservation_invalid_inputs(device):
    with pytest.raises(TypeError):
        DirectReservation(device, RESERVATION_ARN)


def test_direct_reservation_local_no_reservation():
    mock_device = MagicMock(spec=LocalSimulator)
    mock_device.create_quantum_task = MagicMock()
    kwargs = {
        "program": {"ir": '{"instructions":[]}', "qubitCount": 4},
        "shots": 1,
    }
    with DirectReservation(mock_device, None):
        mock_device.create_quantum_task(**kwargs)
        mock_device.create_quantum_task.assert_called_once_with(**kwargs)


def test_context_management(aws_device):
    with DirectReservation(aws_device, RESERVATION_ARN):
        assert os.getenv("AMZN_BRAKET_RESERVATION_DEVICE_ARN") == DEVICE_ARN
        assert os.getenv("AMZN_BRAKET_RESERVATION_TIME_WINDOW_ARN") == RESERVATION_ARN
    assert not os.getenv("AMZN_BRAKET_RESERVATION_DEVICE_ARN")
    assert not os.getenv("AMZN_BRAKET_RESERVATION_TIME_WINDOW_ARN")


def test_start_reservation_already_active(aws_device):
    reservation = DirectReservation(aws_device, RESERVATION_ARN)
    reservation.start()
    with pytest.raises(RuntimeError, match=RUNTIME_ERROR_MESSAGE):
        reservation.start()
    reservation.stop()


def test_stop_reservation_not_active(aws_device):
    reservation = DirectReservation(aws_device, RESERVATION_ARN)
    with pytest.warns(UserWarning):
        reservation.stop()


def test_multiple_start_stop_cycles(aws_device):
    reservation = DirectReservation(aws_device, RESERVATION_ARN)
    reservation.start()
    reservation.stop()
    reservation.start()
    reservation.stop()
    assert not os.getenv("AMZN_BRAKET_RESERVATION_DEVICE_ARN")
    assert not os.getenv("AMZN_BRAKET_RESERVATION_TIME_WINDOW_ARN")


def test_two_direct_reservations(aws_device):
    with pytest.raises(RuntimeError, match=RUNTIME_ERROR_MESSAGE):
        with DirectReservation(aws_device, RESERVATION_ARN):
            with DirectReservation(aws_device, "reservation_arn_example_2"):
                pass


def test_create_quantum_task_with_correct_device_and_reservation(aws_device):
    kwargs = {"deviceArn": DEVICE_ARN, "shots": 1}
    with patch("boto3.client"):
        mock_client = MagicMock()
        aws_session = AwsSession(braket_client=mock_client)
        with DirectReservation(aws_device, RESERVATION_ARN):
            aws_session.create_quantum_task(**kwargs)
            kwargs["associations"] = [
                {
                    "arn": RESERVATION_ARN,
                    "type": "RESERVATION_TIME_WINDOW_ARN",
                }
            ]
            mock_client.create_quantum_task.assert_called_once_with(**kwargs)


def test_warning_for_overridden_reservation_arn(aws_device):
    kwargs = {
        "deviceArn": DEVICE_ARN,
        "shots": 1,
        "associations": [
            {
                "arn": "task_reservation_arn",
                "type": "RESERVATION_TIME_WINDOW_ARN",
            }
        ],
    }
    correct_kwargs = {
        "deviceArn": DEVICE_ARN,
        "shots": 1,
        "associations": [
            {
                "arn": RESERVATION_ARN,
                "type": "RESERVATION_TIME_WINDOW_ARN",
            }
        ],
    }
    with patch("boto3.client"):
        mock_client = MagicMock()
        aws_session = AwsSession(braket_client=mock_client)
        with pytest.warns(
            UserWarning,
            match="A reservation ARN was passed to 'CreateQuantumTask', but it is being overridden",
        ):
            with DirectReservation(aws_device, RESERVATION_ARN):
                aws_session.create_quantum_task(**kwargs)
                mock_client.create_quantum_task.assert_called_once_with(**correct_kwargs)


def test_warning_not_triggered_wrong_association_type():
    kwargs = {
        "deviceArn": DEVICE_ARN,
        "shots": 1,
        "associations": [{"type": "OTHER_TYPE"}],
    }
    with patch("boto3.client"):
        mock_client = MagicMock()
        aws_session = AwsSession(braket_client=mock_client)
        aws_session.create_quantum_task(**kwargs)
        mock_client.create_quantum_task.assert_called_once_with(**kwargs)
