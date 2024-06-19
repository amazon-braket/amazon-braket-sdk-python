from typing import List

from pytket.circuit import Circuit, OpType


class ComposedGates:
    @staticmethod
    def add_pswap(circ: Circuit, arguments, qubits: List[int]):
        assert len(arguments) == 1
        assert len(qubits) == 2
        circ.add_gate(OpType.ZZPhase, arguments, [qubits[0], qubits[1]])
        circ.add_gate(OpType.SWAP, [qubits[0], qubits[1]])
        circ.add_phase(arguments[0] / 2)

    @staticmethod
    def add_cphaseshift00(circ: Circuit, arguments, qubits: List[int]):
        assert len(arguments) == 1
        assert len(qubits) == 2
        circ.add_gate(OpType.X, [qubits[1]])
        circ.add_gate(OpType.CX, [qubits[1], qubits[0]])
        circ.add_gate(OpType.CU1, arguments, [qubits[1], qubits[0]])
        circ.add_gate(OpType.CX, [qubits[1], qubits[0]])
        circ.add_gate(OpType.X, [qubits[1]])

    @staticmethod
    def add_cphaseshift01(circ: Circuit, arguments, qubits: List[int]):
        assert len(arguments) == 1
        assert len(qubits) == 2
        circ.add_gate(OpType.CX, [qubits[1], qubits[0]])
        circ.add_gate(OpType.CU1, arguments, [qubits[1], qubits[0]])
        circ.add_gate(OpType.CX, [qubits[1], qubits[0]])

    @staticmethod
    def add_cphaseshift10(circ: Circuit, arguments, qubits: List[int]):
        assert len(arguments) == 1
        assert len(qubits) == 2
        circ.add_gate(OpType.CX, [qubits[0], qubits[1]])
        circ.add_gate(OpType.CU1, arguments, [qubits[0], qubits[1]])
        circ.add_gate(OpType.CX, [qubits[0], qubits[1]])
