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
from typing import Tuple
from decimal import Decimal

import braket.ir.ahs as ir
from braket.ahs.atom_arrangement import AtomArrangement, SiteType
from braket.ahs.driving_field import DrivingField
from braket.ahs.hamiltonian import Hamiltonian
from braket.ahs.shifting_field import ShiftingField


class DiscretizeError(Exception):
    """Raised if the discretization of the numerical values of the AHS program fails.
    """
    pass


class AnalogHamiltonianSimulation:
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
        return self._register

    @property
    def hamiltonian(self) -> Hamiltonian:
        return self._hamiltonian

    def to_ir(self) -> ir.Program:
        return ir.Program(
            setup=ir.Setup(atomArray=self._register_to_ir()), hamiltonian=self._hamiltonian_to_ir()
        )

    def _register_to_ir(self) -> ir.AtomArray:
        return ir.AtomArray(
            sites=[site.coordinate for site in self.register],
            filling=[1 if site.site_type == SiteType.FILLED else 0 for site in self.register],
        )

    def _hamiltonian_to_ir(self) -> ir.Hamiltonian:
        terms = defaultdict(list)
        for term in self.hamiltonian.terms:
            term_type, term_ir = _get_term_ir(term)
            terms[term_type].append(term_ir)
        return ir.Hamiltonian(
            drivingFields=terms["driving_fields"], shiftingFields=terms["shifting_fields"]
        )

    def discretize(self, device) -> AnalogHamiltonianSimulation:
        """ Creates a new AnalogHamiltonianSimulation with all numerical values represented
            as Decimal objects with fixed precision based on the capabilities of the device.

            Args:
                device (AwsDevice): The device for which to discretize the program.

            Returns:
                AnalogHamiltonianSimulation: A discretized version of this program.

            Raises:
                DiscretizeError: If unable to discretize the program.
        """

        # Gather resolution values

        register_position_resolution = device.properties.paradigm.lattice.geometry.positionResolution
        driving_parameters = device.properties.paradigm.rydberg.rydbergGlobal
        driving_field_resolutions = {
            'amplitude': {
                'time': driving_parameters.timeResolution,
                'value': driving_parameters.rabiFrequencyResolution
            },
            'detuning': {
                'time': driving_parameters.timeResolution,
                'value': driving_parameters.detuningResolution
            },
            'phase': {
                'time': driving_parameters.timeResolution,
                'value': driving_parameters.phaseResolution
            }
        }
        shifting_parameters = device.properties.paradigm.rydberg.rydbergLocal
        shifting_field_resolutions = {
            'magnitude': {
                'time': shifting_parameters.timeResolution,
                'value': shifting_parameters.commonDetuningResolution,
                'pattern': shifting_parameters.localDetuningResolution
            }
        }

        # Discretize register

        try:
            discretized_register = self.register.discretize(register_position_resolution)
        except:
            raise DiscretizeError(f'Failed to discretize register {self.register}')

        # Discretize Hamiltonian

        discretized_hamiltonian = Hamiltonian()
        for idx, term in enumerate(self.hamiltonian):
            if isinstance(term, DrivingField):
                resolutions = driving_field_resolutions
                fields = dict(
                    amplitude=term.amplitude,
                    phase=term.phase,
                    detuning=term.detuning
                )
            elif isinstance(term, ShiftingField):
                resolutions = shifting_field_resolutions
                fields = dict(
                    magnitude=term.magnitude
                )
            else:
                raise NotImplementedError(
                    f'Only DrivingField and ShiftingField terms can be discretized.'
                    f'Hamiltonian term {idx} is of type {type(term)}'
                )

            for field_name, original_field in fields.items():
                try:
                    time_res = resolutions[field_name]['time']
                    value_res = resolutions[field_name]['value']
                    pattern_res = resolutions[field_name].get('pattern')
                    fields[field_name] = original_field.discretize(time_res, value_res, pattern_res)
                except:
                    DiscretizeError(f'Failed to discretize {field_name} of Hamiltonian term {idx}: {original_field}')

            discretized_term = type(term)(**fields)
            discretized_hamiltonian += discretized_term

        return AnalogHamiltonianSimulation(
            resister=discretized_register,
            hamiltonian=discretized_hamiltonian
        )


@singledispatch
def _get_term_ir(
    term: Hamiltonian,
) -> Tuple[str, dict]:
    raise TypeError(f"Unable to convert Hamiltonian term type {type(term)}.")


@_get_term_ir.register
def _(term: ShiftingField) -> Tuple[str, ir.ShiftingField]:
    return "shifting_fields", ir.ShiftingField(
        magnitude=ir.PhysicalField(
            sequence=ir.Waveform(
                times=term.magnitude.time_series.times(),
                values=term.magnitude.time_series.values(),
            ),
            pattern=term.magnitude.pattern.series,
        )
    )


@_get_term_ir.register
def _(term: DrivingField) -> Tuple[str, ir.DrivingField]:
    return "driving_fields", ir.DrivingField(
        amplitude=ir.PhysicalField(
            sequence=ir.Waveform(
                times=term.amplitude.time_series.times(),
                values=term.amplitude.time_series.values(),
            ),
            pattern="uniform",
        ),
        phase=ir.PhysicalField(
            sequence=ir.Waveform(
                times=term.phase.time_series.times(),
                values=term.phase.time_series.values(),
            ),
            pattern="uniform",
        ),
        detuning=ir.PhysicalField(
            sequence=ir.Waveform(
                times=term.detuning.time_series.times(),
                values=term.detuning.time_series.values(),
            ),
            pattern="uniform",
        ),
    )
