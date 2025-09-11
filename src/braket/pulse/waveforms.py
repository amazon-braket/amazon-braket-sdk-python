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

import random
import string
from abc import ABC, abstractmethod

import numpy as np
import scipy as sp
from oqpy import WaveformVar, bool_, complex128, declare_waveform_generator, duration, float64
from oqpy.base import OQPyExpression

from braket.parametric.free_parameter import FreeParameter
from braket.parametric.free_parameter_expression import (
    FreeParameterExpression,
    subs_if_free_parameter,
)
from braket.parametric.parameterizable import Parameterizable


class Waveform(ABC):
    """A waveform is a time-dependent envelope that can be used to emit signals on an output port
    or receive signals from an input port. As such, when transmitting signals to the qubit, a
    frame determines time at which the waveform envelope is emitted, its carrier frequency, and
    it's phase offset. When capturing signals from a qubit, at minimum a frame determines the
    time at which the signal is captured. See https://openqasm.com/language/openpulse.html#waveforms
    for more details.
    """

    @abstractmethod
    def _to_oqpy_expression(self) -> OQPyExpression:
        """Returns an OQPyExpression defining this waveform."""

    @abstractmethod
    def sample(self, dt: float) -> np.ndarray:
        """Generates a sample of amplitudes for this Waveform based on the given time resolution.

        Args:
            dt (float): The time resolution.

        Returns:
            np.ndarray: The sample amplitudes for this waveform.
        """

    @staticmethod
    @abstractmethod
    def _from_calibration_schema(waveform_json: dict) -> Waveform:
        """Parses a JSON input and returns the BDK waveform. See https://github.com/aws/amazon-braket-schemas-python/blob/main/src/braket/device_schema/pulse/native_gate_calibrations_v1.py#L104

        Args:
            waveform_json (dict): A JSON object with the needed parameters for making the Waveform.

        Returns:
            Waveform: A Waveform object parsed from the supplied JSON.
        """


