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

from braket.ir.ahs.physical_field import PhysicalField


class PhysicalFieldValidator(PhysicalField):
    # Pattern, if string, must be "uniform"
    @root_validator(pre=True, skip_on_failure=True)
    def pattern_str(cls, values):
        pattern = values["pattern"]
        if isinstance(pattern, str):
            if pattern != "uniform":
                raise ValueError(f'Invalid pattern string ({pattern}); only string: "uniform"')
        return values
