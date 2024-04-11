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

from unittest.mock import Mock

import pytest

from braket.aws.aws_device import AwsDevice, AwsDeviceType
from braket.devices.local_simulator import LocalSimulator
from braket.reservations import Reservation


def test_non_braket_device():
    non_device = Mock()
    with pytest.raises(ValueError):
        with Reservation(non_device):
            pass


def test_local_simulator():
    local_simulator = Mock(spec=LocalSimulator)
    local_simulator.run = Mock()

    with Reservation(local_simulator, reservation_arn="arn:test"):
        local_simulator.run("circuit", 100)

    local_simulator.run.assert_called_once_with("circuit", 100)


def test_aws_simulator():
    simulator_device = Mock(spec=AwsDevice)
    simulator_device.type = AwsDeviceType.SIMULATOR
    simulator_device.run = Mock()

    with Reservation(simulator_device, reservation_arn="arn:test"):
        simulator_device.run("circuit", 100)

    simulator_device.run.assert_called_once_with("circuit", 100)


@pytest.mark.parametrize("reservation_arn", [None, "arn:test"])
def test_qpu_device(reservation_arn):
    qpu_device = Mock(spec=AwsDevice)
    qpu_device.type = AwsDeviceType.QPU
    qpu_device.run = Mock()

    with Reservation(qpu_device, reservation_arn=reservation_arn):
        qpu_device.run("circuit", 100)

    qpu_device.run.assert_called_once_with("circuit", 100, reservation_arn=reservation_arn)