class ArbitraryWaveform(Waveform):
    """An arbitrary waveform with amplitudes at each timestep explicitly specified using
    an array.
    """

    def __init__(self, amplitudes: list[complex], id: str | None = None):
        """Initializes an `ArbitraryWaveform`.

        Args:
            amplitudes (list[complex]): Array of complex values specifying the
                waveform amplitude at each timestep. The timestep is determined by the sampling rate
                of the frame to which waveform is applied to.
            id (Optional[str]): The identifier used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.amplitudes = list(amplitudes)
        self.id = id or _make_identifier_name()

    def __repr__(self) -> str:
        return f"ArbitraryWaveform('id': {self.id}, 'amplitudes': {self.amplitudes})"

    def __eq__(self, other: ArbitraryWaveform):
        return isinstance(other, ArbitraryWaveform) and (self.amplitudes, self.id) == (
            other.amplitudes,
            other.id,
        )

    def _to_oqpy_expression(self) -> OQPyExpression:
        """Returns an OQPyExpression defining this waveform.

        Returns:
            OQPyExpression: The OQPyExpression.
        """
        return WaveformVar(init_expression=self.amplitudes, name=self.id)

    def sample(self, dt: float) -> np.ndarray:
        """Generates a sample of amplitudes for this Waveform based on the given time resolution.

        Args:
            dt (float): The time resolution.

        Raises:
            NotImplementedError: This class does not implement sample.

        Returns:
            np.ndarray: The sample amplitudes for this waveform.
        """
        raise NotImplementedError

    @staticmethod
    def _from_calibration_schema(waveform_json: dict) -> ArbitraryWaveform:
        wave_id = waveform_json["waveformId"]
        complex_amplitudes = [complex(i[0], i[1]) for i in waveform_json["amplitudes"]]
        return ArbitraryWaveform(complex_amplitudes, wave_id)


class ConstantWaveform(Waveform, Parameterizable):
    """A constant waveform which holds the supplied `iq` value as its amplitude for the
    specified length.
    """

    def __init__(self, length: float | FreeParameterExpression, iq: complex, id: str | None = None):
        """Initializes a `ConstantWaveform`.

        Args:
            length (Union[float, FreeParameterExpression]): Value (in seconds)
                specifying the duration of the waveform.
            iq (complex): complex value specifying the amplitude of the waveform.
            id (Optional[str]): The identifier used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.length = length
        self.iq = iq
        self.id = id or _make_identifier_name()

    def __repr__(self) -> str:
        return f"ConstantWaveform('id': {self.id}, 'length': {self.length}, 'iq': {self.iq})"

    @property
    def parameters(self) -> list[FreeParameterExpression | FreeParameter | float]:
        """Returns the parameters associated with the object, either unbound free parameter
        expressions or bound values.

        Returns:
            list[Union[FreeParameterExpression, FreeParameter, float]]: a list of parameters.
        """
        return [self.length]

    def bind_values(self, **kwargs: FreeParameter | str) -> ConstantWaveform:
        """Takes in parameters and returns an object with specified parameters
        replaced with their values.

        Args:
            **kwargs (Union[FreeParameter, str]): Arbitrary keyword arguments.

        Returns:
            ConstantWaveform: A copy of this waveform with the requested parameters bound.
        """
        constructor_kwargs = {
            "length": subs_if_free_parameter(self.length, **kwargs),
            "iq": self.iq,
            "id": self.id,
        }
        return ConstantWaveform(**constructor_kwargs)

    def __eq__(self, other: ConstantWaveform):
        return isinstance(other, ConstantWaveform) and (self.length, self.iq, self.id) == (
            other.length,
            other.iq,
            other.id,
        )

    def _to_oqpy_expression(self) -> OQPyExpression:
        """Returns an OQPyExpression defining this waveform.

        Returns:
            OQPyExpression: The OQPyExpression.
        """
        constant_generator = declare_waveform_generator(
            "constant", [("length", duration), ("iq", complex128)]
        )
        return WaveformVar(
            init_expression=constant_generator(self.length, self.iq),
            name=self.id,
        )

    def sample(self, dt: float) -> np.ndarray:
        """Generates a sample of amplitudes for this Waveform based on the given time resolution.

        Args:
            dt (float): The time resolution.

        Returns:
            np.ndarray: The sample amplitudes for this waveform.
        """
        # Amplitudes should be gated by [0:self.length]
        sample_range = np.arange(0, self.length, dt)
        return self.iq * np.ones_like(sample_range)

    @staticmethod
    def _from_calibration_schema(waveform_json: dict) -> ConstantWaveform:
        wave_id = waveform_json["waveformId"]
        length = iq = None
        for val in waveform_json["arguments"]:
            if val["name"] == "length":
                length = (
                    float(val["value"])
                    if val["type"] == "float"
                    else FreeParameterExpression(val["value"])
                )
            if val["name"] == "iq":
                iq = (
                    complex(val["value"])
                    if val["type"] == "complex"
                    else FreeParameterExpression(val["value"])
                )
        return ConstantWaveform(length=length, iq=iq, id=wave_id)


