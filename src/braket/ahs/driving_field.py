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

from braket.ahs.discretization_types import DiscretizationProperties
from braket.ahs.field import Field
from braket.ahs.hamiltonian import Hamiltonian
from braket.timings.time_series import StitchBoundaryCondition, TimeSeries


class DrivingField(Hamiltonian):
    def __init__(
        self,
        amplitude: Field | TimeSeries,
        phase: Field | TimeSeries,
        detuning: Field | TimeSeries,
    ) -> None:
        r"""Creates a Hamiltonian term :math:`H_{drive}` for the driving field
        that coherently transfers atoms from the ground state to the Rydberg state
        in an AnalogHamiltonianSimulation, defined by the formula

        .. math::
            H_{drive} (t) := \frac{\Omega(t)}{2} e^{i \phi(t)} \left(
                \sum_k |g_k \rangle \langle r_k| + |r_k \rangle \langle g_k|
            \right) - \Delta(t) \sum_k{| r_k \rangle \langle r_k |}

        where

            :math:`\Omega(t)` is the global Rabi frequency in rad/s,

            :math:`\phi(t)` is the global phase in rad/s,

            :math:`\Delta(t)` is the global detuning in rad/s,

            :math:`|g_k \rangle` is the ground state of atom :math:`k`,

            :math:`|r_k \rangle` is the Rydberg state of atom :math:`k`.

        with the sum :math:`\sum_k` taken over all target atoms.

        Args:
            amplitude (Union[Field, TimeSeries]): global amplitude (:math:`\Omega(t)`).
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
    def terms(self) -> list[Hamiltonian]:
        return [self]

    @property
    def amplitude(self) -> Field:
        r"""Field: The global amplitude (:math:`\Omega(t)`). Time is in s, and value is in rad/s."""
        return self._amplitude

    @property
    def phase(self) -> Field:
        r"""Field: The global phase (:math:`\phi(t)`). Time is in s, and value is in rad/s."""
        return self._phase

    @property
    def detuning(self) -> Field:
        r"""Field: global detuning (:math:`\Delta(t)`). Time is in s, and value is in rad/s."""
        return self._detuning

    def stitch(
        self, other: DrivingField, boundary: StitchBoundaryCondition = StitchBoundaryCondition.MEAN
    ) -> DrivingField:
        """Stitches two driving fields based on TimeSeries.stitch method.
        The time points of the second DrivingField are shifted such that the first time point of
        the second DrifingField coincides with the last time point of the first DrivingField.
        The boundary point value is handled according to StitchBoundaryCondition argument value.

        Args:
            other (DrivingField): The second shifting field to be stitched with.
            boundary (StitchBoundaryCondition): {"mean", "left", "right"}. Boundary point handler.

                Possible options are
              - "mean" - take the average of the boundary value points of the first
                and the second time series.
              - "left" - use the last value from the left time series as the boundary point.
              - "right" - use the first value from the right time series as the boundary point.

        Returns:
            DrivingField: The stitched DrivingField object.
        """
        amplitude = self.amplitude.time_series.stitch(other.amplitude.time_series, boundary)
        detuning = self.detuning.time_series.stitch(other.detuning.time_series, boundary)
        phase = self.phase.time_series.stitch(other.phase.time_series, boundary)

        return DrivingField(amplitude=amplitude, detuning=detuning, phase=phase)

    def discretize(self, properties: DiscretizationProperties) -> DrivingField:
        """Creates a discretized version of the Hamiltonian.

        Args:
            properties (DiscretizationProperties): Capabilities of a device that represent the
                resolution with which the device can implement the parameters.

        Returns:
            DrivingField: A new discretized DrivingField.
        """
        driving_parameters = properties.rydberg.rydbergGlobal
        time_resolution = driving_parameters.timeResolution

        amplitude_value_resolution = driving_parameters.rabiFrequencyResolution
        discretized_amplitude = self.amplitude.discretize(
            time_resolution=time_resolution,
            value_resolution=amplitude_value_resolution,
        )

        phase_value_resolution = driving_parameters.phaseResolution
        discretized_phase = self.phase.discretize(
            time_resolution=time_resolution,
            value_resolution=phase_value_resolution,
        )

        detuning_value_resolution = driving_parameters.detuningResolution
        discretized_detuning = self.detuning.discretize(
            time_resolution=time_resolution,
            value_resolution=detuning_value_resolution,
        )
        return DrivingField(
            amplitude=discretized_amplitude, phase=discretized_phase, detuning=discretized_detuning
        )

    @staticmethod
    def from_lists(
        times: list[float], amplitudes: list[float], detunings: list[float], phases: list[float]
    ) -> DrivingField:
        """Builds DrivingField Hamiltonian from lists defining time evolution
        of Hamiltonian parameters (Rabi frequency, detuning, phase).
        The values of the parameters at each time points are global for all atoms.

        Args:
            times (list[float]): The time points of the driving field
            amplitudes (list[float]): The values of the amplitude
            detunings (list[float]): The values of the detuning
            phases (list[float]): The values of the phase

        Raises:
            ValueError: If any of the input args length is different from the rest.

        Returns:
            DrivingField: DrivingField Hamiltonian.
        """
        if not (len(times) == len(amplitudes) == len(detunings) == len(phases)):
            raise ValueError(
                f"The lengths of the lists for times({len(times)}), amplitudes({len(amplitudes)}),\
                detunings({len(detunings)}) and phases({len(phases)}) are not equal"
            )

        amplitude = TimeSeries()
        detuning = TimeSeries()
        phase = TimeSeries()

        for t, amplitude_value, detuning_value, phase_value in zip(
            times, amplitudes, detunings, phases
        ):
            amplitude.put(t, amplitude_value)
            detuning.put(t, detuning_value)
            phase.put(t, phase_value)

        return DrivingField(amplitude=amplitude, detuning=detuning, phase=phase)
