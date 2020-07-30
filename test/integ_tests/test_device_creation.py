# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import pytest

from braket.aws import AwsDevice

DWAVE_ARN = "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6"
RIGETTI_ARN = "arn:aws:braket:::device/qpu/rigetti/Aspen-8"
IONQ_ARN = "arn:aws:braket:::device/qpu/ionq/ionQdevice"
SIMULATOR_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"


@pytest.mark.parametrize("arn", [(RIGETTI_ARN), (IONQ_ARN), (DWAVE_ARN), (SIMULATOR_ARN)])
def test_qpu_creation(arn, aws_session):
    device = AwsDevice(arn, aws_session=aws_session)
    assert device.arn == arn


def test_device_across_regions(aws_session):
    # assert QPUs across different regions can be created using the same aws_session
    AwsDevice(RIGETTI_ARN, aws_session)
    AwsDevice(IONQ_ARN, aws_session)
