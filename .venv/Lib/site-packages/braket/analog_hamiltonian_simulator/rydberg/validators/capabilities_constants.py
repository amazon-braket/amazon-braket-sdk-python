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

from decimal import Decimal

from pydantic import PositiveInt
from pydantic.v1.main import BaseModel


class CapabilitiesConstants(BaseModel):
    DIMENSIONS: PositiveInt = 2
    BOUNDING_BOX_SIZE_X: Decimal
    BOUNDING_BOX_SIZE_Y: Decimal
    MAX_TIME: Decimal
    MIN_DISTANCE: Decimal
    GLOBAL_AMPLITUDE_VALUE_MIN: Decimal
    GLOBAL_AMPLITUDE_VALUE_MAX: Decimal
    GLOBAL_DETUNING_VALUE_MIN: Decimal
    GLOBAL_DETUNING_VALUE_MAX: Decimal

    LOCAL_MAGNITUDE_SEQUENCE_VALUE_MIN: Decimal
    LOCAL_MAGNITUDE_SEQUENCE_VALUE_MAX: Decimal

    MAGNITUDE_PATTERN_VALUE_MIN: Decimal
    MAGNITUDE_PATTERN_VALUE_MAX: Decimal
    MAX_NET_DETUNING: Decimal
