from typing import Any, Sequence

from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.qubit_set import QubitSet


class CompositeOperator(QuantumOperator):
    """
    Class `CompositeOperator` represents a composition of quantum operators operating on N qubits.
    This class contains the metadata for defining what a composite operator is and what it does.
    """

    def __init__(self, qubit_count: int, ascii_symbols: Sequence[str]):
        """
        Args:
            qubit_count (int): Number of qubits this composite operator interacts with.
            ascii_symbols (str): ASCII string symbols for the composite operator. These are used
                when printing a diagram of circuits.

        Raises:
            ValueError: `qubit_count` is less than 1, `ascii_symbols` are `None`, or
                `ascii_symbols` length != 1
        """
        if len(ascii_symbols) != 1:
            msg = f"ascii_symbols, {ascii_symbols}, length must 1"
            raise ValueError(msg)

        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    def to_ir(self, *args, **kwargs) -> Any:
        """Returns IR representation of quantum operator

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        raise NotImplementedError("to_ir has not been implemented yet.")

    def decompose(self, target: QubitSet):
        """
        Decomposes by one level and returns the composite operator's corresponding iterable
        of instructions.

        Args:
            target (QubitSet): target qubit(s)
        """
        return []

    def __eq__(self, other):
        if isinstance(other, CompositeOperator):
            return self.name == other.name
        return NotImplemented

    def __repr__(self):
        return f"{self.name}('qubit_count': {self.qubit_count})"

    @classmethod
    def register_composite_operator(cls, composite_operator: "CompositeOperator"):
        """Register a composite operator implementation by adding it into the CompositeOperator class.

        Args:
            composite_operator (CompositeOperator): CompositeOperator class to register.
        """
        setattr(cls, composite_operator.__name__, composite_operator)
