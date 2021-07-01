# general imports
import math

# AWS imports: Import Braket SDK modules
from braket.circuits.composite_operator import CompositeOperator
from braket.circuits.gates import *
from braket.circuits.instruction import Instruction
from braket.circuits.qubit_set import QubitSet


class GHZ(CompositeOperator):
    """
    Operator for constructing the Greenberger–Horne–Zeilinger state.

    Args:
        qubit_count (int): Number of target qubits.
    """

    def __init__(self, qubit_count: int):
        super().__init__(qubit_count=qubit_count, ascii_symbols=["GHZ"])

    def to_ir(self, target: QubitSet):
        return [instr.to_ir() for instr in self.decompose(target)]

    def decompose(self, target: QubitSet) -> Iterable[Instruction]:
        """
        Returns an iterable of instructions corresponding to the quantum circuit that constructs
        the Greenberger-Horne-Zeilinger (GHZ) state, applied to the argument qubits.

        Args:
            target (QubitSet): Target qubits

        Returns:
            Iterable[Instruction]: iterable of instructions for GHZ

        Raises:
            ValueError: If number of qubits in `target` does not equal `qubit_count`.
        """
        if len(target) != self.qubit_count:
            raise ValueError(f"Operator qubit count {self.qubit_count} must be "
                             f"equal to size of target qubit set {target}")

        instructions = [Instruction(Gate.H(), target=target[0])]
        for i in range(0, len(target) - 1):
            instructions.append(Instruction(Gate.CNot(), target=[target[i], target[i + 1]]))
        return instructions

    @staticmethod
    @circuit.subroutine(register=True)
    def ghz(targets: QubitSet):
        """
        Registers this function into the circuit class.

        Args:
            targets (QubitSet): Target qubits.

        Returns:
            Instruction: GHZ instruction.

        Examples:
            >>> circ = Circuit().ghz([0, 1, 2])
        """
        return Instruction(CompositeOperator.GHZ(len(targets)), target=targets)


CompositeOperator.register_composite_operator(GHZ)


class QFT(CompositeOperator):
    """
    Operator for quantom fourier transform

    Args:
        qubit_count (int): Number of target qubits.
        method (str): String specification of method to use for decomposition,
                         with non-recursive approach by default (method="default"),
                         or recursive approach (method="recursive").
    """

    def __init__(self, qubit_count: int, method: str = "default"):

        if method != "default" and method != "recursive":
            raise TypeError("method must either be 'default' or 'recursive'.")

        self._method = method
        super().__init__(qubit_count=qubit_count, ascii_symbols=["QFT"])

    def to_ir(self, target: QubitSet):
        return [instr.to_ir() for instr in self.decompose(target)]

    def decompose(self, target: QubitSet) -> Iterable[Instruction]:
        """
        Returns an iterable of instructions corresponding to the Quantum Fourier Transform (QFT)
        algorithm, applied to the argument qubits.

        Args:
            target (QubitSet): Target qubits

        Returns:
            Iterable[Instruction]: iterable of instructions for QFT

        Raises:
            ValueError: If number of qubits in `target` does not equal `qubit_count`.
        """

        if len(target) != self.qubit_count:
            raise ValueError(f"Operator qubit count {self.qubit_count} must be "
                             f"equal to size of target qubit set {target}")

        instructions = []

        # get number of qubits
        num_qubits = len(target)

        if self._method == "recursive":
            # On a single qubit, the QFT is just a Hadamard.
            if len(target) == 1:
                instructions.append(Instruction(Gate.H(), target=target))

            # For more than one qubit, we define mQFT recursively:
            else:

                # First add a Hadamard gate
                instructions.append(Instruction(Gate.H(), target=target[0]))

                # Then apply the controlled rotations, with weights (angles) defined by the distance to the control qubit.
                for k, qubit in enumerate(target[1:]):
                    instructions.append(
                        Instruction(Gate.CPhaseShift(2 * math.pi / (2 ** (k + 2))), target=[qubit, target[0]]))

                # Now apply the above gates recursively to the rest of the qubits
                instructions.append(Instruction(CompositeOperator.mQFT(len(target[1:])), target=target[1:]))

        elif self._method == "default":
            for k in range(num_qubits):
                # First add a Hadamard gate
                instructions.append(Instruction(Gate.H(), target=[target[k]]))

                # Then apply the controlled rotations, with weights (angles) defined by the distance to the control qubit.
                # Start on the qubit after qubit k, and iterate until the end.  When num_qubits==1, this loop does not run.
                for j in range(1, num_qubits - k):
                    angle = 2 * math.pi / (2 ** (j + 1))
                    instructions.append(Instruction(Gate.CPhaseShift(angle), target=[target[k + j], target[k]]))

        # Then add SWAP gates to reverse the order of the qubits:
        for i in range(math.floor(num_qubits / 2)):
            instructions.append(Instruction(Gate.Swap(), target=[target[i], target[-i - 1]]))

        return instructions

    @staticmethod
    @circuit.subroutine(register=True)
    def qft(targets: QubitSet, method: str = "default") -> Instruction:
        """Registers this function into the circuit class.

        Args:
            targets (QubitSet): Target qubits.

        Returns:
            Instruction: QFT instruction.

        Examples:
            >>> circ = Circuit().mqft([0, 1, 2])
        """
        return Instruction(CompositeOperator.QFT(len(targets), method), target=targets)


