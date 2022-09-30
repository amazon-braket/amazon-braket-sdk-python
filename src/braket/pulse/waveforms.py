# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from abc import ABC, abstractmethod
from typing import List, Optional, Union

import sympy
from oqpy import WaveformVar, bool_, complex128, declare_waveform_generator, duration, float64
from oqpy.base import OQDurationLiteral, OQPyExpression, make_identifier_name

from braket.circuits.free_parameter import FreeParameter
from braket.circuits.free_parameter_expression import (
    FreeParameterExpression,
    FreeParameterExpressionIdentifier,
    subs_if_free_parameter,
)
from braket.circuits.parameterizable import Parameterizable


class Waveform(ABC):
    """
    A waveform is a time-dependent envelope that can be used to emit signals on an output port
    or receive signals from an input port. As such, when transmitting signals to the qubit, a
    frame determines time at which the waveform envelope is emitted, its carrier frequency, and
    it’s phase offset. When capturing signals from a qubit, at minimum a frame determines the
    time at which the signal is captured. See https://openqasm.com/language/openpulse.html#waveforms
    for more details.
    """

    @abstractmethod
    # TODO: Make this private once oqpy changes are done.
    def to_oqpy_expression(self) -> OQPyExpression:
        """Returns an OQPyExpression defining this waveform."""


class ArbitraryWaveform(Waveform):
    """An arbitrary waveform with amplitudes at each timestep explicitly specified using
    an array."""

    def __init__(self, amplitudes: List[complex], id: Optional[str] = None):
        """
        Args:
            amplitudes (List[complex]): Array of complex values specifying the
                waveform amplitude at each timestep. The timestep is determined by the sampling rate
                of the frame to which waveform is applied to.
            id (Optional[str]): The identifier used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.amplitudes = amplitudes
        self.id = id or make_identifier_name()

    def __eq__(self, other):
        return isinstance(other, ArbitraryWaveform) and (self.amplitudes, self.id) == (
            other.amplitudes,
            other.id,
        )

    def to_oqpy_expression(self) -> OQPyExpression:
        return WaveformVar(init_expression=self.amplitudes, ident=self.id)


class ConstantWaveform(Waveform, Parameterizable):
    """A constant waveform which holds the supplied `iq` value as its amplitude for the
    specified length."""

    def __init__(
        self, length: Union[float, FreeParameterExpression], iq: complex, id: Optional[str] = None
    ):
        """
        Args:
            length (Union[float, FreeParameterExpression]): Value (in seconds)
                specifying the duration of the waveform.
            iq (complex): complex value specifying the amplitude of the waveform.
            id (Optional[str]): The identifier used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.length = length
        self.iq = iq
        self.id = id or make_identifier_name()

    @property
    def parameters(self) -> List[Union[FreeParameterExpression, FreeParameter, float]]:
        """Returns the parameters associated with the object, either unbound free parameter
        expressions or bound values."""
        return [self.length]

    def bind_values(self, **kwargs) -> ConstantWaveform:
        """Takes in parameters and returns an object with specified parameters
        replaced with their values.

        Returns:
            ConstantWaveform: A copy of this waveform with the requested parameters bound.
        """
        constructor_kwargs = {
            "length": subs_if_free_parameter(self.length, **kwargs),
            "iq": self.iq,
            "id": self.id,
        }
        return ConstantWaveform(**constructor_kwargs)

    def __eq__(self, other):
        return isinstance(other, ConstantWaveform) and (self.length, self.iq, self.id) == (
            other.length,
            other.iq,
            other.id,
        )

    def to_oqpy_expression(self) -> OQPyExpression:
        constant_generator = declare_waveform_generator(
            "constant", [("length", duration), ("iq", complex128)]
        )
        return WaveformVar(
            init_expression=constant_generator(_map_to_oqpy_type(self.length, True), self.iq),
            ident=self.id,
        )


