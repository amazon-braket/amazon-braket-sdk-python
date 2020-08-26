from typing import Iterable

import numpy as np

import braket.ir.jaqcd as ir
from braket.circuits import circuit
from braket.circuits.instruction import Instruction
from braket.circuits.noise import Noise, ProbabilisticNoise
from braket.circuits.quantum_operator_helpers import (
    is_CPTP,
    verify_quantum_operator_matrix_dimensions,
)
from braket.circuits.qubit_set import QubitSet, QubitSetInput

"""
To add a new Noise implementation:
    1. Implement the class and extend `Noise`
    2. Add a method with the `@circuit.subroutine(register=True)` decorator. Method name
       will be added into the `Circuit` class. This method is the default way clients add
       this noise to a circuit.
    3. Register the class with the `Noise` class via `Noise.register_noise()`.
"""


class BitFlip(ProbabilisticNoise):
    """Bit flip noise channel which transforms a density matrix D according to:

    .. math:: D \\Rightarrow (1-p) D + p X D X^{\\dagger}
    where
    ::
        I  =  [1.  0.]
              [0.  1.]

        X  =  [0.  1.]
              [1.  0.]

        p = probability

    This noise channel is shown as `NBF` in circuit diagrams.
    """

    def __init__(self, probability: float):
        super().__init__(
            probability=probability,
            qubit_count=1,
            ascii_symbols=["NBF({:.2g})".format(probability)],
        )

    def to_ir(self, target: QubitSet):
        return ir.BitFlip.construct(target=target[0], probability=self.probability)

    def to_matrix(self) -> Iterable[np.ndarray]:
        K0 = np.sqrt(1 - self.probability) * np.eye(2, dtype=complex)
        K1 = np.sqrt(self.probability) * np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
        return [K0, K1]

    @staticmethod
    @circuit.subroutine(register=True)
    def bit_flip(target: QubitSetInput, probability: float) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            probability (float): Probability of bit flipping.

        Returns:
            Iterable[Instruction]: `Iterable` of BitFlip instructions.

        Examples:
            >>> circ = Circuit().bit_flip(0, probability=0.1)
        """
        return [
            Instruction(Noise.BitFlip(probability=probability), target=qubit)
            for qubit in QubitSet(target)
        ]


Noise.register_noise(BitFlip)


class PhaseFlip(ProbabilisticNoise):
    """Phase flip noise channel which transforms a density matrix D according to:

    .. math:: D \\Rightarrow (1-p) D + p Z D Z^{\\dagger}
    where
    ::
        I  =  [1.  0.]
              [0.  1.]

        Z  =  [1.   0.]
              [0.  -1.]

        p = probability

    This noise channel is shown as `NPF` in circuit diagrams.
    """

    def __init__(self, probability: float):
        super().__init__(
            probability=probability,
            qubit_count=1,
            ascii_symbols=["NPF({:.2g})".format(probability)],
        )

    def to_ir(self, target: QubitSet):
        return ir.PhaseFlip.construct(target=target[0], probability=self.probability)

    def to_matrix(self) -> Iterable[np.ndarray]:
        K0 = np.sqrt(1 - self.probability) * np.eye(2, dtype=complex)
        K1 = np.sqrt(self.probability) * np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
        return [K0, K1]

    @staticmethod
    @circuit.subroutine(register=True)
    def phase_flip(target: QubitSetInput, probability: float) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            probability (float): Probability of phase flipping.

        Returns:
            Iterable[Instruction]: `Iterable` of PhaseFlip instructions.

        Examples:
            >>> circ = Circuit().phase_flip(0, probability=0.1)
        """
        return [
            Instruction(Noise.PhaseFlip(probability=probability), target=qubit)
            for qubit in QubitSet(target)
        ]


Noise.register_noise(PhaseFlip)