CompositeOperator.register_composite_operator(QFT)


class mQFT(CompositeOperator):
    """
    Operator for "modified" quantom fourier transform. This is the same as quantum fourier transform but
    excluding the SWAP gates.

    Args:
        qubit_count (int): Number of target qubits.
    """

    def __init__(self, qubit_count: int):
        super().__init__(qubit_count=qubit_count, ascii_symbols=["mQFT"])

    def to_ir(self, target: QubitSet):
        return [instr.to_ir() for instr in self.decompose(target)]

    def decompose(self, target: QubitSet) -> Iterable[Instruction]:
        """
        Returns an iterable of instructions corresponding to the Quantum Fourier Transform (QFT)
        algorithm, applied to the argument qubits.

        Args:
            target (QubitSet): Target qubits

        Returns:
            Iterable[Instruction]: iterable of instructions for QFT

        Raises:
            ValueError: If number of qubits in `target` does not equal `qubit_count`.
        """

        if len(target) != self.qubit_count:
            raise ValueError(f"Operator qubit count {self.qubit_count} must be "
                             f"equal to size of target qubit set {target}")

        instructions = []

        if len(target) == 1:
            instructions.append(Instruction(Gate.H(), target=target))

        # For more than one qubit, we define mQFT recursively:
        else:

            # First add a Hadamard gate
            instructions.append(Instruction(Gate.H(), target=target[0]))

            # Then apply the controlled rotations, with weights (angles) defined by the distance to the control qubit.
            for k, qubit in enumerate(target[1:]):
                instructions.append(
                    Instruction(Gate.CPhaseShift(2 * math.pi / (2 ** (k + 2))), target=[qubit, target[0]]))

            # Now apply the above gates recursively to the rest of the qubits
            instructions.append(Instruction(CompositeOperator.mQFT(len(target[1:])), target=target[1:]))

        return instructions

    @staticmethod
    @circuit.subroutine(register=True)
    def mqft(targets: QubitSet) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            targets (QubitSet): Target qubits.

        Returns:
            Instruction: QFT instruction.

        Examples:
            >>> circ = Circuit().mqft([0, 1, 2])
        """
        return Instruction(CompositeOperator.mQFT(len(targets)), target=targets)


CompositeOperator.register_composite_operator(mQFT)


class iQFT(CompositeOperator):
    """
    Operator for inverse quantom fourier transform

    Args:
        qubit_count (int): Number of target qubits.
    """

    def __init__(self, qubit_count: int):
        super().__init__(qubit_count=qubit_count, ascii_symbols=["iQFT"])

    def to_ir(self, target: QubitSet):
        return [instr.to_ir() for instr in self.decompose(target)]

    def decompose(self, target: QubitSet) -> Iterable[Instruction]:
        """
        Returns an iterable of instructions corresponding to the inverse Quantum Fourier Transform
        (iQFT) algorithm, applied to the argument qubits.

        Args:
            target (QubitSet): Target qubits

        Returns:
            Iterable[Instruction]: iterable of instructions for iQFT

        Raises:
            ValueError: If number of qubits in `target` does not equal `qubit_count`.
        """

        if len(target) != self.qubit_count:
            raise ValueError(f"Operator qubit count {self.qubit_count} must be "
                             f"equal to size of target qubit set {target}")

        instructions = []

        # Set number of qubits
        num_qubits = len(target)

        # First add SWAP gates to reverse the order of the qubits:
        for i in range(math.floor(num_qubits / 2)):
            instructions.append(Instruction(Gate.Swap(), target=[target[i], target[-i - 1]]))

        # Start on the last qubit and work to the first.
        for k in reversed(range(num_qubits)):

            # Apply the controlled rotations, with weights (angles) defined by the distance to the control qubit.
            # These angles are the negative of the angle used in the QFT.
            # Start on the last qubit and iterate until the qubit after k.
            # When num_qubits==1, this loop does not run.
            for j in reversed(range(1, num_qubits - k)):
                angle = -2 * math.pi / (2 ** (j + 1))
                instructions.append(Instruction(Gate.CPhaseShift(angle), target=[target[k + j], target[k]]))

            # Then add a Hadamard gate
            instructions.append(Instruction(Gate.H(), target=[target[k]]))

        return instructions

    @staticmethod
    @circuit.subroutine(register=True)
    def iqft(targets: QubitSet) -> Instruction:
        """Registers this function into the circuit class.

        Args:
            targets (QubitSet): Target qubits.

        Returns:
            Instruction: iQFT instruction.

        Examples:
            >>> circ = Circuit().iqft([0, 1, 2])
        """
        return Instruction(CompositeOperator.iQFT(len(targets)), target=targets)


CompositeOperator.register_composite_operator(iQFT)


class QPE(CompositeOperator):
    """
    Operator for Quantum Phase Estimation.

    Args:
        precision_qubit_count (int): The number of qubits in the precision register.
        query_qubit_count (int): The number of qubits in the query register.
        matrix (numpy.ndarray): Unitary matrix whose eigenvalues we wish to estimate.
        condense (boolean): Optional boolean flag for controlled unitaries,
                         with C-(U^{2^k}) by default (default is True),
                         or C-U controlled-unitary (2**power) times.

    Raises:
        ValueError: If `matrix` is not a two-dimensional square matrix,
            or has a dimension length that is not a positive power of 2,
            or is not unitary.
    """

    def __init__(self, precision_qubit_count: int, query_qubit_count: int, matrix: np.ndarray, condense=True):
        verify_quantum_operator_matrix_dimensions(matrix)
        self._matrix = np.array(matrix, dtype=complex)

        if not is_unitary(self._matrix):
            raise ValueError(f"{self._matrix} is not unitary")

        self._condense = condense
        self._precision_qubit_count = precision_qubit_count
        self._query_qubit_count = query_qubit_count
        super().__init__(qubit_count=precision_qubit_count + query_qubit_count, ascii_symbols=["QPE"])

    def to_ir(self, target: QubitSet):
        return [instr.to_ir() for instr in self.decompose(target)]

    def controlled_unitary(self, unitary) -> np.ndarray:
        # Define projectors onto the computational basis
        p0 = np.array([[1.0, 0.0], [0.0, 0.0]])

        p1 = np.array([[0.0, 0.0], [0.0, 1.0]])

        # Construct numpy matrix
        id_matrix = np.eye(len(unitary))
        controlled_matrix = np.kron(p0, id_matrix) + np.kron(p1, unitary)

        return controlled_matrix

    def decompose(self, target: QubitSet) -> Iterable[Instruction]:
        """
        Returns an iterable of instructions corresponding to the Quantum Phase Estimation
        (QPE) algorithm, applied to the argument qubits.

        Args:
            target (QubitSet): Target qubits

        Returns:
            Iterable[Instruction]: iterable of instructions for QPE

        Raises:
            ValueError: If number of qubits in `target` does not equal to total number of precision
                and query qubits.
        """

        if len(target) != self.qubit_count:
            raise ValueError(f"Operator qubit count {self.qubit_count} must be "
                             f"equal to size of target qubit set {target}")

        precision_qubits = target[:self._precision_qubit_count]
        query_qubits = target[self._precision_qubit_count:self._precision_qubit_count + self._query_qubit_count]

        # Apply Hadamard across precision qubits
        instructions = [Instruction(Gate.H(), target=qubit) for qubit in precision_qubits]

        # Apply controlled unitaries. Start with the last precision_qubit, and end with the first
        for ii, qubit in enumerate(reversed(precision_qubits)):
            # Set power exponent for unitary
            power = ii

            # Alternative 1: Implement C-(U^{2^k})
            if self._condense:
                # Define new unitary with matrix U^{2^k}
                Uexp = np.linalg.matrix_power(self._matrix, 2 ** power)
                CUexp = self.controlled_unitary(Uexp)

                # Apply the controlled unitary C-(U^{2^k})
                instructions.append(Instruction(Gate.Unitary(CUexp), target=[qubit] + list(query_qubits)))

            # Alternative 2: One can instead apply controlled-unitary (2**power) times to get C-U^{2^power}
            else:
                for _ in range(2 ** power):
                    CU = self.controlled_unitary(self._matrix)
                    instructions.append(Instruction(Gate.Unitary(CU), target=[qubit] + list(query_qubits)))

        # Apply inverse qft to the precision_qubits
        instructions.append(Instruction(CompositeOperator.iQFT(len(precision_qubits)), precision_qubits))

        return instructions

    @staticmethod
    @circuit.subroutine(register=True)
    def qpe(targets1: QubitSet, targets2: QubitSet, matrix: np.ndarray, condense=True):
        """Registers this function into the circuit class.

        Args:
            targets1 (QubitSet): Qubits defining the precision register.
            targets2 (QubitSet): Qubits defining the query register.
            matrix: Unitary matrix whose eigenvalues we wish to estimate

        Returns:
            Instruction: QPE instruction.

        Raises:
            ValueError: If `matrix` is not a two-dimensional square matrix,
                or has a dimension length that is not compatible with the `targets`,
                or is not unitary.

        Examples:
            >>> circ = Circuit().qpe(QubitSet([0, 1, 2]), QubitSet([4, 5, 6]), np.array([[0, 1], [1, 0]]))
        """
        if 2 ** len(targets2) != matrix.shape[0]:
            raise ValueError("Dimensions of the supplied unitary are incompatible with the query qubits")

        return Instruction(CompositeOperator.QPE(len(targets1), len(targets2), matrix, condense),
                           target=targets1 + targets2)


CompositeOperator.register_composite_operator(QPE)