class DragGaussianWaveform(Waveform, Parameterizable):
    """A gaussian waveform with an additional gaussian derivative component and lifting applied."""

    def __init__(
        self,
        length: float | FreeParameterExpression,
        sigma: float | FreeParameterExpression,
        beta: float | FreeParameterExpression,
        amplitude: float | FreeParameterExpression = 1,
        zero_at_edges: bool = False,
        id: str | None = None,
    ):
        """Initializes a `DragGaussianWaveform`.

        Args:
            length (Union[float, FreeParameterExpression]): Value (in seconds)
                specifying the duration of the waveform.
            sigma (Union[float, FreeParameterExpression]): A measure (in seconds) of
                how wide or narrow the Gaussian peak is.
            beta (Union[float, FreeParameterExpression]): The correction amplitude.
            amplitude (Union[float, FreeParameterExpression]): The amplitude of the
                waveform envelope. Defaults to 1.
            zero_at_edges (bool): bool specifying whether the waveform amplitude is clipped to
                zero at the edges. Defaults to False.
            id (Optional[str]): The identifier used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.length = length
        self.sigma = sigma
        self.beta = beta
        self.amplitude = amplitude
        self.zero_at_edges = zero_at_edges
        self.id = id or _make_identifier_name()

    def __repr__(self) -> str:
        return (
            f"DragGaussianWaveform('id': {self.id}, 'length': {self.length}, "
            f"'sigma': {self.sigma}, 'beta': {self.beta}, 'amplitude': {self.amplitude}, "
            f"'zero_at_edges': {self.zero_at_edges})"
        )

    @property
    def parameters(self) -> list[FreeParameterExpression | FreeParameter | float]:
        """Returns the parameters associated with the object, either unbound free parameter
        expressions or bound values.
        """
        return [self.length, self.sigma, self.beta, self.amplitude]

    def bind_values(self, **kwargs: FreeParameter | str) -> DragGaussianWaveform:
        """Takes in parameters and returns an object with specified parameters
        replaced with their values.

        Args:
            **kwargs (Union[FreeParameter, str]): Arbitrary keyword arguments.

        Returns:
            DragGaussianWaveform: A copy of this waveform with the requested parameters bound.
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

    def __eq__(self, other: DragGaussianWaveform):
        return isinstance(other, DragGaussianWaveform) and (
            self.length,
            self.sigma,
            self.beta,
            self.amplitude,
            self.zero_at_edges,
            self.id,
        ) == (other.length, other.sigma, other.beta, other.amplitude, other.zero_at_edges, other.id)

    def _to_oqpy_expression(self) -> OQPyExpression:
        """Returns an OQPyExpression defining this waveform.

        Returns:
            OQPyExpression: The OQPyExpression.
        """
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
                self.length,
                self.sigma,
                self.beta,
                self.amplitude,
                self.zero_at_edges,
            ),
            name=self.id,
        )

    def sample(self, dt: float) -> np.ndarray:
        """Generates a sample of amplitudes for this Waveform based on the given time resolution.

        Args:
            dt (float): The time resolution.

        Returns:
            np.ndarray: The sample amplitudes for this waveform.
        """
        sample_range = np.arange(0, self.length, dt)
        t0 = self.length / 2
        zero_at_edges_int = int(self.zero_at_edges)
        return (
            (1 - (1.0j * self.beta * ((sample_range - t0) / self.sigma**2)))
            * (
                self.amplitude
                / (1 - zero_at_edges_int * np.exp(-0.5 * ((self.length / (2 * self.sigma)) ** 2)))
            )
            * (
                np.exp(-0.5 * (((sample_range - t0) / self.sigma) ** 2))
                - zero_at_edges_int * np.exp(-0.5 * ((self.length / (2 * self.sigma)) ** 2))
            )
        )

    @staticmethod
    def _from_calibration_schema(waveform_json: dict) -> DragGaussianWaveform:
        waveform_parameters = {"id": waveform_json["waveformId"]}
        for val in waveform_json["arguments"]:
            waveform_parameters[val["name"]] = (
                float(val["value"])
                if val["type"] == "float"
                else FreeParameterExpression(val["value"])
            )
        return DragGaussianWaveform(**waveform_parameters)


