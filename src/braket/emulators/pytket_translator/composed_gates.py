from collections.abc import Iterable
from typing import List, Union

from pytket.circuit import Circuit, OpType
from sympy import Expr, Symbol


class ComposedGates:
    @staticmethod
    def add_pswap(
        circ: Circuit, arguments: Iterable[Union[float, Expr, Symbol]], qubits: List[int]
    ) -> None:
        """
        Applies a pswap operation to the target qubits in the provided circuit using
        gate operations available in Pytket.
        Args:
            circ (Circuit): The pytket circuit to add the gate to.
            arguments (Iterable[Union[float, Expr, Symbol]]): Contains the
                pswap angle argument.
            qubits (List[int]): The indices of the target qubits in the pswap operation.
        """
        assert len(arguments) == 1
        assert len(qubits) == 2
        circ.add_gate(OpType.ZZPhase, arguments, [qubits[0], qubits[1]])
        circ.add_gate(OpType.SWAP, [qubits[0], qubits[1]])
        circ.add_phase(arguments[0] / 2)

    @staticmethod
    def add_cphaseshift00(
        circ: Circuit, arguments: Iterable[Union[float, Expr, Symbol]], qubits: List[int]
    ) -> None:
        """
        Applies a cphaseshift00 operation to the target qubits in the provided circuit using
        gate operations available in Pytket.
        Args:
            circ (Circuit): The pytket circuit to add the gate to.
            arguments (Iterable[Union[float, Expr, Symbol]]): Contains the
                cphaseshift00 angle argument.
            qubits (List[int]): The indices of the target qubits in the cphaseshift00 operation.
        """
        assert len(arguments) == 1
        assert len(qubits) == 2
        circ.add_gate(OpType.X, [qubits[1]])
        circ.add_gate(OpType.CX, [qubits[1], qubits[0]])
        circ.add_gate(OpType.CU1, arguments, [qubits[1], qubits[0]])
        circ.add_gate(OpType.CX, [qubits[1], qubits[0]])
        circ.add_gate(OpType.X, [qubits[1]])

    @staticmethod
    def add_cphaseshift01(
        circ: Circuit, arguments: Iterable[Union[float, Expr, Symbol]], qubits: List[int]
    ) -> None:
        """
        Applies a cphaseshift01 operation to the target qubits in the provided circuit using
        gate operations available in Pytket.
        Args:
            circ (Circuit): The pytket circuit to add the gate to.
            arguments (Iterable[Union[float, Expr, Symbol]]): Contains the
                cphaseshift01 angle argument.
            qubits (List[int]): The indices of the target qubits in the cphaseshift01 operation.
        """
        assert len(arguments) == 1
        assert len(qubits) == 2
        circ.add_gate(OpType.CX, [qubits[1], qubits[0]])
        circ.add_gate(OpType.CU1, arguments, [qubits[1], qubits[0]])
        circ.add_gate(OpType.CX, [qubits[1], qubits[0]])

    @staticmethod
    def add_cphaseshift10(
        circ: Circuit, arguments: Iterable[Union[float, Expr, Symbol]], qubits: List[int]
    ) -> None:
        """
        Applies a cphaseshift10 operation to the target qubits in the provided circuit using
        gate operations available in Pytket.
        Args:
            circ (Circuit): The pytket circuit to add the gate to.
            arguments (Iterable[Union[float, Expr, Symbol]]): Contains the
                cphaseshift10 angle argument.
            qubits (List[int]): The indices of the target qubits in the cphaseshift10 operation.
        """
        assert len(arguments) == 1
        assert len(qubits) == 2
        circ.add_gate(OpType.CX, [qubits[0], qubits[1]])
        circ.add_gate(OpType.CU1, arguments, [qubits[0], qubits[1]])
        circ.add_gate(OpType.CX, [qubits[0], qubits[1]])
