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

from collections.abc import Iterable
from typing import Optional

import numpy as np

from braket.default_simulator.observables import Hermitian, Identity, TensorProduct
from braket.default_simulator.operation import GateOperation, KrausOperation
from braket.default_simulator.result_types import _from_braket_observable
from braket.ir.jaqcd.program_v1 import Results
from braket.ir.jaqcd.shared_models import Observable, OptionalMultiTarget


class Circuit:
    """
    This is a lightweight analog to braket.ir.jaqcd.program_v1.Program.
    The Interpreter compiles to an IR to hand off to the simulator,
    braket.default_simulator.state_vector_simulator.StateVectorSimulator, for example.
    Our simulator module takes in a circuit specification that satisfies the interface
    implemented by this class.
    """

    def __init__(
        self,
        instructions: Optional[list[GateOperation]] = None,
        results: Optional[list[Results]] = None,
    ):
        self.instructions = []
        self.results = []
        self.qubit_set = set()
        self.measured_qubits = []
        self.target_classical_indices = []

        if instructions:
            for instruction in instructions:
                self.add_instruction(instruction)

        if results:
            for result in results:
                self.add_result(result)

    def add_instruction(self, instruction: [GateOperation, KrausOperation]) -> None:
        """
        Add instruction to the circuit.

        Args:
            instruction (GateOperation): Instruction to add.
        """
        self.instructions.append(instruction)
        self.qubit_set |= set(instruction.targets)

    def add_measure(self, target: tuple[int], classical_targets: Iterable[int] = None):
        for index, qubit in enumerate(target):
            if qubit in self.measured_qubits:
                raise ValueError(f"Qubit {qubit} is already measured or captured.")
            self.measured_qubits.append(qubit)
            self.qubit_set.add(qubit)
            self.target_classical_indices.append(
                classical_targets[index]
                if classical_targets
                else max(index, len(self.target_classical_indices))
            )

    def add_result(self, result: Results) -> None:
        """
        Add result type to the circuit.

        Args:
            result (Results): Result type to add.
        """
        self.results.append(result)
        if isinstance(result, OptionalMultiTarget) and result.targets is not None:
            self.qubit_set |= set(result.targets)

    @property
    def num_qubits(self) -> int:
        return len(self.qubit_set)

    @property
    def basis_rotation_instructions(self):
        """Basis rotation instructions implied by the provided observables"""
        basis_rotation_instructions = []
        observable_map = {}

        def process_observable(observable):
            if isinstance(observable, Identity):
                return
            measured_qubits = tuple(observable.measured_qubits)
            for qubit in measured_qubits:
                for target, previously_measured in observable_map.items():
                    if qubit in target:
                        # must ensure that target is the same
                        if target != measured_qubits:
                            raise ValueError("Qubit part of incompatible results targets")
                        # must ensure observable is the same
                        if type(previously_measured) is not type(observable):
                            raise ValueError("Conflicting result types applied to a single qubit")
                        # including matrix value for Hermitians
                        if isinstance(observable, Hermitian):
                            if not np.allclose(previously_measured.matrix, observable.matrix):
                                raise ValueError(
                                    "Conflicting result types applied to a single qubit"
                                )
            observable_map[measured_qubits] = observable

        for result in self.results:
            if isinstance(result, Observable):
                observables = result.observable

                if result.targets is not None:
                    braket_obs = _from_braket_observable(observables, result.targets)

                    if isinstance(braket_obs, TensorProduct):
                        for factor in braket_obs.factors:
                            process_observable(factor)
                    else:
                        process_observable(braket_obs)

                else:
                    for q in range(self.num_qubits):
                        braket_obs = _from_braket_observable(observables, [q])
                        process_observable(braket_obs)

        for obs in observable_map.values():
            diagonalizing_gates = obs.diagonalizing_gates(self.num_qubits)
            basis_rotation_instructions.extend(diagonalizing_gates)

        return basis_rotation_instructions

    def __eq__(self, other: Circuit):
        return (self.instructions, self.results) == (other.instructions, other.results)
