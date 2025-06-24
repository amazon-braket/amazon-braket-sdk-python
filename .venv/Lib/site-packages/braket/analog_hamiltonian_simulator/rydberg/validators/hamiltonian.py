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

from pydantic.v1 import root_validator

from braket.ir.ahs.hamiltonian import Hamiltonian


class HamiltonianValidator(Hamiltonian):
    @root_validator(pre=True, skip_on_failure=True)
    def max_one_driving_field(cls, values):
        driving_fields = values["drivingFields"]
        if len(driving_fields) > 1:
            raise ValueError(
                f"At most one driving field should be specified; {len(driving_fields)} are given."
            )
        return values

    @root_validator(pre=True, skip_on_failure=True)
    def max_one_local_detuning(cls, values):
        local_detunings = values["localDetuning"]
        if len(local_detunings) > 1:
            raise ValueError(
                f"At most one shifting field should be specified; {len(local_detunings)} are given."
            )
        return values

    @root_validator(pre=True, skip_on_failure=True)
    def all_sequences_in_driving_and_local_detunings_have_the_same_last_timepoint(cls, values):
        d_field_names = {"amplitude", "phase", "detuning"}
        s_field_names = {"magnitude"}
        end_times = {}
        for index, field in enumerate(values["drivingFields"]):
            for name in d_field_names:
                end_times[f"{name} of driving field {index}"] = field[name]["time_series"]["times"][
                    -1
                ]
        for index, field in enumerate(values["localDetuning"]):
            for name in s_field_names:
                end_times[f"{name} of shifting field {index}"] = field[name]["time_series"][
                    "times"
                ][-1]

        if len(set(end_times.values())) > 1:
            raise ValueError("The timepoints for all the sequences are not equal.")
        return values
