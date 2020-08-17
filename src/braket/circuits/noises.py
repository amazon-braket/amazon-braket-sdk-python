from typing import Iterable

import braket.ir.jaqcd as ir
import numpy as np
from braket.circuits import circuit
from braket.circuits.instruction import Instruction
from braket.circuits.quantum_operator_helpers import (
    is_CPTP,
    verify_quantum_operator_matrix_dimensions,
)
from braket.circuits.qubit_set import QubitSet, QubitSetInput
from braket.circuits.noise import Noise, ProbabilityNoise


"""
To add a new noise:
    1. Implement the class and extend `Noise`
    2. Add a method with the `@circuit.subroutine(register=True)` decorator. Method name
       will be added into the `Circuit` class. This method is the default way
       clients add this noise to a circuit.
    3. Register the class with the `Noise` class via `Noise.register_noise()`.
"""


class Bit_Flip(ProbabilityNoise):
    """Bit flip noise channel."""

    def __init__(self, prob: float):
        super().__init__(prob=prob,
                         qubit_count=1,
                         ascii_symbols=["NB({:.2g})".format(prob)],
        )

    def to_ir(self, target: QubitSet):
        return ir.Bit_Flip.construct(target=target[0], prob=self.prob)

    def to_matrix(self) -> Iterable[np.ndarray]:
        K0 = np.sqrt(1-self.prob) * np.array([[1.0, 0.0], [0.0, 1.0]], dtype=complex)
        K1 = np.sqrt(self.prob)   * np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
        return [K0, K1]

    @staticmethod
    @circuit.subroutine(register=True)
    def bit_flip(target: QubitSetInput, prob: float) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            prob (float): Probability of bit flipping.

        Returns:
            Iterable[Instruction]: `Iterable` of Bit_Flip instructions.

        Examples:
            >>> circ = Circuit().bit_flip(0, prob=0.1)
        """
        return [Instruction(Noise.Bit_Flip(prob=prob), target=qubit) for qubit in QubitSet(target)]

Noise.register_noise(Bit_Flip)


class Phase_Flip(ProbabilityNoise):
    """Phase flip noise channel."""

    def __init__(self, prob: float):
        super().__init__(prob=prob,
                         qubit_count=1,
                         ascii_symbols=["NP({:.2g})".format(prob)],
        )

    def to_ir(self, target: QubitSet):
        return ir.Phase_Flip.construct(target=target[0], prob=self.prob)

    def to_matrix(self) -> Iterable[np.ndarray]:
        K0 = np.sqrt(1-self.prob) * np.array([[1.0, 0.0], [0.0, 1.0]], dtype=complex)
        K1 = np.sqrt(self.prob)   * np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
        return [K0, K1]

    @staticmethod
    @circuit.subroutine(register=True)
    def phase_flip(target: QubitSetInput, prob: float) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            prob (float): Probability of phase flipping.

        Returns:
            Iterable[Instruction]: `Iterable` of Phase_Flip instructions.

        Examples:
            >>> circ = Circuit().phase_flip(0, prob=0.1)
        """
        return [Instruction(Noise.Phase_Flip(prob=prob), target=qubit) for qubit in QubitSet(target)]

Noise.register_noise(Phase_Flip)


