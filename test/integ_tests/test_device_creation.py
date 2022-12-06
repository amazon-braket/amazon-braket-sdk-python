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

import pytest

from braket.aws import AwsDevice

RIGETTI_ARN = "arn:aws:braket:::device/qpu/rigetti/Aspen-10"
IONQ_ARN = "arn:aws:braket:::device/qpu/ionq/ionQdevice"
SIMULATOR_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
OQC_ARN = "arn:aws:braket:eu-west-2::device/qpu/oqc/Lucy"
PULSE_ARN = "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-2-pulse"


@pytest.mark.parametrize(
    "arn", [(RIGETTI_ARN), (IONQ_ARN), (OQC_ARN), (SIMULATOR_ARN), (PULSE_ARN)]
)
def test_device_creation(arn, aws_session):
    device = AwsDevice(arn, aws_session=aws_session)
    assert device.arn == arn
    assert device.name
    assert device.status
    assert device.type
    assert device.provider_name
    assert device.properties


@pytest.mark.parametrize("arn", [(PULSE_ARN)])
def test_device_pulse_properties(arn, aws_session):
    device = AwsDevice(arn, aws_session=aws_session)
    assert device.ports
    assert device.frames


def test_device_across_regions(aws_session):
    # assert QPUs across different regions can be created using the same aws_session
    AwsDevice(RIGETTI_ARN, aws_session)
    AwsDevice(IONQ_ARN, aws_session)
    AwsDevice(OQC_ARN, aws_session)


@pytest.mark.parametrize("arn", [(RIGETTI_ARN), (IONQ_ARN), (OQC_ARN), (SIMULATOR_ARN)])
def test_get_devices_arn(arn):
    results = AwsDevice.get_devices(arns=[arn])
    assert results[0].arn == arn


def test_get_devices_others():
    provider_names = ["Amazon Braket"]
    types = ["SIMULATOR"]
    statuses = ["ONLINE"]
    results = AwsDevice.get_devices(provider_names=provider_names, types=types, statuses=statuses)
    assert results
    for result in results:
        assert result.provider_name in provider_names
        assert result.type in types
        assert result.status in statuses


def test_get_devices_all():
    result_arns = [result.arn for result in AwsDevice.get_devices()]
    for arn in [RIGETTI_ARN, IONQ_ARN, SIMULATOR_ARN, OQC_ARN]:
        assert arn in result_arns
