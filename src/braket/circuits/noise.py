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

from typing import Any, Dict, List, Optional, Sequence, Union

from braket.circuits.free_parameter import FreeParameter
from braket.circuits.free_parameter_expression import FreeParameterExpression
from braket.circuits.parameterizable import Parameterizable
from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.qubit_set import QubitSet


class Noise(QuantumOperator):
    """
    Class `Noise` represents a noise channel that operates on one or multiple qubits. Noise
    are considered as building blocks of quantum circuits that simulate noise. It can be
    used as an operator in an `Instruction` object. It appears in the diagram when user prints
    a circuit with `Noise`. This class is considered the noise channel definition containing
    the metadata that defines what the noise channel is and what it does.
    """

    def __init__(self, qubit_count: Optional[int], ascii_symbols: Sequence[str]):
        """
        Args:
            qubit_count (int, optional): Number of qubits this noise channel interacts with.
            ascii_symbols (Sequence[str]): ASCII string symbols for this noise channel. These
                are used when printing a diagram of circuits. Length must be the same as
                `qubit_count`, and index ordering is expected to correlate with target ordering
                on the instruction.

        Raises:
            ValueError: `qubit_count` is less than 1, `ascii_symbols` are None, or
                length of `ascii_symbols` is not equal to `qubit_count`
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    @property
    def name(self) -> str:
        """
        Returns the name of the quantum operator

        Returns:
            The name of the quantum operator as a string
        """
        return self.__class__.__name__

    def to_ir(self, target: QubitSet) -> Any:
        """Returns IR object of quantum operator and target

        Args:
            target (QubitSet): target qubit(s)
        Returns:
            IR object of the quantum operator and target
        """
        raise NotImplementedError("to_ir has not been implemented yet.")

    def to_matrix(self, *args, **kwargs) -> Any:
        """Returns a list of matrices defining the Kraus matrices of the noise channel.

        Returns:
            Iterable[np.ndarray]: list of matrices defining the Kraus matrices of the noise channel.
        """
        raise NotImplementedError("to_matrix has not been implemented yet.")

    def __eq__(self, other):
        if isinstance(other, Noise):
            return self.name == other.name
        return False

    def __repr__(self):
        return f"{self.name}('qubit_count': {self.qubit_count})"

    @classmethod
    def from_dict(cls, noise: dict) -> Noise:
        if "__class__" in noise:
            noise_name = noise["__class__"]
            noise_cls = getattr(cls, noise_name)
            return noise_cls.from_dict(noise)
        raise NotImplementedError

    @classmethod
    def register_noise(cls, noise: Noise):
        """Register a noise implementation by adding it into the Noise class.

        Args:
            noise (Noise): Noise class to register.
        """
        setattr(cls, noise.__name__, noise)


class SingleProbabilisticNoise(Noise, Parameterizable):
    """
    Class `SingleProbabilisticNoise` represents the bit/phase flip noise channel on N qubits
    parameterized by a single probability.
    """

    def __init__(
        self,
        probability: Union[FreeParameterExpression, float],
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
        max_probability: float = 0.5,
    ):
        """
        Args:
            probability (Union[FreeParameterExpression, float]): The probability that the
                noise occurs.
            qubit_count (int, optional): The number of qubits to apply noise.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.
            max_probability (float): Maximum allowed probability of the noise channel. Default: 0.5

        Raises:
            ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, `probability` is not `float` or
                `FreeParameterExpression`, `probability` > 1/2, or `probability` < 0
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

        if not isinstance(probability, FreeParameterExpression):
            _validate_param_value(probability, "probability", max_probability)
        self._probability = probability

    @property
    def probability(self) -> float:
        """
        Returns:
            probability (float): The probability that parametrizes the noise channel.
        """
        return self._probability

    def __repr__(self):
        return f"{self.name}('probability': {self.probability}, 'qubit_count': {self.qubit_count})"

    def __str__(self):
        return f"{self.name}({self.probability})"

    @property
    def parameters(self) -> List[Union[FreeParameterExpression, float]]:
        """
        Returns the parameters associated with the object, either unbound free parameter expressions
        or bound values.

        Returns:
            List[Union[FreeParameterExpression, float]]: The free parameter expressions
            or fixed values associated with the object.
        """
        return [self._probability]

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.name == other.name and self.probability == other.probability
        return False

    def bind_values(self, **kwargs) -> SingleProbabilisticNoise:
        """
        Takes in parameters and attempts to assign them to values.

        Args:
            **kwargs: The parameters that are being assigned.

        Returns:
            SingleProbabilisticNoise: A new Noise object of the same type with the requested
            parameters bound.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def to_dict(self) -> dict:
        """
        Converts this object into a dictionary representation.

        Returns:
            dict: A dictionary object that represents this object. It can be converted back
            into this object using the `from_dict()` method.
        """
        return {
            "__class__": self.__class__.__name__,
            "probability": _parameter_to_dict(self.probability),
            "qubit_count": self.qubit_count,
            "ascii_symbols": self.ascii_symbols,
        }


class SingleProbabilisticNoise_34(SingleProbabilisticNoise):
    """
    Class `SingleProbabilisticNoise` represents the Depolarizing and TwoQubitDephasing noise
    channels parameterized by a single probability.
    """

    def __init__(
        self,
        probability: Union[FreeParameterExpression, float],
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """
        Args:
            probability (Union[FreeParameterExpression, float]): The probability that the
                noise occurs.
            qubit_count (int, optional): The number of qubits to apply noise.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

        Raises:
            ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, `probability` is not `float` or
                `FreeParameterExpression`, `probability` > 3/4, or `probability` < 0
        """
        super().__init__(
            probability=probability,
            qubit_count=qubit_count,
            ascii_symbols=ascii_symbols,
            max_probability=0.75,
        )


class SingleProbabilisticNoise_1516(SingleProbabilisticNoise):
    """
    Class `SingleProbabilisticNoise` represents the TwoQubitDepolarizing noise channel
    parameterized by a single probability.
    """

    def __init__(
        self,
        probability: Union[FreeParameterExpression, float],
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """
        Args:
            probability (Union[FreeParameterExpression, float]): The probability that the
                noise occurs.
            qubit_count (int, optional): The number of qubits to apply noise.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

        Raises:
            ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, `probability` is not `float` or
                `FreeParameterExpression`, `probability` > 15/16, or `probability` < 0
        """
        super().__init__(
            probability=probability,
            qubit_count=qubit_count,
            ascii_symbols=ascii_symbols,
            max_probability=0.9375,
        )


class MultiQubitPauliNoise(Noise, Parameterizable):
    """
    Class `MultiQubitPauliNoise` represents a general multi-qubit Pauli channel,
    parameterized by up to 4**N - 1 probabilities.
    """

    _allowed_substrings = {"I", "X", "Y", "Z"}

    def __init__(
        self,
        probabilities: Dict[str, Union[FreeParameterExpression, float]],
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """[summary]

        Args:
            probabilities (Dict[str, Union[FreeParameterExpression, float]]): A dictionary with
                Pauli strings as keys and the probabilities as values, i.e. {"XX": 0.1. "IZ": 0.2}.
            qubit_count (Optional[int]): The number of qubits the Pauli noise acts on.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

        Raises:
            ValueError: If
                `qubit_count` < 1,
                `ascii_symbols` is `None`,
                `ascii_symbols` length != `qubit_count`,
                `probabilities` are not `float`s or FreeParameterExpressions,
                any of `probabilities` > 1 or `probabilities` < 0,
                the sum of all probabilities is > 1,
                if "II" is specified as a Pauli string,
                if any Pauli string contains invalid strings,
                or if the length of probabilities is greater than 4**qubit_count.
            TypeError: If the type of the dictionary keys are not strings.
                If the probabilities are not floats.
        """

        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)
        self._probabilities = probabilities

        if not probabilities:
            raise ValueError("Pauli dictionary must not be empty.")

        identity = self.qubit_count * "I"
        if identity in probabilities:
            raise ValueError(
                f"{identity} is not allowed as a key. Please enter only non-identity Pauli strings."
            )

        total_prob = 0
        for pauli_string, prob in probabilities.items():
            MultiQubitPauliNoise._validate_pauli_string(
                pauli_string, self.qubit_count, self._allowed_substrings
            )
            if not isinstance(prob, FreeParameterExpression):
                _validate_param_value(prob, f"probability for {pauli_string}")
                total_prob += prob
        if not (1.0 >= total_prob >= 0.0):
            raise ValueError(
                (
                    "Total probability must be a real number in the interval [0, 1]. "
                    f"Total probability was {total_prob}."
                )
            )

    @classmethod
    def _validate_pauli_string(cls, pauli_str, qubit_count, allowed_substrings):
        if not isinstance(pauli_str, str):
            raise TypeError(f"Type of {pauli_str} was not a string.")
        if len(pauli_str) != qubit_count:
            raise ValueError(
                (
                    "Length of each Pauli string must be equal to number of qubits. "
                    f"{pauli_str} had length {len(pauli_str)} instead of length {qubit_count}."
                )
            )
        if not set(pauli_str) <= allowed_substrings:
            raise ValueError(
                (
                    "Strings must be Pauli strings consisting of only [I, X, Y, Z]. "
                    f"Received {pauli_str}."
                )
            )

    def __repr__(self):
        return (
            f"{self.name}('probabilities' : {self._probabilities}, "
            f"'qubit_count': {self.qubit_count})"
        )

    def __str__(self):
        return f"{self.name}({self._probabilities})"

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.name == other.name and self._probabilities == other._probabilities
        return False

    @property
    def probabilities(self) -> Dict[str, float]:
        """
        Dict[str, float]: A map of a Pauli string to its corresponding probability.
        """
        return self._probabilities

    @property
    def parameters(self) -> List[Union[FreeParameterExpression, float]]:
        """
        Returns the parameters associated with the object, either unbound free parameter expressions
        or bound values.

        Parameters are in alphabetical order of the Pauli strings in `probabilities`.

        Returns:
            List[Union[FreeParameterExpression, float]]: The free parameter expressions
            or fixed values associated with the object.
        """
        return [
            self._probabilities[pauli_string] for pauli_string in sorted(self._probabilities.keys())
        ]

    def bind_values(self, **kwargs) -> MultiQubitPauliNoise:
        """
        Takes in parameters and attempts to assign them to values.

        Args:
            **kwargs: The parameters that are being assigned.

        Returns:
            MultiQubitPauliNoise: A new Noise object of the same type with the requested
            parameters bound.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def to_dict(self) -> dict:
        """
        Converts this object into a dictionary representation.

        Returns:
            dict: A dictionary object that represents this object. It can be converted back
            into this object using the `from_dict()` method.
        """
        probabilities = dict()
        for pauli_string, prob in self._probabilities.items():
            probabilities[pauli_string] = _parameter_to_dict(prob)
        return {
            "__class__": self.__class__.__name__,
            "probabilities": probabilities,
            "qubit_count": self.qubit_count,
            "ascii_symbols": self.ascii_symbols,
        }