class Depolarizing(ProbabilisticNoise):
    """Depolarizing noise channel which transforms a density matrix D according to:

    .. math::
        D \\Rightarrow (1-p) D + \\frac{p}{3} X D X^{\\dagger} + \\frac{p}{3} Y D Y^{\\dagger}
        + \\frac{p}{3} Z D Z^{\\dagger}

    where
    ::
        I  =  [1.  0.]
              [0.  1.]

        X  =  [0.  1.]
              [1.  0.]

        Y  =  [0.  -i ]
              [i    0.]

        Z  =  [1.   0.]
              [0.  -1.]

        p = probability

    This noise channel is shown as `ND` in circuit diagrams.
    """

    def __init__(self, probability: float):
        super().__init__(
            probability=probability,
            qubit_count=1,
            ascii_symbols=["ND({:.2g})".format(probability)],
        )

    def to_ir(self, target: QubitSet):
        return ir.Depolarizing.construct(target=target[0], probability=self.probability)

    def to_matrix(self) -> Iterable[np.ndarray]:
        K0 = np.sqrt(1 - self.probability) * np.eye(2, dtype=complex)
        K1 = np.sqrt(self.probability / 3) * np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
        K2 = np.sqrt(self.probability / 3) * 1j * np.array([[0.0, -1.0], [1.0, 0.0]], dtype=complex)
        K3 = np.sqrt(self.probability / 3) * np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
        return [K0, K1, K2, K3]

    @staticmethod
    @circuit.subroutine(register=True)
    def depolarizing(target: QubitSetInput, probability: float) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            probability (float): Probability of depolarizing.

        Returns:
            Iterable[Instruction]: `Iterable` of Depolarizing instructions.

        Examples:
            >>> circ = Circuit().depolarizing(0, probability=0.1)
        """
        return [
            Instruction(Noise.Depolarizing(probability=probability), target=qubit)
            for qubit in QubitSet(target)
        ]


Noise.register_noise(Depolarizing)


class AmplitudeDamping(ProbabilisticNoise):
    """AmplitudeDamping noise channel which transforms a density matrix D according to:

    .. math:: D \\Rightarrow E_0 D E_0^{\\dagger} + E_1 D E1^{\\dagger}
    where
    ::
        E_0  =  [1.  0.       ]
                [0.  sqrt(1-p)]

        E_1  =  [0.  sqrt(p)]
                [0.  0.     ]

        p = probability

    This noise channel is shown as `NAD` in circuit diagrams.
    """

    def __init__(self, probability: float):
        super().__init__(
            probability=probability,
            qubit_count=1,
            ascii_symbols=["NAD({:.2g})".format(probability)],
        )

    def to_ir(self, target: QubitSet):
        return ir.AmplitudeDamping.construct(target=target[0], probability=self.probability)

    def to_matrix(self) -> Iterable[np.ndarray]:
        K0 = np.array([[1.0, 0.0], [0.0, np.sqrt(1 - self.probability)]], dtype=complex)
        K1 = np.array([[0.0, np.sqrt(self.probability)], [0.0, 0.0]], dtype=complex)
        return [K0, K1]

    @staticmethod
    @circuit.subroutine(register=True)
    def amplitude_damping(target: QubitSetInput, probability: float) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            probability (float): Probability of amplitude damping.

        Returns:
            Iterable[Instruction]: `Iterable` of AmplitudeDamping instructions.

        Examples:
            >>> circ = Circuit().amplitude_damping(0, probability=0.1)
        """
        return [
            Instruction(Noise.AmplitudeDamping(probability=probability), target=qubit)
            for qubit in QubitSet(target)
        ]


Noise.register_noise(AmplitudeDamping)


class PhaseDamping(ProbabilisticNoise):
    """Phase damping noise channel which transforms a density matrix D according to:

    .. math:: D \\Rightarrow E_0 D E_0^{\\dagger} + E_1 D E1^{\\dagger}
    where
    ::
        E_0  =  [1.  0.       ]
                [0.  sqrt(1-p)]

        E_1  =  [0.  0.     ]
                [0.  sqrt(p)]

        p = probability

    This noise channel is shown as `NPD` in circuit diagrams.
    """

    def __init__(self, probability: float):
        super().__init__(
            probability=probability,
            qubit_count=1,
            ascii_symbols=["NPD({:.2g})".format(probability)],
        )

    def to_ir(self, target: QubitSet):
        return ir.PhaseDamping.construct(target=target[0], probability=self.probability)

    def to_matrix(self) -> Iterable[np.ndarray]:
        K0 = np.array([[1.0, 0.0], [0.0, np.sqrt(1 - self.probability)]], dtype=complex)
        K1 = np.array([[0.0, 0.0], [0.0, np.sqrt(self.probability)]], dtype=complex)
        return [K0, K1]

    @staticmethod
    @circuit.subroutine(register=True)
    def phase_damping(target: QubitSetInput, probability: float) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            target (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            probability (float): Probability of phase damping.

        Returns:
            Iterable[Instruction]: `Iterable` of PhaseDamping instructions.

        Examples:
            >>> circ = Circuit().phase_damping(0, probability=0.1)
        """
        return [
            Instruction(Noise.PhaseDamping(probability=probability), target=qubit)
            for qubit in QubitSet(target)
        ]


Noise.register_noise(PhaseDamping)


class Kraus(Noise):
    """User-defined noise channel that uses the provided matrices as Kraus operators
    This noise channel is shown as `NK` in circuit diagrams.     

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
            raise ValueError(
                "The input matrices do not define a completely-positive trace-preserving map."
            )

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
            matrix_as_list = [
                [[element.real, element.imag] for element in row] for row in matrix.tolist()
            ]
            serializable.append(matrix_as_list)
        return serializable

    @staticmethod
    @circuit.subroutine(register=True)
    def kraus(
        targets: QubitSetInput, matrices: Iterable[np.array], display_name: str = "NK"
    ) -> Iterable[Instruction]:
        """Registers this function into the circuit class.

        Args:
            targets (Qubit, int, or iterable of Qubit / int): Target qubit(s)
            matrices (Iterable[np.array]): Matrices that define a general noise channel.

        Returns:
            Iterable[Instruction]: `Iterable` of Kraus instructions.

        Examples:
            >>> circ = Circuit().kraus(0, matrices=matrices)
        """
        return Instruction(
            Noise.Kraus(matrices=matrices, display_name=display_name), target=targets
        )


Noise.register_noise(Kraus)
