from typing import Any, Sequence

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

    def __init__(
        self,
        qubit_count: int,
        ascii_symbols: Sequence[str],
    ):
        """
        Args:
            qubit_count (int): Number of qubits this noise channel interacts with.
            ascii_symbols (Sequence[str]): ASCII string symbols for this noise channel. These
                are used when printing a diagram of circuits. Length must be the same as
                `qubit_count`, and index ordering is expected to correlate with target ordering
                on the instruction.

        Raises:
            ValueError: `qubit_count` is less than 1, `ascii_symbols` are None, or
                length of `ascii_symbols` is not equal to `qubit_count`
        """
        if qubit_count < 1:
            raise ValueError(f"qubit_count, {qubit_count}, must be greater than zero")
        self._qubit_count = qubit_count

        if ascii_symbols is None:
            raise ValueError("ascii_symbols must not be None")

        if len(ascii_symbols) != qubit_count:
            msg = f"ascii_symbols, {ascii_symbols}, length must equal qubit_count, {qubit_count}"
            raise ValueError(msg)
        self._ascii_symbols = tuple(ascii_symbols)

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
        return NotImplemented

    def __repr__(self):
        return f"{self.name}('qubit_count': {self.qubit_count})"

    @classmethod
    def register_noise(cls, noise: "Noise"):
        """Register a noise implementation by adding it into the Noise class.

        Args:
            noise (Noise): Noise class to register.
        """
        setattr(cls, noise.__name__, noise)


class SingleProbabilisticNoise(Noise):
    """
    Class `SingleProbabilisticNoise` represents a noise channel on N qubits parameterized by
    a single probability.
    """

    def __init__(self, probability: float, qubit_count: int, ascii_symbols: Sequence[str]):
        """
        Args:
            probability (float): The probability that the noise occurs.
            qubit_count (int): The number of qubits to apply noise.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

        Raises:
            ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, `probability` is not `float`,
                `probability` > 1.0, or `probability` < 0.0
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

        if not isinstance(probability, float):
            raise ValueError("probability must be float type")
        if not (probability <= 1.0 and probability >= 0.0):
            raise ValueError("probability must be a real number in the interval [0,1]")
        self._probability = probability

    @property
    def probability(self) -> float:
        """
        Returns:
            probability (float): The probability that parameterizes the Kraus matrices.
        """
        return self._probability

    def __repr__(self):
        return f"{self.name}('probability': {self.probability}, 'qubit_count': {self.qubit_count})"


class GeneralPauliNoise(Noise):
    """
    Class `GeneralPauliNoise` represents the general Pauli noise channel on N qubits
    parameterized by three probabilities.
    """

    def __init__(
        self,
        probX: float,
        probY: float,
        probZ: float,
        qubit_count: int,
        ascii_symbols: Sequence[str],
    ):
        """
        Args:
            probX [float], probY [float], probZ [float]: The coefficients of the Kraus operators
            in the channel.
            qubit_count (int): The number of qubits to apply noise.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

        Raises:
            ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, `probX` or `probY` or `probZ`
                is not `float`, `probX` or `probY` or `probZ` > 1.0, or
                `probX` or `probY` or `probZ` < 0.0, or `probX`+`probY`+`probZ` > 0
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

        if not isinstance(probX, float):
            raise ValueError("probX must be float type")
        if not (probX <= 1.0 and probX >= 0.0):
            raise ValueError("probX must be a real number in the interval [0,1]")
        if not isinstance(probY, float):
            raise ValueError("probY must be float type")
        if not (probY <= 1.0 and probY >= 0.0):
            raise ValueError("probY must be a real number in the interval [0,1]")
        if not isinstance(probZ, float):
            raise ValueError("probZ must be float type")
        if not (probZ <= 1.0 and probZ >= 0.0):
            raise ValueError("probZ must be a real number in the interval [0,1]")
        if probX + probY + probZ > 1:
            raise ValueError("the sum of probX, probY, probZ cannot be larger than 1")

        self._probX = probX
        self._probY = probY
        self._probZ = probZ

    @property
    def probX(self) -> float:
        """
        Returns:
            probX (float): The probability that parameterizes the Kraus matrices.
        """
        return self._probX

    @property
    def probY(self) -> float:
        """
        Returns:
            probY (float): The probability that parameterizes the Kraus matrices.
        """
        return self._probY

    @property
    def probZ(self) -> float:
        """
        Returns:
            probZ (float): The probability that parameterizes the Kraus matrices.
        """
        return self._probZ

    def __repr__(self):
        return f"{self.name}('probX': {self.probX}, 'probY': {self.probY}, \
'probZ': {self.probZ}, 'qubit_count': {self.qubit_count})"


class DampingNoise(Noise):
    """
    Class `DampingNoise` represents a damping noise channel
    on N qubits parameterized by gamma.
    """

    def __init__(self, gamma: float, qubit_count: int, ascii_symbols: Sequence[str]):
        """
        Args:
            gamma (float): Probability of damping.
            qubit_count (int): The number of qubits to apply noise.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

            Raises:
                ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, `gamma` is not `float`,
                `gamma` > 1.0, or `gamma` < 0.0.
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

        if not isinstance(gamma, float):
            raise ValueError("gamma must be float type")
        if not (gamma <= 1.0 and gamma >= 0.0):
            raise ValueError("gamma must be a real number in the interval [0,1]")
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


class GeneralizedAmplitudeDampingNoise(DampingNoise):
    """
    Class `GeneralizedAmplitudeDampingNoise` represents the generalized amplitude damping
    noise channel on N qubits parameterized by gamma and probability.
    """

    def __init__(
        self, probability: float, gamma: float, qubit_count: int, ascii_symbols: Sequence[str]
    ):
        """
        Args:
            probability (float): Probability of the system being excited by the environment.
            gamma (float): Probability of damping.
            qubit_count (int): The number of qubits to apply noise.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

            Raises:
                ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, `probability` or `gamma` is not `float`,
                `probability` > 1.0, or `probability` < 0.0, `gamma` > 1.0, or `gamma` < 0.0.
        """
        super().__init__(gamma=gamma, qubit_count=qubit_count, ascii_symbols=ascii_symbols)

        if not isinstance(probability, float):
            raise ValueError("probability must be float type")
        if not (probability <= 1.0 and probability >= 0.0):
            raise ValueError("probability must be a real number in the interval [0,1]")
        self._probability = probability

    @property
    def probability(self) -> float:
        """
        Returns:
            probability (float): Probability of the system being excited by the environment.
        """
        return self._probability

    def __repr__(self):
        return f"{self.name}('probability': {self.probability}, 'gamma': {self.gamma}, \
'qubit_count': {self.qubit_count})"