class DragGaussianWaveform(Waveform, Parameterizable):
    """A gaussian waveform with an additional gaussian derivative component and lifting applied."""

    def __init__(
        self,
        length: Union[float, FreeParameterExpression],
        sigma: Union[float, FreeParameterExpression],
        beta: Union[float, FreeParameterExpression],
        amplitude: Union[float, FreeParameterExpression] = 1,
        zero_at_edges: bool = True,
        id: Optional[str] = None,
    ):
        """
        Args:
            length (Union[float, FreeParameterExpression]): Value (in seconds)
                specifying the duration of the waveform.
            sigma (Union[float, FreeParameterExpression]): A measure (in seconds) of
                how wide or narrow the Gaussian peak is.
            beta (Union[float, FreeParameterExpression]): The correction amplitude.
            amplitude (Union[float, FreeParameterExpression]): The amplitude of the
                waveform envelope. Defaults to 1.
            zero_at_edges (bool): bool specifying whether the waveform amplitude is clipped to
                zero at the edges. Defaults to True.
            id (Optional[str]): The identifier used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.length = length
        self.sigma = sigma
        self.beta = beta
        self.amplitude = amplitude
        self.zero_at_edges = zero_at_edges
        self.id = id or make_identifier_name()

    @property
    def parameters(self) -> List[Union[FreeParameterExpression, FreeParameter, float]]:
        """Returns the parameters associated with the object, either unbound free parameter
        expressions or bound values."""
        return [self.length, self.sigma, self.beta, self.amplitude]

    def bind_values(self, **kwargs) -> DragGaussianWaveform:
        """Takes in parameters and returns an object with specified parameters
        replaced with their values.

        Returns:
            ConstantWaveform: A copy of this waveform with the requested parameters bound.
        """
        constructor_kwargs = {
            "length": subs_if_free_parameter(self.length, **kwargs),
            "sigma": subs_if_free_parameter(self.sigma, **kwargs),
            "beta": subs_if_free_parameter(self.beta, **kwargs),
            "amplitude": subs_if_free_parameter(self.amplitude, **kwargs),
            "zero_at_edges": self.zero_at_edges,
            "id": self.id,
        }
        return DragGaussianWaveform(**constructor_kwargs)

    def __eq__(self, other):
        return isinstance(other, DragGaussianWaveform) and (
            self.length,
            self.sigma,
            self.beta,
            self.amplitude,
            self.zero_at_edges,
            self.id,
        ) == (other.length, other.sigma, other.beta, other.amplitude, other.zero_at_edges, other.id)

    def to_oqpy_expression(self) -> OQPyExpression:
        drag_gaussian_generator = declare_waveform_generator(
            "drag_gaussian",
            [
                ("length", duration),
                ("sigma", duration),
                ("beta", float64),
                ("amplitude", float64),
                ("zero_at_edges", bool_),
            ],
        )
        return WaveformVar(
            init_expression=drag_gaussian_generator(
                _map_to_oqpy_type(self.length, True),
                _map_to_oqpy_type(self.sigma, True),
                _map_to_oqpy_type(self.beta),
                _map_to_oqpy_type(self.amplitude),
                self.zero_at_edges,
            ),
            ident=self.id,
        )


class GaussianWaveform(Waveform, Parameterizable):
    """A waveform with amplitudes following a gaussian distribution for the specified parameters."""

    def __init__(
        self,
        length: Union[float, FreeParameterExpression],
        sigma: Union[float, FreeParameterExpression],
        amplitude: Union[float, FreeParameterExpression] = 1,
        zero_at_edges: bool = True,
        id: Optional[str] = None,
    ):
        """
        Args:
            length (Union[float, FreeParameterExpression]): Value (in seconds) specifying the
                duration of the waveform.
            sigma (Union[float, FreeParameterExpression]): A measure (in seconds) of how wide
                or narrow the Gaussian peak is.
            amplitude (Union[float, FreeParameterExpression]): The amplitude of the waveform
                envelope. Defaults to 1.
            zero_at_edges (bool): bool specifying whether the waveform amplitude is clipped to
                zero at the edges. Defaults to True.
            id (Optional[str]): The identifier used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.length = length
        self.sigma = sigma
        self.amplitude = amplitude
        self.zero_at_edges = zero_at_edges
        self.id = id or make_identifier_name()

    @property
    def parameters(self) -> List[Union[FreeParameterExpression, FreeParameter, float]]:
        """Returns the parameters associated with the object, either unbound free parameter
        expressions or bound values."""
        return [self.length, self.sigma, self.amplitude]

    def bind_values(self, **kwargs) -> GaussianWaveform:
        """Takes in parameters and returns an object with specified parameters
        replaced with their values.

        Returns:
            ConstantWaveform: A copy of this waveform with the requested parameters bound.
        """
        constructor_kwargs = {
            "length": subs_if_free_parameter(self.length, **kwargs),
            "sigma": subs_if_free_parameter(self.sigma, **kwargs),
            "amplitude": subs_if_free_parameter(self.amplitude, **kwargs),
            "zero_at_edges": self.zero_at_edges,
            "id": self.id,
        }
        return GaussianWaveform(**constructor_kwargs)

    def __eq__(self, other):
        return isinstance(other, GaussianWaveform) and (
            self.length,
            self.sigma,
            self.amplitude,
            self.zero_at_edges,
            self.id,
        ) == (other.length, other.sigma, other.amplitude, other.zero_at_edges, other.id)

    def to_oqpy_expression(self) -> OQPyExpression:
        gaussian_generator = declare_waveform_generator(
            "gaussian",
            [
                ("length", duration),
                ("sigma", duration),
                ("amplitude", float64),
                ("zero_at_edges", bool_),
            ],
        )
        return WaveformVar(
            init_expression=gaussian_generator(
                _map_to_oqpy_type(self.length, True),
                _map_to_oqpy_type(self.sigma, True),
                _map_to_oqpy_type(self.amplitude),
                self.zero_at_edges,
            ),
            ident=self.id,
        )


# TODO: Reconcile handling of FreeParameterExpressionIdentifier and OQDurationLiteral in oqpy
def _map_to_oqpy_type(
    parameter: Union[FreeParameterExpression, float], is_duration_type: bool = False
) -> Union[FreeParameterExpressionIdentifier, OQPyExpression]:
    if isinstance(parameter, sympy.core.numbers.Float):
        return float(parameter)
    if isinstance(parameter, FreeParameterExpression):
        return (
            OQDurationLiteral(parameter)
            if is_duration_type
            else FreeParameterExpressionIdentifier(parameter)
        )
    return parameter
