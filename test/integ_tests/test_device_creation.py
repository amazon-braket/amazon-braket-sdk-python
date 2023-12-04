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

from typing import List, Set

import pytest

from braket.aws import AwsDevice
from braket.devices import Devices

RIGETTI_ARN = "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-3"
IONQ_ARN = "arn:aws:braket:us-east-1::device/qpu/ionq/Harmony"
SIMULATOR_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
OQC_ARN = "arn:aws:braket:eu-west-2::device/qpu/oqc/Lucy"
PULSE_ARN = "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-3"


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


@pytest.mark.parametrize("arn", [(PULSE_ARN)])
def test_device_gate_calibrations(arn, aws_session):
    device = AwsDevice(arn, aws_session=aws_session)
    assert device.gate_calibrations


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


def _get_provider_name(device: AwsDevice) -> str:
    arn_provider = device.arn.split("/")[2]

    # capitalize as in provider name
    provider_primary_name = device.provider_name.split()[0]
    if arn_provider == provider_primary_name.lower():
        capitalized = provider_primary_name
    else:
        capitalized = arn_provider.upper()

    # remove dashes
    return capitalized.replace("-", "")


def _get_device_name(device: AwsDevice) -> str:
    arn_device_name = device.arn.split("/")[-1]

    device_name = (
        arn_device_name.replace("Advantage_system", "Advantage").replace("_", "").replace("-", "")
    )

    if device.provider_name == "Amazon Braket":
        device_name = device_name.upper()
    return device_name


def _get_active_providers(aws_devices: List[AwsDevice]) -> Set[str]:
    active_providers = set()
    for device in aws_devices:
        if device.status != "RETIRED":
            active_providers.add(_get_provider_name(device))
    return active_providers


def _validate_device(device: AwsDevice, active_providers: Set[str]):
    provider_name = _get_provider_name(device)
    if provider_name not in active_providers:
        provider_name = f"_{provider_name}"
    device_name = _get_device_name(device)
    if device.status == "RETIRED":
        device_name = f"_{device_name}"

    assert getattr(getattr(Devices, provider_name), device_name) == device.arn


def test_device_enum():
    aws_devices = AwsDevice.get_devices()
    active_providers = _get_active_providers(aws_devices)

    # validate all devices in API
    for device in aws_devices:
        _validate_device(device, active_providers)

    # validate all devices in enum
    providers = [getattr(Devices, attr) for attr in dir(Devices) if not attr.startswith("__")]
    for provider in providers:
        for device_arn in provider:
            device = AwsDevice(device_arn)
            _validate_device(device, active_providers)
