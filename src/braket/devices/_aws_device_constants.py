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

# This file contains hardcoded values for Amazon Braket devices;
# remove when these values are available in device capabilities

from collections.abc import Iterable
from functools import singledispatch

from braket.device_schema import DeviceCapabilities
from braket.device_schema.ionq import IonqDeviceCapabilities
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.devices import Devices

"""
The following values are not available through Braket device
calibration data and must be hardcoded.
"""
_QPU_GATE_DURATIONS = {
    Devices.Rigetti.Ankaa2: {
        "single_qubit_gate_duration": 40e-9,
        "two_qubit_gate_duration": 240e-9,
    },
    Devices.IQM.Garnet: {"single_qubit_gate_duration": 32e-9, "two_qubit_gate_duration": 60e-9},
}

_GATE_TRANSLATONS_RIGETTI = {"CPHASE": "CPhaseShift"}
_GATE_TRANSLATIONS_IONQ = {"GPI": "GPi", "GPI2": "GPi2"}


def _get_qpu_gate_translations(
    properties: DeviceCapabilities, gate_name: str | Iterable[str]
) -> str | list[str]:
    """Returns the translated gate name(s) for a given QPU device capabilities schema type
        and gate name(s).

    Args:
        properties (DeviceCapabilities): Device capabilities object based on a
            device-specific schema.
        gate_name (str | Iterable[str]): The name(s) of the gate(s). If gate_name is a list
            of string gate names, this function attempts to retrieve translations of all the gate
            names.

    Returns:
        str | list[str]: The translated gate name(s)
    """
    if isinstance(gate_name, str):
        return _get_qpu_gate_translation(properties, gate_name)
    else:
        return [_get_qpu_gate_translation(properties, name) for name in gate_name]


@singledispatch
def _get_qpu_gate_translation(properties: DeviceCapabilities, gate_name: str) -> str:
    """Returns the translated gate name for a given QPU ARN and gate name.

    Args:
        properties (DeviceCapabilities): QPU Device Capabilities object with a
            QHP-specific schema.
        gate_name (str): The name of the gate

    Returns:
        str: The translated gate name
    """
    return gate_name


@_get_qpu_gate_translation.register
def _(_: RigettiDeviceCapabilities, gate_name: str) -> str:
    translations = {"CPHASE": "CPhaseShift"}
    return translations.get(gate_name, gate_name)


@_get_qpu_gate_translation.register(IonqDeviceCapabilities)
def _(_: IonqDeviceCapabilities, gate_name: str) -> str:
    translations = {"GPI": "GPi", "GPI2": "GPi2"}
    return translations.get(gate_name, gate_name)
