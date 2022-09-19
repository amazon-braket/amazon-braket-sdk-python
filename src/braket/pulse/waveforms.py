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

from abc import ABC, abstractmethod
from typing import List, Optional

from oqpy import WaveformVar, bool_, complex128, declare_waveform_generator, duration, float64
from oqpy.base import OQPyExpression, make_identifier_name


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

    def __init__(self, amplitudes: List[complex], name: Optional[str] = None):
        """
        Args:
            amplitudes (List[complex]): Array of complex values specifying the
                waveform amplitude at each timestep. The timestep is determined by the sampling rate
                of the frame to which waveform is applied to.
            name (Optional[str]): The name used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.amplitudes = amplitudes
        self.name = name or make_identifier_name()

    def to_oqpy_expression(self) -> OQPyExpression:
        return WaveformVar(init_expression=self.amplitudes, ident=self.name)


class ConstantWaveform(Waveform):
    """A constant waveform which holds the supplied `iq` value as its amplitude for the
    specified length."""

    def __init__(self, length: float, iq: complex, name: Optional[str] = None):
        """
        Args:
            length (float): Value (in seconds) specifying the duration of the waveform.
            iq (complex): complex value specifying the amplitude of the waveform.
            name (Optional[str]): The name used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.length = length
        self.iq = iq
        self.name = name or make_identifier_name()

    def to_oqpy_expression(self) -> OQPyExpression:
        constant_generator = declare_waveform_generator(
            "constant", [("length", duration), ("iq", complex128)]
        )
        return WaveformVar(
            init_expression=constant_generator(self.length, self.iq), ident=self.name
        )


class DragGaussianWaveform(Waveform):
    """A gaussian waveform with an additional gaussian derivative component and lifting applied."""

    def __init__(
        self,
        length: float,
        sigma: float,
        beta: float,
        amplitude: float = 1,
        zero_at_edges: bool = True,
        name: Optional[str] = None,
    ):
        """
        Args:
            length (float): Value (in seconds) specifying the duration of the waveform.
            sigma (float): A measure of how wide or narrow the Gaussian peak is.
            beta (float): The correction amplitude.
            amplitude (float): The amplitude of the waveform envelope. Defaults to 1.
            zero_at_edges (bool): bool specifying whether the waveform amplitude is clipped to
                zero at the edges. Defaults to True.
            name (Optional[str]): The name used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.length = length
        self.sigma = sigma
        self.beta = beta
        self.amplitude = amplitude
        self.zero_at_edges = zero_at_edges
        self.name = name or make_identifier_name()

    def to_oqpy_expression(self) -> OQPyExpression:
        drag_gaussian_generator = declare_waveform_generator(
            "drag_gaussian",
            [
                ("length", duration),
                ("sigma", float64),
                ("beta", float64),
                ("amplitude", float64),
                ("zero_at_edges", bool_),
            ],
        )
        return WaveformVar(
            init_expression=drag_gaussian_generator(
                self.length, self.sigma, self.beta, self.amplitude, self.zero_at_edges
            ),
            ident=self.name,
        )


class GaussianWaveform(Waveform):
    """A waveform with amplitudes following a gaussian distribution for the specified parameters."""

    def __init__(
        self,
        length: float,
        sigma: float,
        amplitude: float = 1,
        zero_at_edges: bool = True,
        name: Optional[str] = None,
    ):
        """
        Args:
            length (float): Value (in seconds) specifying the duration of the waveform.
            sigma (float): A measure of how wide or narrow the Gaussian peak is.
            amplitude (float): The amplitude of the waveform envelope. Defaults to 1.
            zero_at_edges (bool): bool specifying whether the waveform amplitude is clipped to
                zero at the edges. Defaults to True.
            name (Optional[str]): The name used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.length = length
        self.sigma = sigma
        self.amplitude = amplitude
        self.zero_at_edges = zero_at_edges
        self.name = name or make_identifier_name()

    def to_oqpy_expression(self) -> OQPyExpression:
        gaussian_generator = declare_waveform_generator(
            "gaussian",
            [
                ("length", duration),
                ("sigma", float64),
                ("amplitude", float64),
                ("zero_at_edges", bool_),
            ],
        )
        return WaveformVar(
            init_expression=gaussian_generator(
                self.length, self.sigma, self.amplitude, self.zero_at_edges
            ),
            ident=self.name,
        )
