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

from __future__ import annotations

from collections import defaultdict
from functools import singledispatch

import braket.ir.ahs as ir
from braket.ahs.atom_arrangement import AtomArrangement, SiteType
from braket.ahs.discretization_types import DiscretizationError, DiscretizationProperties
from braket.ahs.driving_field import DrivingField
from braket.ahs.hamiltonian import Hamiltonian
from braket.ahs.shifting_field import ShiftingField
from braket.device_schema import DeviceActionType


class AnalogHamiltonianSimulation:
    SHIFTING_FIELDS_PROPERTY = "shifting_fields"
    DRIVING_FIELDS_PROPERTY = "driving_fields"

    def __init__(self, register: AtomArrangement, hamiltonian: Hamiltonian) -> None:
        """Creates an AnalogHamiltonianSimulation with a given setup, and terms.

        Args:
            register (AtomArrangement): The initial atom arrangement for the simulation.
            hamiltonian (Hamiltonian): The hamiltonian to simulate.
        """
        self._register = register
        self._hamiltonian = hamiltonian

    @property
    def register(self) -> AtomArrangement:
        """AtomArrangement: The initial atom arrangement for the simulation."""
        return self._register

    @property
    def hamiltonian(self) -> Hamiltonian:
        """Hamiltonian: The hamiltonian to simulate."""
        return self._hamiltonian

    def to_ir(self) -> ir.Program:
        """Converts the Analog Hamiltonian Simulation into the canonical intermediate
        representation.

        Returns:
            Program: A representation of the circuit in the IR format.
        """
        return ir.Program(
            setup=ir.Setup(ahs_register=self._register_to_ir()),
            hamiltonian=self._hamiltonian_to_ir(),
        )

    def _register_to_ir(self) -> ir.AtomArrangement:
        return ir.AtomArrangement(
            sites=[site.coordinate for site in self.register],
            filling=[1 if site.site_type == SiteType.FILLED else 0 for site in self.register],
        )

    def _hamiltonian_to_ir(self) -> ir.Hamiltonian:
        terms = defaultdict(list)
        for term in self.hamiltonian.terms:
            term_type, term_ir = _get_term_ir(term)
            terms[term_type].append(term_ir)
        return ir.Hamiltonian(
            drivingFields=terms[AnalogHamiltonianSimulation.DRIVING_FIELDS_PROPERTY],
            shiftingFields=terms[AnalogHamiltonianSimulation.SHIFTING_FIELDS_PROPERTY],
        )

    def discretize(self, device) -> AnalogHamiltonianSimulation:  # noqa
        """Creates a new AnalogHamiltonianSimulation with all numerical values represented
        as Decimal objects with fixed precision based on the capabilities of the device.

        Args:
            device (AwsDevice): The device for which to discretize the program.

        Returns:
            AnalogHamiltonianSimulation: A discretized version of this program.

        Raises:
            DiscretizeError: If unable to discretize the program.
        """

        required_action_schema = DeviceActionType.AHS
        if (required_action_schema not in device.properties.action) or (
            device.properties.action[required_action_schema].actionType != required_action_schema
        ):
            raise DiscretizationError(
                f"AwsDevice {device} does not accept {required_action_schema} action schema."
            )

        properties = DiscretizationProperties(
            device.properties.paradigm.lattice, device.properties.paradigm.rydberg
        )
        discretized_register = self.register.discretize(properties)
        discretized_hamiltonian = self.hamiltonian.discretize(properties)
        return AnalogHamiltonianSimulation(
            register=discretized_register, hamiltonian=discretized_hamiltonian
        )


@singledispatch
def _get_term_ir(
    term: Hamiltonian,
) -> tuple[str, dict]:
    raise TypeError(f"Unable to convert Hamiltonian term type {type(term)}.")


@_get_term_ir.register
def _(term: ShiftingField) -> tuple[str, ir.ShiftingField]:
    return AnalogHamiltonianSimulation.SHIFTING_FIELDS_PROPERTY, ir.ShiftingField(
        magnitude=ir.PhysicalField(
            time_series=ir.TimeSeries(
                times=term.magnitude.time_series.times(),
                values=term.magnitude.time_series.values(),
            ),
            pattern=term.magnitude.pattern.series,
        )
    )


@_get_term_ir.register
def _(term: DrivingField) -> tuple[str, ir.DrivingField]:
    return AnalogHamiltonianSimulation.DRIVING_FIELDS_PROPERTY, ir.DrivingField(
        amplitude=ir.PhysicalField(
            time_series=ir.TimeSeries(
                times=term.amplitude.time_series.times(),
                values=term.amplitude.time_series.values(),
            ),
            pattern="uniform",
        ),
        phase=ir.PhysicalField(
            time_series=ir.TimeSeries(
                times=term.phase.time_series.times(),
                values=term.phase.time_series.values(),
            ),
            pattern="uniform",
        ),
        detuning=ir.PhysicalField(
            time_series=ir.TimeSeries(
                times=term.detuning.time_series.times(),
                values=term.detuning.time_series.values(),
            ),
            pattern="uniform",
        ),
    )
