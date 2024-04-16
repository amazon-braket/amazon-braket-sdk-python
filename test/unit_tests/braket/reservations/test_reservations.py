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

import pytest

from braket.aws import AwsDevice

# Assuming DirectReservation is in a module named direct_reservation_module
from braket.reservations.reservations import DirectReservation


@pytest.fixture
def aws_device():
    device = AwsDevice("device_arn_example")
    return device


def test_initialization_with_string():
    """Test initialization with string device ARN and valid reservation ARN."""
    res = DirectReservation("device_arn_string", "reservation_arn_string")
    assert res.device_arn == "device_arn_string"
    assert res.reservation_arn == "reservation_arn_string"


def test_initialization_with_device(aws_device):
    """Test initialization with AwsDevice instance."""
    res = DirectReservation(aws_device, "reservation_arn_string")
    assert res.device_arn == "device_arn_example"


def test_environment_variables_set_and_cleared():
    """Test that environment variables are correctly set and cleared."""
    with DirectReservation("device_arn_string", "reservation_arn_string"):
        assert os.getenv("AMZN_BRAKET_DEVICE_ARN_TEMP") == "device_arn_string"
        assert os.getenv("AMZN_BRAKET_RESERVATION_ARN_TEMP") == "reservation_arn_string"
    # Check variables are cleared after context
    assert os.getenv("AMZN_BRAKET_DEVICE_ARN_TEMP") is None
    assert os.getenv("AMZN_BRAKET_RESERVATION_ARN_TEMP") is None


def test_start_raises_error_when_already_active():
    """Test that starting an already active context raises an error."""
    res = DirectReservation("device_arn_string", "reservation_arn_string")
    res.start()
    with pytest.raises(RuntimeError):
        res.start()
    res.stop()  # Ensure clean-up


def test_stop_raises_error_when_not_active():
    """Test that stopping a non-active context raises an error."""
    res = DirectReservation("device_arn_string", "reservation_arn_string")
    with pytest.raises(RuntimeError):
        res.stop()


def test_invalid_device_arn_type():
    """Test that passing an invalid device_arn type raises a ValueError."""
    with pytest.raises(ValueError):
        DirectReservation(123, "reservation_arn_string")  # Invalid type, should be str or AwsDevice
