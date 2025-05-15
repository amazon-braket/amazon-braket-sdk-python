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

import enum
from braket.experimental_capabilities.experimental_capability import (
    register_capabilities,
    ExperimentalCapability,
)


@register_capabilities
class IqmExperimentalCapabilities(enum.Enum):
    classical_control = ExperimentalCapability(
        "classical_control",
        description=(
            "Enable 'cc_prx' and `measure_ff` in a program to perform "
            "mid-circuit measurement and feedforward control."
        ),
    )
    another_capability = ExperimentalCapability(
        "another_capability", description="Another experimental capability"
    )
