# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from braket.emulation.device_emulator_properties import (
    DeviceEmulatorProperties,
)

from braket.emulation.device_emulator_utils import (
    standardize_ionq_device_properties_json,
    standardize_ionq_device_properties,
)
from braket.device_schema.iqm.iqm_device_capabilities_v1 import IqmDeviceCapabilities

from conftest import valid_supportedResultTypes


def test_standardize_ionq_device_properties_json(reduced_ionq_device_capabilities_json):
    device_properties_json = standardize_ionq_device_properties_json(
        reduced_ionq_device_capabilities_json
    )
    device_em_properties = DeviceEmulatorProperties.from_json(device_properties_json)
    assert device_em_properties.qubitCount == 25
    assert device_em_properties.nativeGateSet == ["gpi", "gpi2", "ms"]
    assert device_em_properties.connectivityGraph == {}
    for i in range(25):
        assert device_em_properties.oneQubitProperties[f"{i}"].T1.value == 123.45678
        if i != 3:
            edge = [3, i]
            edge = f"{min(edge)}-{max(edge)}"
            assert (
                device_em_properties.twoQubitProperties[edge].twoQubitGateFidelity[0].gateName
                == "MS"
            )
            assert (
                device_em_properties.twoQubitProperties[edge].twoQubitGateFidelity[0].fidelity
                == 0.12345
            )
            assert (
                device_em_properties.twoQubitProperties[edge].twoQubitGateFidelity[0].standardError
                == None
            )

    assert device_em_properties.supportedResultTypes == valid_supportedResultTypes
    assert device_em_properties.qubit_labels == list(range(25))
    assert device_em_properties.fully_connected == True
    assert device_em_properties.directed == False


def test_standardize_ionq_device_properties(reduced_ionq_device_capabilities):
    device_properties = standardize_ionq_device_properties(reduced_ionq_device_capabilities)
    device_em_properties = DeviceEmulatorProperties.from_device_properties(device_properties)
    assert device_em_properties.qubitCount == 25


def test_invalid_standardize_ionq_device_properties_json(reduced_standardized_json_3):
    with pytest.raises(ValueError):
        standardize_ionq_device_properties_json(reduced_standardized_json_3)


def test_invalid_standardize_ionq_device_properties(reduced_standardized_json_3):
    device_properties = IqmDeviceCapabilities.parse_raw(reduced_standardized_json_3)
    with pytest.raises(ValueError):
        standardize_ionq_device_properties(device_properties)
