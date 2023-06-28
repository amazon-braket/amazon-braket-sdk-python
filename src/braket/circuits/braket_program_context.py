import os
from typing import Tuple, List

from braket.circuits import Circuit, Gate, Instruction, QubitSet, observables
from braket.circuits.gates import Unitary
from braket.circuits.translations import (
    braket_noise_gate_to_instruction,
    BRAKET_GATES,
    braket_result_to_result_type,
)
from braket.default_simulator import KrausOperation
from braket.default_simulator.gate_operations import GPhase
from braket.default_simulator.openqasm.program_context import AbstractProgramContext
import numpy as np
from braket.ir.jaqcd.program_v1 import Results
from braket.circuits.noise import Noise


class BraketProgramContext(AbstractProgramContext):
    def __init__(self):
        super().__init__(Circuit())

    def is_builtin_gate(self, name: str) -> bool:
        """Whether the gate is currently in scope as a built-in Braket gate"""
        user_defined_gate = self.is_user_defined_gate(name)
        return name in BRAKET_GATES and not user_defined_gate

    def add_phase_instruction(self, target: Tuple[int], phase_value: int):
        raise NotImplementedError

    def add_gate_instruction(
        self, gate_name: str, target: Tuple[int], *params, ctrl_modifiers: List[int], power: int
    ):
        target_qubits = target[len(ctrl_modifiers) :]
        control_qubits = target[: len(ctrl_modifiers)]
        instruction = Instruction(
            BRAKET_GATES[gate_name](*params[0]),
            target=target_qubits,
            control=control_qubits,
            control_state=ctrl_modifiers,
            power=power,
        )
        self.circuit.add_instruction(instruction)

    def add_custom_unitary(
        self,
        unitary: np.ndarray,
        target: Tuple[int],
    ) -> None:
        """Add a custom Unitary instruction to the circuit"""
        instruction = Instruction(Unitary(unitary)(), target)
        self.circuit.add_instruction(instruction)

    def add_noise_instruction(self, noise: KrausOperation):
        """Add a noise instruction the circuit"""
        self.circuit.add_instruction(braket_noise_gate_to_instruction(noise))

    def add_result(self, result: Results) -> None:
        """Add a result type to the circuit"""
        self.circuit.add_result_type(braket_result_to_result_type(result))
