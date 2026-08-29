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

"""Analog Hamiltonian Simulation is an emerging paradigm in quantum computing that
differs significantly from the traditional quantum circuit model. Instead of a
sequence of gates, an AHS program is defined by the time-dependent and space-dependent
parameters of the Hamiltonian. This module provides classes for defining atom
arrangements, driving fields, shifting fields, local detuning, and other components
for building AHS programs on QuEra devices.
"""

from braket.ahs.analog_hamiltonian_simulation import (
    AnalogHamiltonianSimulation,  # ruff:ignore[unused-import]
)
from braket.ahs.atom_arrangement import (  # ruff:ignore[unused-import]
    AtomArrangement,
    AtomArrangementItem,
    SiteType,
)
from braket.ahs.canvas import Canvas  # ruff:ignore[unused-import]
from braket.ahs.discretization_types import DiscretizationProperties  # ruff:ignore[unused-import]
from braket.ahs.driving_field import DrivingField  # ruff:ignore[unused-import]
from braket.ahs.field import Field  # ruff:ignore[unused-import]
from braket.ahs.hamiltonian import Hamiltonian  # ruff:ignore[unused-import]
from braket.ahs.local_detuning import LocalDetuning  # ruff:ignore[unused-import]
from braket.ahs.pattern import Pattern  # ruff:ignore[unused-import]
from braket.ahs.shifting_field import ShiftingField  # ruff:ignore[unused-import]
