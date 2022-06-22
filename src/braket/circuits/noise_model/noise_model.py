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

from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional, Type

from braket.circuits.circuit import Circuit
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.noise import Noise
from braket.circuits.noise_model.circuit_instruction_criteria import CircuitInstructionCriteria
from braket.circuits.noise_model.criteria import Criteria, CriteriaKey, CriteriaKeyResult
from braket.circuits.noise_model.initialization_criteria import InitializationCriteria
from braket.circuits.noise_model.result_type_criteria import ResultTypeCriteria
from braket.circuits.qubit_set import QubitSetInput
from braket.circuits.result_types import ObservableResultType


@dataclass
class NoiseModelInstruction:
    """Represents a single instruction for a Noise Model."""

    noise: Noise
    criteria: Criteria

    def __init__(self, noise: Noise, criteria: Criteria):
        if not isinstance(noise, Noise):
            raise ValueError(f"{noise} must be a Noise type.")
        if not isinstance(criteria, Criteria):
            raise ValueError(f"{criteria} must be a Criteria type.")
        self.noise = noise
        self.criteria = criteria

    def __repr__(self):
        return f"NoiseModelInstruction(noise={self.noise}, criteria={self.criteria})"

    def __str__(self):
        return f"{self.noise}, {self.criteria}"

    def to_dict(self) -> dict:
        """Converts this object to a dictionary."""
        return {"noise": self.noise.to_dict(), "criteria": self.criteria.to_dict()}

    @classmethod
    def from_dict(cls, noise_model_item: dict) -> NoiseModelInstruction:
        """
        Converts a dictionary representing an object of this class into an instance of this class.

        Args:
            noise_model_item (dict): A dictionary representation of an object of this class.

        Returns:
            NoiseModelInstruction: An object of this class that corresponds
            to the passed in dictionary.
        """
        return NoiseModelInstruction(
            noise=Noise.from_dict(noise_model_item["noise"]),
            criteria=Criteria.from_dict(noise_model_item["criteria"]),
        )


@dataclass
class NoiseModelInstructions:
    """Represents the instructions in a noise model, seperated by type."""

    initialization_noise: List[NoiseModelInstruction]
    gate_noise: List[NoiseModelInstruction]
    readout_noise: List[NoiseModelInstruction]