class GaussianWaveform(Waveform, Parameterizable):
    """A waveform with amplitudes following a gaussian distribution for the specified parameters."""

    def __init__(
        self,
        length: float | FreeParameterExpression,
        sigma: float | FreeParameterExpression,
        amplitude: float | FreeParameterExpression = 1,
        zero_at_edges: bool = False,
        id: str | None = None,
    ):
        """Initializes a `GaussianWaveform`.

        Args:
            length (Union[float, FreeParameterExpression]): Value (in seconds) specifying the
                duration of the waveform.
            sigma (Union[float, FreeParameterExpression]): A measure (in seconds) of how wide
                or narrow the Gaussian peak is.
            amplitude (Union[float, FreeParameterExpression]): The amplitude of the waveform
                envelope. Defaults to 1.
            zero_at_edges (bool): bool specifying whether the waveform amplitude is clipped to
                zero at the edges. Defaults to False.
            id (Optional[str]): The identifier used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.length = length
        self.sigma = sigma
        self.amplitude = amplitude
        self.zero_at_edges = zero_at_edges
        self.id = id or _make_identifier_name()

    def __repr__(self) -> str:
        return (
            f"GaussianWaveform('id': {self.id}, 'length': {self.length}, 'sigma': {self.sigma}, "
            f"'amplitude': {self.amplitude}, 'zero_at_edges': {self.zero_at_edges})"
        )

    @property
    def parameters(self) -> list[FreeParameterExpression | FreeParameter | float]:
        """Returns the parameters associated with the object, either unbound free parameter
        expressions or bound values.
        """
        return [self.length, self.sigma, self.amplitude]

    def bind_values(self, **kwargs: FreeParameter | str) -> GaussianWaveform:
        """Takes in parameters and returns an object with specified parameters
        replaced with their values.

        Args:
            **kwargs (Union[FreeParameter, str]): Arbitrary keyword arguments.

        Returns:
            GaussianWaveform: A copy of this waveform with the requested parameters bound.
        """
        constructor_kwargs = {
            "length": subs_if_free_parameter(self.length, **kwargs),
            "sigma": subs_if_free_parameter(self.sigma, **kwargs),
            "amplitude": subs_if_free_parameter(self.amplitude, **kwargs),
            "zero_at_edges": self.zero_at_edges,
            "id": self.id,
        }
        return GaussianWaveform(**constructor_kwargs)

    def __eq__(self, other: GaussianWaveform):
        return isinstance(other, GaussianWaveform) and (
            self.length,
            self.sigma,
            self.amplitude,
            self.zero_at_edges,
            self.id,
        ) == (other.length, other.sigma, other.amplitude, other.zero_at_edges, other.id)

    def _to_oqpy_expression(self) -> OQPyExpression:
        """Returns an OQPyExpression defining this waveform.

        Returns:
            OQPyExpression: The OQPyExpression.
        """
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
                self.length,
                self.sigma,
                self.amplitude,
                self.zero_at_edges,
            ),
            name=self.id,
        )

    def sample(self, dt: float) -> np.ndarray:
        """Generates a sample of amplitudes for this Waveform based on the given time resolution.

        Args:
            dt (float): The time resolution.

        Returns:
            np.ndarray: The sample amplitudes for this waveform.
        """
        sample_range = np.arange(0, self.length, dt)
        t0 = self.length / 2
        zero_at_edges_int = int(self.zero_at_edges)
        return (
            self.amplitude
            / (1 - zero_at_edges_int * np.exp(-0.5 * ((self.length / (2 * self.sigma)) ** 2)))
        ) * (
            np.exp(-0.5 * (((sample_range - t0) / self.sigma) ** 2))
            - zero_at_edges_int * np.exp(-0.5 * ((self.length / (2 * self.sigma)) ** 2))
        )

    @staticmethod
    def _from_calibration_schema(waveform_json: dict) -> GaussianWaveform:
        waveform_parameters = {"id": waveform_json["waveformId"]}
        for val in waveform_json["arguments"]:
            waveform_parameters[val["name"]] = (
                float(val["value"])
                if val["type"] == "float"
                else FreeParameterExpression(val["value"])
            )
        return GaussianWaveform(**waveform_parameters)


class ErfSquareWaveform(Waveform, Parameterizable):
    """A square waveform with smoothed edges."""

    def __init__(
        self,
        length: float | FreeParameterExpression,
        width: float | FreeParameterExpression,
        sigma: float | FreeParameterExpression,
        off_center: float | FreeParameterExpression = 0,
        amplitude: float | FreeParameterExpression = 1,
        zero_at_edges: bool = False,
        id: str | None = None,
    ):
        r"""Initializes a `ErfSquareWaveform`.

        .. math:: (\text{step}((t-t_1)/sigma) + \text{step}(-(t-t_2)/sigma) - 1)

        where :math:`\text{step}(t)` is the rounded step function defined as
        :math:`(erf(t)+1)/2` and :math:`t_1` and :math:`t_2` are the timestamps at the half
        height. The waveform is scaled such that its maximum is equal to `amplitude`.

        Args:
            length (float | FreeParameterExpression): Duration (in seconds) from the start
                to the end of the waveform.
            width (float | FreeParameterExpression): Duration (in seconds) between the
                half height of the two edges.
            sigma (float | FreeParameterExpression): A characteristic time of how quickly
                the edges rise and fall.
            off_center (float | FreeParameterExpression): Shift the smoothed square waveform
                earlier or later in time. When positive, the smoothed square is shifted later
                (to the right), otherwise earlier (to the left). Defaults to 0.
            amplitude (float | FreeParameterExpression): The amplitude of the waveform
                envelope. Defaults to 1.
            zero_at_edges (bool): Whether the waveform is scaled such that it has zero value at the
                edges. Defaults to False.
            id (str | None): The identifier used for declaring this waveform. A random string of
                ascii characters is assigned by default.
        """
        self.length = length
        self.width = width
        self.sigma = sigma
        self.off_center = off_center
        self.amplitude = amplitude
        self.zero_at_edges = zero_at_edges
        self.id = id or _make_identifier_name()

    def __repr__(self) -> str:
        return (
            f"ErfSquareWaveform('id': {self.id}, 'length': {self.length}, "
            f"'width': {self.width}, 'sigma': {self.sigma}, 'off_center': {self.off_center}, "
            f"'amplitude': {self.amplitude}, 'zero_at_edges': {self.zero_at_edges})"
        )

    @property
    def parameters(self) -> list[FreeParameterExpression | FreeParameter | float]:
        """Returns the parameters associated with the object, either unbound free parameter
        expressions or bound values.
        """
        return [self.length, self.width, self.sigma, self.off_center, self.amplitude]

    def bind_values(self, **kwargs: FreeParameter | str) -> ErfSquareWaveform:
        """Takes in parameters and returns an object with specified parameters
        replaced with their values.

        Args:
            **kwargs (FreeParameter | str): Arbitrary keyword arguments.

        Returns:
            ErfSquareWaveform: A copy of this waveform with the requested parameters bound.
        """
        constructor_kwargs = {
            "length": subs_if_free_parameter(self.length, **kwargs),
            "width": subs_if_free_parameter(self.width, **kwargs),
            "sigma": subs_if_free_parameter(self.sigma, **kwargs),
            "off_center": subs_if_free_parameter(self.off_center, **kwargs),
            "amplitude": subs_if_free_parameter(self.amplitude, **kwargs),
            "zero_at_edges": self.zero_at_edges,
            "id": self.id,
        }
        return ErfSquareWaveform(**constructor_kwargs)

    def __eq__(self, other: ErfSquareWaveform):
        return isinstance(other, ErfSquareWaveform) and (
            self.length,
            self.width,
            self.sigma,
            self.off_center,
            self.amplitude,
            self.zero_at_edges,
            self.id,
        ) == (
            other.length,
            other.width,
            other.sigma,
            other.off_center,
            other.amplitude,
            other.zero_at_edges,
            other.id,
        )

    def _to_oqpy_expression(self) -> OQPyExpression:
        """Returns an OQPyExpression defining this waveform.

        Returns:
            OQPyExpression: The OQPyExpression.
        """
        erf_square_generator = declare_waveform_generator(
            "erf_square",
            [
                ("length", duration),
                ("width", duration),
                ("sigma", duration),
                ("off_center", duration),
                ("amplitude", float64),
                ("zero_at_edges", bool_),
            ],
        )
        return WaveformVar(
            init_expression=erf_square_generator(
                self.length,
                self.width,
                self.sigma,
                self.off_center,
                self.amplitude,
                self.zero_at_edges,
            ),
            name=self.id,
        )

    def sample(self, dt: float) -> np.ndarray:
        """Generates a sample of amplitudes for this Waveform based on the given time resolution.

        Args:
            dt (float): The time resolution.

        Returns:
            np.ndarray: The sample amplitudes for this waveform.
        """
        sample_range = np.arange(0, self.length, dt)
        t1 = (self.length - self.width) / 2 + self.off_center
        t2 = (self.length + self.width) / 2 + self.off_center
        samples = (
            sp.special.erf((sample_range - t1) / self.sigma)
            + sp.special.erf(-(sample_range - t2) / self.sigma)
        ) / 2

        mid_waveform_height = sp.special.erf((self.width / 2) / self.sigma)
        waveform_bottom = (sp.special.erf(-t1 / self.sigma) + sp.special.erf(t2 / self.sigma)) / 2

        if self.zero_at_edges:
            return (
                (samples - waveform_bottom)
                / (mid_waveform_height - waveform_bottom)
                * self.amplitude
            )
        return samples * self.amplitude / mid_waveform_height

    @staticmethod
    def _from_calibration_schema(waveform_json: dict) -> ErfSquareWaveform:
        waveform_parameters = {"id": waveform_json["waveformId"]}
        for val in waveform_json["arguments"]:
            waveform_parameters[val["name"]] = (
                float(val["value"])
                if val["type"] == "float"
                else FreeParameterExpression(val["value"])
            )
        return ErfSquareWaveform(**waveform_parameters)


def _make_identifier_name() -> str:
    return "".join([random.choice(string.ascii_letters) for _ in range(10)])  # noqa: S311


def _parse_waveform_from_calibration_schema(waveform: dict) -> Waveform:
    waveform_names = {
        "arbitrary": ArbitraryWaveform._from_calibration_schema,
        "drag_gaussian": DragGaussianWaveform._from_calibration_schema,
        "gaussian": GaussianWaveform._from_calibration_schema,
        "constant": ConstantWaveform._from_calibration_schema,
        "erf_square": ErfSquareWaveform._from_calibration_schema,
    }
    if "amplitudes" in waveform:
        waveform["name"] = "arbitrary"
    if waveform["name"] in waveform_names:
        return waveform_names[waveform["name"]](waveform)
    waveform_id = waveform["waveformId"]
    raise ValueError(f"The waveform {waveform_id} of cannot be constructed")
