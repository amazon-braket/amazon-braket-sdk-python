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

from braket.emulation._standardization import (
    _standardize_ionq_device_properties,
)
from braket.device_schema.iqm.iqm_device_capabilities_v1 import IqmDeviceCapabilities


def test_standardize_ionq_device_properties(reduced_ionq_device_capabilities):
    device_properties = _standardize_ionq_device_properties(reduced_ionq_device_capabilities)
    device_em_properties = DeviceEmulatorProperties.from_device_properties(device_properties)
    assert device_em_properties.qubit_count == 25


def test_invalid_standardize_ionq_device_properties(reduced_standardized_json_3):
    device_properties = IqmDeviceCapabilities.parse_raw(reduced_standardized_json_3)
    with pytest.raises(ValueError):
        _standardize_ionq_device_properties(device_properties)
