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
from decimal import Decimal

import numpy as np

from braket.analog_hamiltonian_simulator.rydberg.validators.capabilities_constants import (
    CapabilitiesConstants,
)
from braket.ir.ahs.program_v1 import Program


def validate_value_range_with_warning(
    values: list[Decimal], min_value: Decimal, max_value: Decimal, name: str
) -> None:
    """
    Validate the given list of values against the allowed range

    Args:
        values (list[Decimal]): The given list of values to be validated
        min_value (Decimal): The minimal value allowed
        max_value (Decimal): The maximal value allowed
        name (str): The name of the field corresponds to the values
    """
    # Raise ValueError if at any item in the values is outside the allowed range
    # [min_value, max_value]
    for i, value in enumerate(values):
        if not min_value <= value <= max_value:
            warnings.warn(
                f"Value {i} ({value}) in {name} time series outside the typical range "
                f"[{min_value}, {max_value}]. The values should  be specified in SI units."
            )
            break  # Only one warning messasge will be issued


def validate_net_detuning_with_warning(
    program: Program,
    time_points: np.ndarray,
    global_detuning_coefs: np.ndarray,
    local_detuning_patterns: list,
    local_detuning_coefs: np.ndarray,
    capabilities: CapabilitiesConstants,
) -> Program:
    """
    Validate the given program for the net detuning of all the atoms at all time points

    Args:
        program (Program): The given program
        time_points (np.ndarray): The time points for both global and local detunings
        global_detuning_coefs (np.ndarray): The values of global detuning
        local_detuning_patterns (List): The pattern of local detuning
        local_detuning_coefs (np.ndarray): The values of local detuning
        capabilities (CapabilitiesConstants): The capability constants

    Returns:
        program (Program): The given program
    """

    for time_ind, time in enumerate(time_points):
        # Get the contributions from all the global detunings
        # (there could be multiple global driving fields) at the time point
        values_global_detuning = sum(
            [detuning_coef[time_ind] for detuning_coef in global_detuning_coefs]
        )

        for atom_index in range(len(local_detuning_patterns[0])):
            # Get the contributions from local detuning at the time point
            values_local_detuning = sum(
                [
                    shift_coef[time_ind] * float(detuning_pattern[atom_index])
                    for detuning_pattern, shift_coef in zip(
                        local_detuning_patterns, local_detuning_coefs
                    )
                ]
            )

            # The net detuning is the sum of both the global and local detunings
            detuning_to_check = np.real(values_local_detuning + values_global_detuning)

            # Issue a warning if the absolute value of the net detuning is
            # beyond MAX_NET_DETUNING
            if abs(detuning_to_check) > capabilities.MAX_NET_DETUNING:
                warnings.warn(
                    f"Atom {atom_index} has net detuning {detuning_to_check} rad/s "
                    f"at time {time} seconds, which is outside the typical range "
                    f"[{-capabilities.MAX_NET_DETUNING}, {capabilities.MAX_NET_DETUNING}]."
                    f"Numerical instabilities may occur during simulation."
                )

                # Return immediately if there is an atom has net detuning
                # exceeding MAX_NET_DETUNING at a time point
                return program
