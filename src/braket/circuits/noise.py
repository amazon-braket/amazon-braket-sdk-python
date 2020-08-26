from typing import Any, Sequence

from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.qubit_set import QubitSet


class Noise(QuantumOperator):
    """
    Class `Noise` represents a noise channel that operates on one or multiple qubits. Noise
    are considered as building blocks of quantum circuits that simulate noise. It can be
    used as an operator in an Instruction object. It appears in the diagram when user prints
    a circuit with Noise. This class is considered the noise channel definition containing
    the metadata that defines what a noise channel is and what it does.
    """

    def __init__(
        self, qubit_count: int, ascii_symbols: Sequence[str],
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
                `ascii_symbols` length != `qubit_count`
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
        """Returns a list of matrices defining the Kraus matrices of
                the noise channel.

            Returns:
                Iterable[np.ndarray]: list of matrices defining the Kraus
                    matrices of the noise channel.
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


class ProbabilisticNoise(Noise):
    """
    Class `ProbabilisticNoise` represents a noise channel on N qubits parameterized by
    a probability.
    """

    def __init__(self, probability: float, qubit_count: int, ascii_symbols: Sequence[str]):
        """
        Args:
            probability (float): The probability of noise, a parameter that generates Kraus
                matrices.
            qubit_count (int): The number of qubits that this noise interacts with.
            ascii_symbols (Sequence[str]): ASCII string symbols for the noise. These are used when
                printing a diagram of a circuit. The length must be the same as `qubit_count`, and
                index ordering is expected to correlate with the target ordering on the instruction.

        Raises:
            ValueError: If the `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != `qubit_count`, `probability` is not `float`,
                `probability`>1.0, or `probability`<0.0
        """
        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

        if not isinstance(probability, float):
            raise ValueError("probability must be float type")
        if not (probability <= 1.0 and probability >= 0.0):
            raise ValueError("probability must be a real number in the interval [0,1]")
        self._probability = probability

    @property
    def probability(self) -> float:
        """ Returns the probability parameter for the noise.

        Returns:
            probability (float): The probability that parameterizes the Kraus matrices.
        """
        return self._probability

    def __repr__(self):
        return f"{self.name}('probability': {self.probability}, 'qubit_count': {self.qubit_count})"