class Depolarizing(ProbabilityNoise):
    """Depolarizing noise channel."""

    def __init__(self, prob: float):
        super().__init__(prob=prob,
                         qubit_count=1,
                         ascii_symbols=["ND({:.2g})".format(prob)],
        )

    def to_ir(self, target: QubitSet):
        return ir.Depolarizing.construct(target=target[0], prob=self.prob)

    def to_matrix(self) -> Iterable[np.ndarray]:
        K0 = np.sqrt(1-self.prob)      * np.array([[1.0, 0.0], [0.0, 1.0]], dtype=complex)
        K1 = np.sqrt(self.prob/3)      * np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
        K2 = np.sqrt(self.prob/3) * 1j * np.array([[0.0, -1.0], [1.0, 0.0]], dtype=complex)
        K3 = np.sqrt(self.prob/3)      * np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
        return [K0, K1, K2, K3]

    @staticmethod
    @circuit.subroutine(register=True)
    def depolarizing(target: QubitSetInput, prob: float) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            prob (float): Probability of depolarizing.

        Returns:
            Iterable[Instruction]: `Iterable` of Depolarizing instructions.

        Examples:
            >>> circ = Circuit().depolarizing(0, prob=0.1)
        """
        return [Instruction(Noise.Depolarizing(prob=prob), target=qubit) for qubit in QubitSet(target)]

Noise.register_noise(Depolarizing)


class Amplitude_Damping(ProbabilityNoise):
    """Phase flip noise channel."""

    def __init__(self, prob: float):
        super().__init__(prob=prob,
                         qubit_count=1,
                         ascii_symbols=["NA({:.2g})".format(prob)],
        )

    def to_ir(self, target: QubitSet):
        return ir.Amplitude_Damping.construct(target=target[0], prob=self.prob)

    def to_matrix(self) -> Iterable[np.ndarray]:
        K0 = np.array([[1.0, 0.0], [0.0, np.sqrt(1-self.prob)]], dtype=complex)
        K1 = np.array([[0.0, np.sqrt(self.prob)], [0.0, 0.0]],   dtype=complex)
        return [K0, K1]

    @staticmethod
    @circuit.subroutine(register=True)
    def amplitude_damping(target: QubitSetInput, prob: float) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            prob (float): Probability of amplitude damping.

        Returns:
            Iterable[Instruction]: `Iterable` of Amplitude_Damping instructions.

        Examples:
            >>> circ = Circuit().amplitude_damping(0, prob=0.1)
        """
        return [Instruction(Noise.Amplitude_Damping(prob=prob), target=qubit) for qubit in QubitSet(target)]

Noise.register_noise(Amplitude_Damping)


class Kraus(Noise):
    """User-defined noise channel

    Args:
        matrices (Iterable[np.array]): A list of matrices that define a noise
            channel. These matrices need to satisify the requirement of CPTP map.
        display_name (str): Name to be used for an instance of this general noise
            channel for circuit diagrams. Defaults to `NK`.

    Raises:
        ValueError: If any matrix in `matrices` is not a two-dimensional square
            matrix,
            or has a dimension length which is not a positive exponent of 2,
            or the `matrices` do not satisify CPTP condition.
    """
    def __init__(self, matrices: Iterable[np.ndarray], display_name: str = "NK"):
        for matrix in matrices:
            verify_quantum_operator_matrix_dimensions(matrix)
        self._matrices = [np.array(matrix, dtype=complex) for matrix in matrices]
        qubit_count = int(np.log2(self._matrices[0].shape[0]))

        if not is_CPTP(self._matrices):
            raise ValueError("The input matrices do not define a completely-positive trace-preserving map.")

        super().__init__(qubit_count=qubit_count, ascii_symbols=[display_name] * qubit_count)

    def to_matrix(self) -> Iterable[np.ndarray]:
        return self._matrices

    def to_ir(self, target: QubitSet):
        return ir.Kraus.construct(
            targets=[qubit for qubit in target],
            matrices=Kraus._transform_matrix_to_ir(self._matrices),
        )

    @staticmethod
    def _transform_matrix_to_ir(matrices: Iterable[np.ndarray]):
        serializable = []
        for matrix in matrices:
            matrix_as_list  = [[[element.real, element.imag] for element in row] for row in matrix.tolist()]
            serializable.append(matrix_as_list)
        return serializable

    @staticmethod
    @circuit.subroutine(register=True)
    def kraus(targets: QubitSetInput, matrices: Iterable[np.array], display_name: str = "NK") -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            targets (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            matrices (Iterable[np.array]): Matrices that define a general noise channel.

        Returns:
            Iterable[Instruction]: `Iterable` of Kraus instructions.

        Examples:
            >>> circ = Circuit().kraus(0, matrices=matrices)
        """
        return Instruction(Noise.Kraus(matrices=matrices, display_name=display_name), target=targets)

Noise.register_noise(Kraus)
