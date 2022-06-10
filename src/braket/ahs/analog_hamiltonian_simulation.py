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

import braket.ir.ahs as ir
from braket.ahs.atom_arrangement import AtomArrangement, SiteType
from braket.ahs.driving_field import DrivingField
from braket.ahs.hamiltonian import Hamiltonian
from braket.ahs.shifting_field import ShiftingField


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
            setup=ir.Setup(atom_array=self._register_to_ir()), hamiltonian=self._hamiltonian_to_ir()
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
            driving_fields=terms["driving_fields"], shifting_fields=terms["shifting_fields"]
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
