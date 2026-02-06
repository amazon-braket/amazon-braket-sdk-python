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

from braket.device_schema.device_action_properties import DeviceActionProperties, DeviceActionType

from braket.emulation.passes import ValidationPass
from braket.program_sets import ProgramSet


class ProgramSetValidator(ValidationPass):
    def __init__(self, device_action: dict[DeviceActionType, DeviceActionProperties]):
        """
        A validator that checks whether or not the device supports the Specification.

        Args:
            device_action (dict): The device.properties.action dictionary.

        Raises:
            ValueError: The task specification is not supported.
        """
        self.device_actions = device_action
        self._supported_specifications = ProgramSet

    def validate(self, task_specification: ProgramSet) -> None:
        """
        Validates the number of executables and total program shots are valid.

        Args:
            task_specification (ProgramSet): The Braket circuit whose qubit count to validate.

        Raises:
            ValueError: Too many executables or too many shots.

        """
        pset_action = self.device_actions["braket.ir.openqasm.program_set"]
        if not isinstance(pset_action, dict):
            pset_action = pset_action.dict()
        max_shots = pset_action["maximumTotalShots"]
        max_exc = pset_action["maximumExecutables"]
        if len(task_specification) > max_exc:
            raise ValueError(
                f"{len(task_specification)} is greater than "
                f"the supported number of executables {max_exc}."
            )

        if len(task_specification) * task_specification.shots_per_executable > max_shots:
            raise ValueError(
                f"{len(task_specification) * task_specification.shots_per_executable} > "
                f"is greater than the total shot limit {max_shots}."
            )