class NoiseModel:
    """
    A Noise Model can be thought of as a set of Noise objects, and a corresponding set of
    criteria for how each Noise object should be applied to a circuit. For example, a noise model
    may represent that every H gate that acts on qubit 0 has a 10% probability of a bit flip, and
    every X gate that acts on qubit 0 has a 20% probability of a bit flip, and 5% probability of
    a phase flip.
    """

    def __init__(self, instructions: List[NoiseModelInstruction] = None):
        self._instructions = instructions or []

    def __repr__(self):
        return str({"instructions": list(self._instructions)})

    def __str__(self):
        instructions = self.get_instructions_by_type()
        all_strings = []
        all_strings.extend(
            NoiseModel._items_to_string("Initialization Noise:", instructions.initialization_noise)
        )
        all_strings.extend(NoiseModel._items_to_string("Gate Noise:", instructions.gate_noise))
        all_strings.extend(
            NoiseModel._items_to_string("Readout Noise:", instructions.readout_noise)
        )
        return "\n".join(all_strings)

    @property
    def instructions(self) -> List[NoiseModelInstruction]:
        """
        List all the noise in the NoiseModel.

        Returns:
            List[NoiseModelInstruction]: The noise model instructions.
        """
        return self._instructions

    def add_noise(self, noise: Noise, criteria: Criteria) -> NoiseModel:
        """Modifies the NoiseModel to add noise with a given Criteria.

        Args:
            noise (Noise): The noise to add.
            criteria (Criteria): The criteria that determines when the noise will be applied.

        Returns:
            NoiseModel: This NoiseModel object.
        """
        return self._add_instruction(NoiseModelInstruction(noise, criteria))

    def insert_noise(self, index: int, noise: Noise, criteria: Criteria) -> NoiseModel:
        """Modifies the NoiseModel to insert a noise with a given Criteria at particular position.

        Args:
            index (int): The index at which to insert.
            noise (Noise): The noise to insert.
            criteria (Criteria): The criteria that determines when the noise will be applied.

        Returns:
            NoiseModel: This NoiseModel object.
        """
        self._instructions.insert(index, NoiseModelInstruction(noise, criteria))
        return self

    def _add_instruction(self, instruction: NoiseModelInstruction) -> NoiseModel:
        """Modifies the NoiseModel to add noise with a given Criteria.

        Args:
            instruction (NoiseModelInstruction): The noise model instruction to add.

        Returns:
            NoiseModel: This NoiseModel object.
        """
        self._instructions.append(instruction)
        return self

    def remove_noise(self, index: int) -> NoiseModel:
        """
        Removes the noise and corresponding criteria from the NoiseModel at the given index.

        Args:
            index (int): The index of the instruction to remove.

        Returns:
            NoiseModel: This NoiseModel object.

        Throws:
            IndexError: If the provided index is not less than the number of noise (as returned
                from items()).
        """
        self._instructions.pop(index)
        return self

    def get_instructions_by_type(self) -> NoiseModelInstructions:
        """Returns the noise in this model by noise type.
        Returns:
            NoiseModelInstructions: The noise model instructions.
        """
        init_noise = []
        gate_noise = []
        readout_noise = []
        for item in self._instructions:
            if isinstance(item.criteria, InitializationCriteria):
                init_noise.append(item)
            elif isinstance(item.criteria, CircuitInstructionCriteria):
                gate_noise.append(item)
            elif isinstance(item.criteria, ResultTypeCriteria):
                readout_noise.append(item)
        return NoiseModelInstructions(
            initialization_noise=init_noise,
            gate_noise=gate_noise,
            readout_noise=readout_noise,
        )

    def from_filter(
        self,
        qubit: Optional[QubitSetInput] = None,
        gate: Optional[Gate] = None,
        noise: Optional[Type[Noise]] = None,
    ) -> NoiseModel:
        """
        Returns a new NoiseModel from this NoiseModel using a given filter. If no filters are
        specified, the returned NoiseModel will be the same as this one.

        Args:
            qubit (Optional[QubitSetInput]): The qubit to filter. Default is None.
                If not None, the returned NoiseModel will only have Noise that might be applicable
                to the passed qubit (or qubit list, if the criteria acts on a multi-qubit Gate).
            gate (Optional[Gate]): The gate to filter. Default is None. If not None,
                the returned NoiseModel will only have Noise that might be applicable
                to the passed Gate.
            noise (Optional[Type[Noise]]): The noise class to filter. Default is None.
                If not None, the returned NoiseModel will only have noise that is of the same
                class as the given noise class.

        Returns:
            NoiseModel: A noise model containing Noise and Criteria that are applicable for
            the given filter.
        """
        new_model = NoiseModel()
        for item in self._instructions:
            if noise is not None and not isinstance(item.noise, noise):
                continue
            if gate is not None:
                gate_keys = item.criteria.get_keys(CriteriaKey.GATE)
                if gate_keys != CriteriaKeyResult.ALL and gate not in gate_keys:
                    continue
            if qubit is not None:
                qubit_keys = item.criteria.get_keys(CriteriaKey.QUBIT)
                if qubit_keys != CriteriaKeyResult.ALL and qubit not in qubit_keys:
                    continue
            new_model.add_noise(item.noise, item.criteria)
        return new_model

    def apply(self, circuit: Circuit) -> Circuit:
        """
        Applies this noise model to a circuit, and returns a new circuit that's the `noisy`
        version of the given circuit. If multiple noise will act on the same instruction,
        they will be applied in the order they are added to the noise model.

        Args:
            circuit (Circuit): a circuit to apply `noise` to.

        Returns:
            Circuit: A new circuit that's a `noisy` version of the passed in circuit.
        """
        instructions = self.get_instructions_by_type()
        new_circuit = NoiseModel._apply_gate_noise(circuit, instructions.gate_noise)
        new_circuit = NoiseModel._apply_init_noise(new_circuit, instructions.initialization_noise)
        return NoiseModel._apply_readout_noise(new_circuit, instructions.readout_noise)

    def to_dict(self) -> dict:
        """Converts this object to a dictionary."""
        return {"instructions": [item.to_dict() for item in self._instructions]}

    @classmethod
    def _apply_gate_noise(
        cls,
        circuit: Circuit,
        gate_noise_instructions: List[NoiseModelInstruction],
    ) -> Circuit:
        """
        Applies the gate noise to return a new circuit that's the `noisy` version of the given
        circuit.

        Args:
            circuit (Circuit): a circuit to apply `noise` to.
            gate_noise_instructions (List[NoiseModelInstruction]): a list of gate noise
                instructions to apply to the circuit.

        Returns:
            Circuit: A new circuit that's a `noisy` version of the passed in circuit. The targets
            set will be populated with the list of targets in the new circuit.
        """
        new_circuit = Circuit()
        for circuit_instruction in circuit.instructions:
            new_circuit.add_instruction(circuit_instruction)
            target_qubits = list(circuit_instruction.target)
            for item in gate_noise_instructions:
                if item.criteria.instruction_matches(circuit_instruction):
                    if item.noise.fixed_qubit_count() == len(target_qubits):
                        new_circuit.add_instruction(Instruction(item.noise, target_qubits))
                    else:
                        for qubit in target_qubits:
                            new_circuit.add_instruction(Instruction(item.noise, qubit))
        for result_type in circuit.result_types:
            new_circuit.add_result_type(result_type)
        return new_circuit

    @classmethod
    def _apply_init_noise(
        cls,
        circuit: Circuit,
        init_noise_instructions: List[NoiseModelInstruction],
    ) -> Circuit:
        """
        Applies the initialization noise of this noise model to a circuit and returns the circuit.

        Args:
            circuit (Circuit): A circuit to apply `noise` to.
            init_noise_instructions (List[NoiseModelInstruction]): A list of initialization noise
                model instructions.

        Returns:
            Circuit: The passed in circuit, with the initialization noise applied.
        """
        if not init_noise_instructions:
            return circuit
        for item in init_noise_instructions:
            qubits = item.criteria.qubit_intersection(circuit.qubits)
            if len(qubits) > 0:
                circuit.apply_initialization_noise(item.noise, list(qubits))
        return circuit

    @classmethod
    def _apply_readout_noise(
        cls,
        circuit: Circuit,
        readout_noise_instructions: List[NoiseModelInstruction],
    ) -> Circuit:
        """
        Applies the readout noise of this noise model to a circuit and returns the circuit.

        Args:
            circuit (Circuit): A circuit to apply `noise` to.
            readout_noise_instructions (List[NoiseModelInstruction]): The list of readout noise
                to apply.

        Returns:
            Circuit: The passed in circuit, with the readout noise applied.
        """
        if not readout_noise_instructions or not circuit.result_types:
            return circuit
        return _apply_noise_on_observable_result_types(circuit, readout_noise_instructions)

    @classmethod
    def _items_to_string(
        cls, instructions_title: str, instructions: List[NoiseModelInstruction]
    ) -> List[str]:
        """
        Creates a string representation of a list of instructions.

        Args:
            instructions_title (str): The title for this list of instructions.
            instructions (List[NoiseModelInstruction]): A list of instructions.

        Returns:
            List[str]: A list of string representations of the passed instructions.
        """
        results = []
        if len(instructions) > 0:
            results.append(instructions_title)
            for item in instructions:
                results.append(f"  {item}")
        return results

    @classmethod
    def from_dict(cls, noise_dict: dict) -> NoiseModel:
        """
        Converts a dictionary representing an object of this class into an instance of this class.

        Args:
            noise_dict (dict): A dictionary representation of an object of this class.

        Returns:
            NoiseModel: An object of this class that corresponds to the passed in dictionary.
        """
        model = NoiseModel()
        all(
            model._add_instruction(NoiseModelInstruction.from_dict(item))
            for item in noise_dict["instructions"]
        )
        return model


def _apply_noise_on_observable_result_types(
    circuit: Circuit, readout_noise_instructions: List[NoiseModelInstruction]
) -> Circuit:
    """Applies readout noise based on the observable result types in the circuit. Each applicable
    Noise will be applied only once to a target in the ObservableResultType.

    Args:
        circuit (Circuit): The circuit to apply the readout noise to.

    Returns:
        Circuit: The passed in circuit, with the readout noise applied.
    """
    result_types = circuit.result_types
    noise_to_apply = defaultdict(set)
    for result_type in result_types:
        if isinstance(result_type, ObservableResultType):
            target_qubits = list(result_type.target)
            for item_index, item in enumerate(readout_noise_instructions):
                if item.criteria.result_type_matches(result_type):
                    for target_qubit in target_qubits:
                        noise_to_apply[target_qubit].add(item_index)
    for qubit in noise_to_apply:
        for noise_item_index in noise_to_apply[qubit]:
            item = readout_noise_instructions[noise_item_index]
            circuit.apply_readout_noise(item.noise, qubit)
    return circuit