class PauliNoise(Noise, Parameterizable):
    """
    Class `PauliNoise` represents the a single-qubit Pauli noise channel
    acting on one qubit. It is parameterized by three probabilities.
    """

    def __init__(
        self,
        probX: Union[FreeParameterExpression, float],
        probY: Union[FreeParameterExpression, float],
        probZ: Union[FreeParameterExpression, float],
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """
        Args:
            probX Union[FreeParameterExpression, float]: The X coefficient of the Kraus operators
                in the channel.
            probY Union[FreeParameterExpression, float]: The Y coefficient of the Kraus operators
                in the channel.
            probZ Union[FreeParameterExpression, float]: The Z coefficient of the Kraus operators
                in the channel.
            qubit_count (int, optional): The number of qubits to apply noise.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

        Raises:
            ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, `probX` or `probY` or `probZ`
                is not `float` or FreeParameterExpression, `probX` or `probY` or `probZ` > 1.0, or
                `probX` or `probY` or `probZ` < 0.0, or `probX`+`probY`+`probZ` > 1
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

        total = 0
        total += PauliNoise._get_param_float(probX, "probX")
        total += PauliNoise._get_param_float(probY, "probY")
        total += PauliNoise._get_param_float(probZ, "probZ")
        if total > 1:
            raise ValueError("the sum of probX, probY, probZ cannot be larger than 1")
        self._parameters = [probX, probY, probZ]

    @staticmethod
    def _get_param_float(param: Union[FreeParameterExpression, float], param_name: str) -> float:
        """Validates the value of a probability and returns its value.

        If param is a free parameter expression, this method returns 0.

        Args:
            param (Union[FreeParameterExpression, float]): The probability to validate
            param_name (str): The name of the probability parameter

        Returns:
            float: The value of the parameter, or 0 if it is a free parameter expression
        """
        if isinstance(param, FreeParameterExpression):
            return 0
        else:
            _validate_param_value(param, param_name)
            return float(param)

    @property
    def probX(self) -> Union[FreeParameterExpression, float]:
        """
        Returns:
            Union[FreeParameterExpression, float]: The probability of a Pauli X error.
        """
        return self._parameters[0]

    @property
    def probY(self) -> Union[FreeParameterExpression, float]:
        """
        Returns:
            Union[FreeParameterExpression, float]: The probability of a Pauli Y error.
        """
        return self._parameters[1]

    @property
    def probZ(self) -> Union[FreeParameterExpression, float]:
        """
        Returns:
            Union[FreeParameterExpression, float]: The probability of a Pauli Z error.
        """
        return self._parameters[2]

    def __repr__(self):
        return (
            f"{self.name}("
            f"'probX': {self._parameters[0]}, "
            f"'probY': {self._parameters[1]}, "
            f"'probZ': {self._parameters[2]}, "
            f"'qubit_count': {self.qubit_count}"
            f")"
        )

    def __str__(self):
        return f"{self.name}({self._parameters[0]}, {self._parameters[1]}, {self._parameters[2]})"

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.name == other.name and self._parameters == other._parameters
        return False

    @property
    def parameters(self) -> List[Union[FreeParameterExpression, float]]:
        """
        Returns the parameters associated with the object, either unbound free parameter expressions
        or bound values.

        Parameters are in the order [probX, probY, probZ]

        Returns:
            List[Union[FreeParameterExpression, float]]: The free parameter expressions
            or fixed values associated with the object.
        """
        return self._parameters

    def bind_values(self, **kwargs) -> PauliNoise:
        """
        Takes in parameters and attempts to assign them to values.

        Args:
            **kwargs: The parameters that are being assigned.

        Returns:
            PauliNoise: A new Noise object of the same type with the requested
            parameters bound.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def to_dict(self) -> dict:
        """
        Converts this object into a dictionary representation.

        Returns:
            dict: A dictionary object that represents this object. It can be converted back
            into this object using the `from_dict()` method.
        """
        return {
            "__class__": self.__class__.__name__,
            "probX": _parameter_to_dict(self.probX),
            "probY": _parameter_to_dict(self.probY),
            "probZ": _parameter_to_dict(self.probZ),
            "qubit_count": self.qubit_count,
            "ascii_symbols": self.ascii_symbols,
        }


class DampingNoise(Noise, Parameterizable):
    """
    Class `DampingNoise` represents a damping noise channel
    on N qubits parameterized by gamma.
    """

    def __init__(
        self,
        gamma: Union[FreeParameterExpression, float],
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """
        Args:
            gamma (Union[FreeParameterExpression, float]): Probability of damping.
            qubit_count (int, optional): The number of qubits to apply noise.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

            Raises:
                ValueError: If
                    `qubit_count` < 1,
                    `ascii_symbols` is `None`,
                    `len(ascii_symbols)` != `qubit_count`,
                    `gamma` is not `float` or `FreeParameterExpression`,
                    or `gamma` > 1.0 or `gamma` < 0.0.
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

        if not isinstance(gamma, FreeParameterExpression):
            _validate_param_value(gamma, "gamma")
        self._gamma = gamma

    @property
    def gamma(self) -> float:
        """
        Returns:
            gamma (float): Probability of damping.
        """
        return self._gamma

    def __repr__(self):
        return f"{self.name}('gamma': {self.gamma}, 'qubit_count': {self.qubit_count})"

    def __str__(self):
        return f"{self.name}({self.gamma})"

    @property
    def parameters(self) -> List[Union[FreeParameterExpression, float]]:
        """
        Returns the parameters associated with the object, either unbound free parameter expressions
        or bound values.

        Returns:
            List[Union[FreeParameterExpression, float]]: The free parameter expressions
            or fixed values associated with the object.
        """
        return [self._gamma]

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.name == other.name and self.gamma == other.gamma
        return False

    def bind_values(self, **kwargs) -> DampingNoise:
        """
        Takes in parameters and attempts to assign them to values.

        Args:
            **kwargs: The parameters that are being assigned.

        Returns:
            DampingNoise: A new Noise object of the same type with the requested
            parameters bound.

        Raises:
            NotImplementedError: Subclasses should implement this function.
        """
        raise NotImplementedError

    def to_dict(self) -> dict:
        """
        Converts this object into a dictionary representation.

        Returns:
            dict: A dictionary object that represents this object. It can be converted back
            into this object using the `from_dict()` method.
        """
        return {
            "__class__": self.__class__.__name__,
            "gamma": _parameter_to_dict(self.gamma),
            "qubit_count": self.qubit_count,
            "ascii_symbols": self.ascii_symbols,
        }


class GeneralizedAmplitudeDampingNoise(DampingNoise):
    """
    Class `GeneralizedAmplitudeDampingNoise` represents the generalized amplitude damping
    noise channel on N qubits parameterized by gamma and probability.
    """

    def __init__(
        self,
        gamma: Union[FreeParameterExpression, float],
        probability: Union[FreeParameterExpression, float],
        qubit_count: Optional[int],
        ascii_symbols: Sequence[str],
    ):
        """
        Args:
            gamma (Union[FreeParameterExpression, float]): Probability of damping.
            probability (Union[FreeParameterExpression, float]): Probability of the system being
                excited by the environment.
            qubit_count (int): The number of qubits to apply noise.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

            Raises:
                ValueError: If
                    `qubit_count` < 1,
                    `ascii_symbols` is `None`,
                    `len(ascii_symbols)` != `qubit_count`,
                    `probability` or `gamma` is not `float` or `FreeParameterExpression`,
                    `probability` > 1.0 or `probability` < 0.0,
                    or `gamma` > 1.0 or `gamma` < 0.0.
        """
        super().__init__(gamma=gamma, qubit_count=qubit_count, ascii_symbols=ascii_symbols)

        if not isinstance(probability, FreeParameterExpression):
            _validate_param_value(probability, "probability")
        self._probability = probability

    @property
    def probability(self) -> float:
        """
        Returns:
            probability (float): Probability of the system being excited by the environment.
        """
        return self._probability

    def __repr__(self):
        return (
            f"{self.name}('gamma': {self.gamma}, "
            f"'probability': {self.probability}, "
            f"'qubit_count': {self.qubit_count})"
        )

    def __str__(self):
        return f"{self.name}({self.gamma}, {self.probability})"

    @property
    def parameters(self) -> List[Union[FreeParameterExpression, float]]:
        """
        Returns the parameters associated with the object, either unbound free parameter expressions
        or bound values.

        Parameters are in the order [gamma, probability]

        Returns:
            List[Union[FreeParameterExpression, float]]: The free parameter expressions
            or fixed values associated with the object.
        """
        return [self.gamma, self.probability]

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return (
                self.name == other.name
                and self.gamma == other.gamma
                and self.probability == other.probability
            )
        return False

    def to_dict(self) -> dict:
        """
        Converts this object into a dictionary representation.

        Returns:
            dict: A dictionary object that represents this object. It can be converted back
            into this object using the `from_dict()` method.
        """
        return {
            "__class__": self.__class__.__name__,
            "gamma": _parameter_to_dict(self.gamma),
            "probability": _parameter_to_dict(self.probability),
            "qubit_count": self.qubit_count,
            "ascii_symbols": self.ascii_symbols,
        }


def _validate_param_value(
    parameter: Union[FreeParameterExpression, float], param_name: str, maximum: float = 1.0
) -> None:
    """Validates the value of a given parameter.

    Args:
        parameter (Union[FreeParameterExpression, float]): The parameter to validate
        param_name (str): The name of the parameter
        maximum (float): The maximum value of the parameter. Default: 1.0
    """
    if not isinstance(parameter, float):
        raise TypeError(f"{param_name} must be float type")
    if not (maximum >= parameter >= 0.0):
        raise ValueError(f"{param_name} must be a real number in the interval [0, {maximum}]")


def _parameter_to_dict(parameter: Union[FreeParameter, float]) -> Union[dict, float]:
    """Converts a parameter to a dictionary if it's a FreeParameter, otherwise returns the float.

    Args:
        parameter(Union[FreeParameter, float]): The parameter to convert.

    Returns:
        A dictionary representation of a FreeParameter if the parameter is a FreeParameter,
        otherwise returns the float.
    """
    if isinstance(parameter, FreeParameter):
        return parameter.to_dict()
    return parameter
