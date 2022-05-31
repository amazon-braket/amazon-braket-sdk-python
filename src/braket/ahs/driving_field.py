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

from typing import List, Union

from braket.ahs.field import Field
from braket.ahs.hamiltonian import Hamiltonian
from braket.ahs.time_series import TimeSeries


class DrivingField(Hamiltonian):
    def __init__(
        self,
        amplitude: Union[Field, TimeSeries],
        phase: Union[Field, TimeSeries],
        detuning: Union[Field, TimeSeries],
    ) -> None:
        """Creates Hamiltonian Term for the Driving Field that coherently transfer atoms
        from the ground state to the Rydberg state in an AnalogHamiltonianSimulation.

        formula: ((Omega(t) / 2) * exp(1j * phi(t)) * Sum_k |g_k><r_k| + h.c.) - Delta(t) * Sum_k |r_k><r_k|  # noqa
        states:
          |g_k> : ground state of atom k.
          |r_k> : Rydberg state of atom k.
        other symbols:
          Sum_k : summation over all target atoms.
          h.c.  : Hermitian conjugate of the preceeding term.

        Args:
            amplitude (Union[Field, TimeSeries]): global amplitude (Omega(t).
                Time is in us, and value is in rad/us.
            amplitude (Union[Field, TimeSeries]): global phase (phi(t)).
                Time is in us, and value is in rad/us.
            amplitude (Union[Field, TimeSeries]): global detuning (Delta(t)).
                Time is in us, and value is in rad/us.
        """
        super().__init__()
        self._amplitude = amplitude if isinstance(amplitude, Field) else Field(amplitude)
        self._phase = phase if isinstance(phase, Field) else Field(phase)
        self._detuning = detuning if isinstance(detuning, Field) else Field(detuning)

    @property
    def terms(self) -> List[Hamiltonian]:
        return [self]

    @property
    def amplitude(self) -> Field:
        return self._amplitude

    @property
    def phase(self) -> Field:
        return self._phase

    @property
    def detuning(self) -> Field:
        return self._detuning
