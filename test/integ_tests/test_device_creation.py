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
from braket.devices import Devices

RIGETTI_ARN = "arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-2"
IONQ_ARN = "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1"
IQM_ARN = "arn:aws:braket:eu-north-1::device/qpu/iqm/Garnet"
SIMULATOR_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
PULSE_ARN = "arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-2"


@pytest.mark.parametrize(
    "arn", [(RIGETTI_ARN), (IONQ_ARN), (IQM_ARN), (SIMULATOR_ARN), (PULSE_ARN)]
)
def test_device_creation(arn, created_braket_devices):
    device = created_braket_devices[arn]
    assert device.arn == arn
    assert device.name
    assert device.status
    assert device.type
    assert device.provider_name
    assert device.properties


@pytest.mark.parametrize("arn", [PULSE_ARN])
def test_device_pulse_properties(arn, aws_session, created_braket_devices):
    device = created_braket_devices[arn]
    assert device.ports
    assert device.frames


def test_device_across_regions(aws_session, created_braket_devices):
    # assert QPUs across different regions can be created using the same aws_session
    created_braket_devices[RIGETTI_ARN]
    created_braket_devices[IONQ_ARN]
    created_braket_devices[IQM_ARN]


@pytest.mark.parametrize("arn", [(IONQ_ARN), (IQM_ARN), (SIMULATOR_ARN)])
def test_get_devices_arn(arn):
    results = AwsDevice.get_devices(arns=[arn])
    assert results[0].arn == arn


@pytest.mark.parametrize("arn", [PULSE_ARN])
def test_device_gate_calibrations(arn, aws_session, created_braket_devices):
    device = created_braket_devices[arn]
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


def test_get_devices_all(braket_devices):
    result_arns = [result.arn for result in braket_devices]
    for arn in [RIGETTI_ARN, IONQ_ARN, IQM_ARN, SIMULATOR_ARN]:
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


def _get_active_providers(aws_devices: list[AwsDevice]) -> set[str]:
    active_providers = {
        _get_provider_name(device) for device in aws_devices if device.status != "RETIRED"
    }
    return active_providers


def _validate_device(device: AwsDevice, active_providers: set[str]):
    provider_name = _get_provider_name(device)
    if provider_name not in active_providers:
        provider_name = f"_{provider_name}"
    device_name = _get_device_name(device)
    if device.status == "RETIRED":
        device_name = f"_{device_name}"

    assert getattr(getattr(Devices, provider_name), device_name) == device.arn


def test_device_enum(braket_devices, created_braket_devices):
    active_providers = _get_active_providers(braket_devices)

    # validate all devices in API
    for device in braket_devices:
        _validate_device(device, active_providers)

    # validate all devices in enum
    providers = [getattr(Devices, attr) for attr in dir(Devices) if not attr.startswith("__")]
    for provider in providers:
        for device_arn in provider:
            device = created_braket_devices[device_arn]
            _validate_device(device, active_providers)
