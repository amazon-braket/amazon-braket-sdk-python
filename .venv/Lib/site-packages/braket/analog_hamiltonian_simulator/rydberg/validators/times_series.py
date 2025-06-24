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

import warnings

from pydantic.v1.class_validators import root_validator

from braket.analog_hamiltonian_simulator.rydberg.validators.capabilities_constants import (
    CapabilitiesConstants,
)
from braket.ir.ahs.time_series import TimeSeries


class TimeSeriesValidator(TimeSeries):
    capabilities: CapabilitiesConstants

    # must have at least 2 time values
    @root_validator(pre=True, skip_on_failure=True)
    def at_least_2_timepoints(cls, values):
        times = values["times"]
        length = len(times)
        min_length = 2
        if length < min_length:
            raise ValueError(f"Length of times must be at least {min_length}; it is {length}")
        return values

    # the first times entry should be 0
    @root_validator(pre=True, skip_on_failure=True)
    def times_start_with_0(cls, values):
        times = values["times"]
        if times[0] != 0.0:
            raise ValueError(f"First time value is {times[0]}; it must be 0.0")
        return values

    # The duration of the program should be below MAX_TIME
    # If not, a warning message will be issue to remind the user that the SI units are used here.
    @root_validator(pre=True, skip_on_failure=True)
    def times_are_not_too_big(cls, values):
        times = values["times"]
        capabilities = values["capabilities"]
        if times[-1] > capabilities.MAX_TIME:
            warnings.warn(
                f"Max time is {times[-1]} seconds which is bigger than the typical scale "
                f"({capabilities.MAX_TIME} seconds). "
                "The time points should be specified in SI units."
            )
        return values

    # The time array must be sorted in ascending order
    @root_validator(pre=True, skip_on_failure=True)
    def times_must_be_ascendingly_sorted(cls, values):
        times = values["times"]
        for i in range(len(times) - 1):
            if times[i] >= times[i + 1]:
                raise ValueError(
                    f"Time point {i} ({times[i]}) and time point {i + 1} ({times[i + 1]}) "
                    "must be monotonically increasing."
                )
        return values

    # Check that the times and the values have the same length
    @root_validator(pre=True, skip_on_failure=True)
    def check_times_and_values_have_same_length(cls, values):
        len_times = len(values["times"])
        len_values = len(values["values"])
        if len_values != len_times:
            raise ValueError(
                f"The sample times (length: {len_times}) and the values (length: {len_values}) "
                "must have the same length."
            )
        return values
