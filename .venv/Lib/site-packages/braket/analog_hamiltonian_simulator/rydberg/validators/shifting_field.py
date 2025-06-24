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

from pydantic.v1.class_validators import root_validator

from braket.analog_hamiltonian_simulator.rydberg.validators.capabilities_constants import (
    CapabilitiesConstants,
)
from braket.analog_hamiltonian_simulator.rydberg.validators.field_validator_util import (
    validate_value_range_with_warning,
)
from braket.ir.ahs.local_detuning import LocalDetuning


class LocalDetuningValidator(LocalDetuning):
    capabilities: CapabilitiesConstants

    @root_validator(pre=True, skip_on_failure=True)
    def magnitude_pattern_is_not_uniform(cls, values):
        magnitude = values["magnitude"]
        pattern = magnitude["pattern"]
        if isinstance(pattern, str):
            raise ValueError(f"Pattern of shifting field must be not be a string - {pattern}")
        return values

    @root_validator(pre=True, skip_on_failure=True)
    def magnitude_pattern_within_bounds(cls, values):
        magnitude = values["magnitude"]
        capabilities = values["capabilities"]
        pattern = magnitude["pattern"]
        for index, pattern_value in enumerate(pattern):
            if (pattern_value < capabilities.MAGNITUDE_PATTERN_VALUE_MIN) or (
                pattern_value > capabilities.MAGNITUDE_PATTERN_VALUE_MAX
            ):
                raise ValueError(
                    f"magnitude pattern value {index} is {pattern_value}; it must be between "
                    f"{capabilities.MAGNITUDE_PATTERN_VALUE_MIN} and "
                    f"{capabilities.MAGNITUDE_PATTERN_VALUE_MAX} (inclusive)."
                )
        return values

    @root_validator(pre=True, skip_on_failure=True)
    def magnitude_values_within_range(cls, values):
        magnitude = values["magnitude"]
        capabilities = values["capabilities"]
        magnitude_values = magnitude["time_series"]["values"]
        validate_value_range_with_warning(
            magnitude_values,
            capabilities.LOCAL_MAGNITUDE_SEQUENCE_VALUE_MIN,
            capabilities.LOCAL_MAGNITUDE_SEQUENCE_VALUE_MAX,
            "magnitude",
        )
        return values
