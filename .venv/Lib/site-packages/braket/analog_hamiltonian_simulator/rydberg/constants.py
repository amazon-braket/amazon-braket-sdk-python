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

from braket.analog_hamiltonian_simulator.rydberg.validators.capabilities_constants import (
    CapabilitiesConstants,
)

# Default units for simulation
TIME_UNIT = 1e-6  # Time unit for simulation is 1e-6 seconds
SPACE_UNIT = 1e-6  # Space unit for simulation is 1e-6 meters
FIELD_UNIT = 1e6  # Frequency unit for simulation is 1e6 Hz

# All the quantities below are in SI units

# Interaction strength
RYDBERG_INTERACTION_COEF = 5.42e-24

BOUNDING_BOX_SIZE_X = 0.0001
BOUNDING_BOX_SIZE_Y = 0.0001
MIN_BLOCKADE_RADIUS = 1e-06
MAX_TIME = 20e-6
MIN_DISTANCE = 4e-6

# Constants for Rabi frequency amplitude
GLOBAL_AMPLITUDE_VALUE_MIN = 0
GLOBAL_AMPLITUDE_VALUE_MAX = 25000000.0

# Constants for global detuning
GLOBAL_DETUNING_VALUE_MIN = -125000000.0
GLOBAL_DETUNING_VALUE_MAX = 125000000.0

# Constants for local detuning (shift)
LOCAL_MAGNITUDE_SEQUENCE_VALUE_MIN = -125000000.0
LOCAL_MAGNITUDE_SEQUENCE_VALUE_MAX = 125000000.0
MAGNITUDE_PATTERN_VALUE_MIN = 0.0
MAGNITUDE_PATTERN_VALUE_MAX = 1.0

# Maximum net detuning for all atoms
MAX_NET_DETUNING = 2e8


def capabilities_constants() -> CapabilitiesConstants:
    return CapabilitiesConstants(
        BOUNDING_BOX_SIZE_X=BOUNDING_BOX_SIZE_X,
        BOUNDING_BOX_SIZE_Y=BOUNDING_BOX_SIZE_Y,
        MAX_TIME=MAX_TIME,
        MIN_DISTANCE=MIN_DISTANCE,
        GLOBAL_AMPLITUDE_VALUE_MIN=GLOBAL_AMPLITUDE_VALUE_MIN,
        GLOBAL_AMPLITUDE_VALUE_MAX=GLOBAL_AMPLITUDE_VALUE_MAX,
        GLOBAL_DETUNING_VALUE_MIN=GLOBAL_DETUNING_VALUE_MIN,
        GLOBAL_DETUNING_VALUE_MAX=GLOBAL_DETUNING_VALUE_MAX,
        LOCAL_MAGNITUDE_SEQUENCE_VALUE_MIN=LOCAL_MAGNITUDE_SEQUENCE_VALUE_MIN,
        LOCAL_MAGNITUDE_SEQUENCE_VALUE_MAX=LOCAL_MAGNITUDE_SEQUENCE_VALUE_MAX,
        MAGNITUDE_PATTERN_VALUE_MIN=MAGNITUDE_PATTERN_VALUE_MIN,
        MAGNITUDE_PATTERN_VALUE_MAX=MAGNITUDE_PATTERN_VALUE_MAX,
        MAX_NET_DETUNING=MAX_NET_DETUNING,
    )
