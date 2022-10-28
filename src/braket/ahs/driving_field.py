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

from braket.ahs.discretization_types import DiscretizationProperties
from braket.ahs.field import Field
from braket.ahs.hamiltonian import Hamiltonian
from braket.timings.time_series import TimeSeries


class DrivingField(Hamiltonian):
    def __init__(
        self,
        amplitude: Union[Field, TimeSeries],
        phase: Union[Field, TimeSeries],
        detuning: Union[Field, TimeSeries],
    ) -> None:
        r"""Creates a Hamiltonian term :math:`H_{drive}` for the driving field
        that coherently transfers atoms from the ground state to the Rydberg state
        in an AnalogHamiltonianSimulation, defined by the formula

        .. math::
            H_{drive} (t) := \frac{\Omega(t)}{2} e^{i \phi(t)} \left(
                \sum_k |g_k \rangle \langle r_k| + |r_k \rangle \langle g_k|
            \right) - \Delta(t) \sum_k{| r_k \rangle \langle r_k |}

        where

            :math:`|g_k \rangle` is the ground state of atom k.

            :math:`|r_k \rangle` is the Rydberg state of atom k.

        and the sum :math:`\sum_k` is taken over all target atoms.

        Args:
            amplitude (Union[Field, TimeSeries]): global amplitude (:math:`\Omega(t)`.
                Time is in s, and value is in rad/s.
            phase (Union[Field, TimeSeries]): global phase (:math:`\phi(t)`).
                Time is in s, and value is in rad/s.
            detuning (Union[Field, TimeSeries]): global detuning (:math:`\Delta(t)`).
                Time is in s, and value is in rad/s.
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
        r"""Field: The global amplitude (:math:`\Omega(t)`). Time is in s, and value is in rad/s."""
        return self._amplitude

    @property
    def phase(self) -> Field:
        r"""Field: The global phase (:math:`\pmega(t)`). Time is in s, and value is in rad/s."""
        return self._phase

    @property
    def detuning(self) -> Field:
        r"""Field: global detuning (:math:`\Delta(t)`). Time is in s, and value is in rad/s."""
        return self._detuning

    def discretize(self, properties: DiscretizationProperties) -> DrivingField:
        """Creates a discretized version of the Hamiltonian.

        Args:
            properties (DiscretizationProperties): Discretization properties of a device.

        Returns:
            DrivingField: A new discretized DrivingField.
        """
        driving_parameters = properties.rydberg.rydbergGlobal
        time_resolution = driving_parameters.timeResolution
        discretized_amplitude = self.amplitude.discretize(
            time_resolution=time_resolution,
            value_resolution=driving_parameters.rabiFrequencyResolution,
        )
        discretized_phase = self.phase.discretize(
            time_resolution=time_resolution,
            value_resolution=driving_parameters.phaseResolution,
        )
        discretized_detuning = self.detuning.discretize(
            time_resolution=time_resolution,
            value_resolution=driving_parameters.detuningResolution,
        )
        return DrivingField(
            amplitude=discretized_amplitude, phase=discretized_phase, detuning=discretized_detuning
        )
