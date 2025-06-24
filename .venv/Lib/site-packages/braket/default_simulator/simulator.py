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

import uuid
import warnings
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Union

import numpy as np

from braket.default_simulator.observables import Hermitian, TensorProduct
from braket.default_simulator.openqasm.circuit import Circuit
from braket.default_simulator.openqasm.interpreter import Interpreter
from braket.default_simulator.openqasm.program_context import AbstractProgramContext, ProgramContext
from braket.default_simulator.operation import Observable, Operation
from braket.default_simulator.operation_helpers import from_braket_instruction
from braket.default_simulator.result_types import (
    ResultType,
    TargetedResultType,
    from_braket_result_type,
)
from braket.default_simulator.simulation import Simulation
from braket.device_schema import DeviceActionType
from braket.ir.jaqcd import Program as JaqcdProgram
from braket.ir.jaqcd.program_v1 import Results
from braket.ir.jaqcd.shared_models import MultiTarget, OptionalMultiTarget
from braket.ir.openqasm import Program as OpenQASMProgram
from braket.simulator import BraketSimulator
from braket.task_result import (
    AdditionalMetadata,
    GateModelTaskResult,
    ResultTypeValue,
    TaskMetadata,
)

_NOISE_INSTRUCTIONS = frozenset(
    instr.lower().replace("_", "")
    for instr in [
        "amplitude_damping",
        "bit_flip",
        "depolarizing",
        "generalized_amplitude_damping",
        "kraus",
        "pauli_channel",
        "two_qubit_pauli_channel",
        "phase_flip",
        "phase_damping",
        "two_qubit_dephasing",
        "two_qubit_depolarizing",
    ]
)


class OpenQASMSimulator(BraketSimulator, ABC):
    """An abstract simulator that runs an OpenQASM 3 program.

    Translation of individual operations and observables from OpenQASM to the desired format
    is handled by implementing the `AbstractProgramContext` interface. This implementation is
    exposed by implementing the `create_program_context` method, which enables the `parse_program`
    method to translate an entire OpenQASM program:

    >>> class MyProgramContext(AbstractProgramContext):
    >>>     def __init__(self):
    >>>         ...
    >>>
    >>>     def add_gate_instruction(self, gate_name: str, target: Tuple[int], ...):
    >>>         ...
    >>>
    >>>     # Implement other MyProgramContext interface methods
    >>>
    >>> class MySimulator(OpenQASMSimulator):
    >>>     def create_program_context(self) -> AbstractProgramContext:
    >>>         return MyProgramContext()
    >>>
    >>>     # Implement other BraketSimulator interface methods
    >>>
    >>> parsed = MySimulator().parse_program(program)

    To register a simulator so the Amazon Braket SDK recognizes its name,
    the name and class must be added as an entry point for "braket.simulators".
    This is done by adding an entry to entry_points in the simulator package's setup.py:

    >>> entry_points = {
    >>>     "braket.simulators": [
    >>>         "backend_name = <backend_class>"
    >>>     ]
    >>> }
    """

    @abstractmethod
    def create_program_context(self) -> AbstractProgramContext:
        """Creates a new program context to handle translation of OpenQASM into a desired format."""

    def parse_program(self, program: OpenQASMProgram) -> AbstractProgramContext:
        """Parses an OpenQASM program and returns a program context.

        Args:
            program (OpenQASMProgram): The program to parse.

        Returns:
            AbstractProgramContext: The program context after the program has been parsed.
        """
        is_file = program.source.endswith(".qasm")
        interpreter = Interpreter(self.create_program_context())
        return interpreter.run(
            source=program.source,
            inputs=program.inputs,
            is_file=is_file,
        )


class BaseLocalSimulator(OpenQASMSimulator):
    def run(
        self, circuit_ir: Union[OpenQASMProgram, JaqcdProgram], *args, **kwargs
    ) -> GateModelTaskResult:
        """
        Simulate a circuit using either OpenQASM or Jaqcd.

        Args:
            circuit_ir (Union[OpenQASMProgram, JaqcdProgram]): Circuit specification.
            shots (int, optional): The number of shots to simulate. Default is 0, which
                performs a full analytical simulation.
            batch_size (int, optional): The size of the circuit partitions to contract,
                if applying multiple gates at a time is desired; see `StateVectorSimulation`.
                Must be a positive integer.
                Defaults to 1, which means gates are applied one at a time without any
                optimized contraction.

        Returns:
            GateModelTaskResult: object that represents the result

        Raises:
            ValueError: If result types are not specified in the IR or sample is specified
                as a result type when shots=0. Or, if StateVector and Amplitude result types
                are requested when shots>0.
        """
        if isinstance(circuit_ir, OpenQASMProgram):
            return self.run_openqasm(circuit_ir, *args, **kwargs)
        return self.run_jaqcd(circuit_ir, *args, **kwargs)

    def create_program_context(self) -> AbstractProgramContext:
        return ProgramContext()

    @abstractmethod
    def initialize_simulation(self, **kwargs) -> Simulation:
        """Initializes simulation with keyword arguments"""

    def _validate_ir_results_compatibility(
        self, results: list[Results], device_action_type
    ) -> None:
        """
        Validate that requested result types are valid for the simulator.

        Args:
            results (list[Results]): Requested result types.

        Raises:
            TypeError: If any the specified result types are not supported
        """
        if results:
            circuit_result_types_name = [result.__class__.__name__ for result in results]
            supported_result_types = self.properties.action[device_action_type].supportedResultTypes
            supported_result_types_name = [result.name for result in supported_result_types]
            for name in circuit_result_types_name:
                if name not in supported_result_types_name:
                    raise TypeError(
                        f"result type {name} is not supported by {self.__class__.__name__}"
                    )

    @staticmethod
    def _validate_shots_and_ir_results(
        shots: int,
        results: list[Results],
        qubit_count: int,
    ) -> None:
        """
        Validated that requested result types are valid for given shots and qubit count.

        Args:
            shots (int): Shots for the simulation.
            results (list[Results]): Specified result types.
            qubit_count (int): Number of qubits for the simulation.

        Raises:
            ValueError: If any of the requested result types are incompatible with the
                qubit count or number of shots.
        """
        if not shots:
            if not results:
                raise ValueError("Result types must be specified in the IR when shots=0")
            for rt in results:
                if rt.type in ["sample"]:
                    raise ValueError("sample can only be specified when shots>0")
                if rt.type == "amplitude":
                    BaseLocalSimulator._validate_amplitude_states(rt.states, qubit_count)
        elif shots and results:
            for rt in results:
                if rt.type in ["statevector", "amplitude", "densitymatrix"]:
                    raise ValueError(
                        "statevector, amplitude and densitymatrix result "
                        "types not available when shots>0"
                    )

    @staticmethod
    def _validate_amplitude_states(states: list[str], qubit_count: int) -> None:
        """
        Validate states in an amplitude result type are valid.

        Args:
            states (list[str]): List of binary strings representing quantum states.
            qubit_count (int): Number of qubits for the simulation.

        Raises:
            ValueError: If any of the states is not the correct size for the number of qubits.
        """
        for state in states:
            if len(state) != qubit_count:
                raise ValueError(
                    f"Length of state {state} for result type amplitude"
                    f" must be equivalent to number of qubits {qubit_count} in circuit"
                )

    @staticmethod
    def _translate_result_types(results: list[Results]) -> list[ResultType]:
        return [from_braket_result_type(result) for result in results]

    @staticmethod
    def _generate_results(
        results: list[Results],
        result_types: list[ResultType],
        simulation: Simulation,
    ) -> list[ResultTypeValue]:
        return [
            ResultTypeValue.construct(
                type=results[index],
                value=result_types[index].calculate(simulation),
            )
            for index in range(len(results))
        ]

    def _create_results_obj(
        self,
        results: list[dict[str, Any]],
        openqasm_ir: OpenQASMProgram,
        simulation: Simulation,
        measured_qubits: list[int] = None,
        mapped_measured_qubits: list[int] = None,
    ) -> GateModelTaskResult:
        return GateModelTaskResult.construct(
            taskMetadata=TaskMetadata(
                id=str(uuid.uuid4()),
                shots=simulation.shots,
                deviceId=self.DEVICE_ID,
            ),
            additionalMetadata=AdditionalMetadata(
                action=openqasm_ir,
            ),
            resultTypes=results,
            measurements=self._formatted_measurements(simulation, mapped_measured_qubits),
            measuredQubits=(measured_qubits or list(range(simulation.qubit_count))),
        )

    @staticmethod
    def _get_qubits_referenced(operations: list[Operation]) -> set[int]:
        return {target for operation in operations for target in operation.targets}

    @staticmethod
    def _validate_result_types_qubits_exist(
        targeted_result_types: list[TargetedResultType], qubit_count: int
    ) -> None:
        for result_type in targeted_result_types:
            targets = result_type.targets
            if targets and max(targets) >= qubit_count:
                raise ValueError(
                    f"Result type ({result_type.__class__.__name__})"
                    f" references invalid qubits {targets}"
                )

    def _validate_ir_instructions_compatibility(
        self,
        circuit_ir: Union[JaqcdProgram, Circuit],
        device_action_type: DeviceActionType,
    ) -> None:
        """
        Validate that requested IR instructions are valid for the simulator.

        Args:
            circuit_ir (Union[JaqcdProgram, Circuit]): IR for the simulator.

        Raises:
            TypeError: If any the specified result types are not supported
        """
        circuit_instruction_names = [
            instr.__class__.__name__.lower().replace("_", "") for instr in circuit_ir.instructions
        ]
        supported_instructions = frozenset(
            op.lower().replace("_", "")
            for op in self.properties.action[device_action_type].supportedOperations
        )
        no_noise = True
        for name in circuit_instruction_names:
            if name in _NOISE_INSTRUCTIONS:
                no_noise = False
                if name not in supported_instructions:
                    raise TypeError(
                        "Noise instructions are not supported by the state vector simulator "
                        "(by default). You need to use the density matrix simulator: "
                        'LocalSimulator("braket_dm").'
                    )
        if no_noise and _NOISE_INSTRUCTIONS.intersection(supported_instructions):
            warnings.warn(
                "You are running a noise-free circuit on the density matrix simulator. "
                "Consider running this circuit on the state vector simulator: "
                'LocalSimulator("default") for a better user experience.'
            )

    def _validate_input_provided(self, circuit: Circuit) -> None:
        """
        Validate that requested circuit has all input parameters provided.

        Args:
            circuit (Circuit): IR for the simulator.

        Raises:
            NameError: If any the specified input parameters are not provided
        """
        for instruction in circuit.instructions:
            possible_parameters = "_angle", "_angle_1", "_angle_2"
            for parameter_name in possible_parameters:
                param = getattr(instruction, parameter_name, None)
                if param is not None:
                    try:
                        float(param)
                    except TypeError:
                        missing_input = param.free_symbols.pop()
                        raise NameError(f"Missing input variable '{missing_input}'.")

    @staticmethod
    def _tensor_product_index_dict(
        observable: TensorProduct, func: Callable[[Observable], Any]
    ) -> dict[int, Any]:
        obj_dict = {}
        i = 0
        factors = list(observable.factors)
        total = len(factors[0].measured_qubits)
        while factors:
            if i >= total:
                factors.pop(0)
                if factors:
                    total += len(factors[0].measured_qubits)
            if factors:
                obj_dict[i] = func(factors[0])
            i += 1
        return obj_dict

    @staticmethod
    def _observable_hash(observable: Observable) -> Union[str, dict[int, str]]:
        if isinstance(observable, Hermitian):
            return str(hash(str(observable.matrix.tobytes())))
        elif isinstance(observable, TensorProduct):
            # Dict of target index to observable hash
            return BaseLocalSimulator._tensor_product_index_dict(
                observable, BaseLocalSimulator._observable_hash
            )
        else:
            return str(observable.__class__.__name__)

    @staticmethod
    def _map_circuit_to_contiguous_qubits(circuit: Union[Circuit, JaqcdProgram]) -> dict[int, int]:
        """
        Maps the qubits in operations and result types to contiguous qubits.

        Args:
            circuit (Union[Circuit, JaqcdProgram]): The circuit containing the operations and
            result types.

        Returns:
            dict[int, int]: Map of qubit index to corresponding contiguous index
        """
        circuit_qubit_set = BaseLocalSimulator._get_circuit_qubit_set(circuit)
        qubit_map = BaseLocalSimulator._contiguous_qubit_mapping(circuit_qubit_set)
        BaseLocalSimulator._map_circuit_qubits(circuit, qubit_map)
        return qubit_map

    @staticmethod
    def _get_circuit_qubit_set(circuit: Union[Circuit, JaqcdProgram]) -> set[int]:
        """
        Returns the set of qubits used in the given circuit.

        Args:
            circuit (Union[Circuit, JaqcdProgram]): The circuit from which to extract the qubit set.

        Returns:
            set[int]: The set of qubits used in the circuit.
        """
        if isinstance(circuit, Circuit):
            return circuit.qubit_set
        else:
            operations = [
                from_braket_instruction(instruction) for instruction in circuit.instructions
            ]
            if circuit.basis_rotation_instructions:
                operations.extend(
                    from_braket_instruction(instruction)
                    for instruction in circuit.basis_rotation_instructions
                )
            return BaseLocalSimulator._get_qubits_referenced(operations)

    @staticmethod
    def _map_circuit_qubits(circuit: Union[Circuit, JaqcdProgram], qubit_map: dict[int, int]):
        """
        Maps the qubits in operations and result types to contiguous qubits.

        Args:
            circuit (Circuit): The circuit containing the operations and result types.
            qubit_map (dict[int, int]): The mapping from qubits to their contiguous indices.

        Returns:
            Circuit: The circuit with qubits in operations and result types mapped
            to contiguous qubits.
        """
        if isinstance(circuit, Circuit):
            BaseLocalSimulator._map_circuit_instructions(circuit, qubit_map)
            BaseLocalSimulator._map_circuit_results(circuit, qubit_map)
        else:
            BaseLocalSimulator._map_jaqcd_instructions(circuit, qubit_map)
        return circuit

    @staticmethod
    def _map_circuit_instructions(circuit: Circuit, qubit_map: dict):
        """
        Maps the targets of each instruction in the circuit to the corresponding qubits in the
        qubit_map.

        Args:
            circuit (Circuit): The circuit containing the instructions.
            qubit_map (dict): A dictionary mapping original qubits to new qubits.
        """
        for ins in circuit.instructions:
            ins._targets = tuple([qubit_map[q] for q in ins.targets])

    @staticmethod
    def _map_circuit_results(circuit: Circuit, qubit_map: dict):
        """
        Maps the targets of each result in the circuit to the corresponding qubits in the qubit_map.

        Args:
            circuit (Circuit): The circuit containing the results.
            qubit_map (dict): A dictionary mapping original qubits to new qubits.
        """
        for result in circuit.results:
            if isinstance(result, (MultiTarget, OptionalMultiTarget)) and result.targets:
                result.targets = [qubit_map[q] for q in result.targets]

    @staticmethod
    def _map_jaqcd_instructions(circuit: JaqcdProgram, qubit_map: dict):
        """
        Maps the attributes of each instruction in the JaqcdProgram to the corresponding qubits in
        the qubit_map.

        Args:
            circuit (JaqcdProgram): The JaqcdProgram containing the instructions.
            qubit_map (dict): A dictionary mapping original qubits to new qubits.
        """
        for ins in circuit.instructions:
            BaseLocalSimulator._map_instruction_attributes(ins, qubit_map)

        if hasattr(circuit, "results") and circuit.results:
            for ins in circuit.results:
                BaseLocalSimulator._map_instruction_attributes(ins, qubit_map)

        if circuit.basis_rotation_instructions:
            for ins in circuit.basis_rotation_instructions:
                ins.target = qubit_map[ins.target]

    @staticmethod
    def _map_instruction_attributes(instruction, qubit_map: dict):
        """
        Maps the qubit attributes of an instruction from JaqcdProgram to the corresponding
        qubits in the qubit_map.

        Args:
            instruction: The Jaqcd instruction whose qubit attributes need to be mapped.
            qubit_map (dict): A dictionary mapping original qubits to new qubits.
        """
        if hasattr(instruction, "control"):
            instruction.control = qubit_map.get(instruction.control, instruction.control)

        if hasattr(instruction, "controls") and instruction.controls:
            instruction.controls = [qubit_map.get(q, q) for q in instruction.controls]

        if hasattr(instruction, "target"):
            instruction.target = qubit_map.get(instruction.target, instruction.target)

        if hasattr(instruction, "targets") and instruction.targets:
            instruction.targets = [qubit_map.get(q, q) for q in instruction.targets]

    @staticmethod
    def _contiguous_qubit_mapping(qubit_set: set[int]) -> dict[int, int]:
        """
        Maping of qubits to contiguous integers. The qubit mapping may be discontiguous or
        contiguous.

        Args:
            qubit_set (set[int]): List of qubits to be mapped.

        Returns:
            dict[int, int]: Dictionary where keys are qubits and values are contiguous integers.
        """
        return {q: i for i, q in enumerate(sorted(qubit_set))}

    @staticmethod
    def _formatted_measurements(
        simulation: Simulation, measured_qubits: Union[list[int], None] = None
    ) -> list[list[str]]:
        """Retrieves formatted measurements obtained from the specified simulation.

        Args:
            simulation (Simulation): Simulation to use for obtaining the measurements.
            measured_qubits (list[int] | None): The qubits that were measured.

        Returns:
            list[list[str]]: List containing the measurements, where each measurement consists
            of a list of measured values of qubits.
        """
        # Get the full measurements
        measurements = [
            list("{number:0{width}b}".format(number=sample, width=simulation.qubit_count))
            for sample in simulation.retrieve_samples()
        ]
        #  Gets the subset of measurements from the full measurements
        if measured_qubits is not None and measured_qubits != []:
            measured_qubits = np.array(measured_qubits)
            in_circuit_mask = measured_qubits < simulation.qubit_count
            measured_qubits_in_circuit = measured_qubits[in_circuit_mask]
            measured_qubits_not_in_circuit = measured_qubits[~in_circuit_mask]

            measurements_array = np.array(measurements)
            selected_measurements = measurements_array[:, measured_qubits_in_circuit]
            measurements = np.pad(
                selected_measurements, ((0, 0), (0, len(measured_qubits_not_in_circuit)))
            ).tolist()
        return measurements

    def run_openqasm(
        self,
        openqasm_ir: OpenQASMProgram,
        shots: int = 0,
        *,
        batch_size: int = 1,
    ) -> GateModelTaskResult:
        """Executes the circuit specified by the supplied `circuit_ir` on the simulator.

        Args:
            openqasm_ir (Program): ir representation of a braket circuit specifying the
                instructions to execute.
            shots (int): The number of times to run the circuit.
            batch_size (int): The size of the circuit partitions to contract,
                if applying multiple gates at a time is desired; see `StateVectorSimulation`.
                Must be a positive integer.
                Defaults to 1, which means gates are applied one at a time without any
                optimized contraction.
        Returns:
            GateModelTaskResult: object that represents the result

        Raises:
            ValueError: If result types are not specified in the IR or sample is specified
                as a result type when shots=0. Or, if StateVector and Amplitude result types
                are requested when shots>0.
        """
        circuit = self.parse_program(openqasm_ir).circuit
        qubit_map = BaseLocalSimulator._map_circuit_to_contiguous_qubits(circuit)
        qubit_count = circuit.num_qubits
        measured_qubits = circuit.measured_qubits
        mapped_measured_qubits = (
            [qubit_map[q] for q in measured_qubits] if measured_qubits else None
        )

        self._validate_ir_results_compatibility(
            circuit.results,
            device_action_type=DeviceActionType.OPENQASM,
        )
        self._validate_ir_instructions_compatibility(
            circuit,
            device_action_type=DeviceActionType.OPENQASM,
        )
        self._validate_input_provided(circuit)
        BaseLocalSimulator._validate_shots_and_ir_results(shots, circuit.results, qubit_count)

        results = circuit.results

        simulation = self.initialize_simulation(
            qubit_count=qubit_count, shots=shots, batch_size=batch_size
        )
        operations = circuit.instructions
        simulation.evolve(operations)

        if not shots:
            result_types = BaseLocalSimulator._translate_result_types(results)
            BaseLocalSimulator._validate_result_types_qubits_exist(
                [
                    result_type
                    for result_type in result_types
                    if isinstance(result_type, TargetedResultType)
                ],
                qubit_count,
            )
            results = BaseLocalSimulator._generate_results(
                circuit.results,
                result_types,
                simulation,
            )
        else:
            simulation.evolve(circuit.basis_rotation_instructions)

        return self._create_results_obj(
            results, openqasm_ir, simulation, measured_qubits, mapped_measured_qubits
        )

    def run_jaqcd(
        self,
        circuit_ir: JaqcdProgram,
        qubit_count: Any = None,
        shots: int = 0,
        *,
        batch_size: int = 1,
    ) -> GateModelTaskResult:
        """Executes the circuit specified by the supplied `circuit_ir` on the simulator.

        Args:
            circuit_ir (Program): ir representation of a braket circuit specifying the
                instructions to execute.
            qubit_count (Any): Unused parameter; in signature for backwards-compatibility
            shots (int): The number of times to run the circuit.
            batch_size (int): The size of the circuit partitions to contract,
                if applying multiple gates at a time is desired; see `StateVectorSimulation`.
                Must be a positive integer.
                Defaults to 1, which means gates are applied one at a time without any
                optimized contraction.
        Returns:
            GateModelTaskResult: object that represents the result

        Raises:
            ValueError: If result types are not specified in the IR or sample is specified
                as a result type when shots=0. Or, if StateVector and Amplitude result types
                are requested when shots>0.
        """
        if qubit_count is not None:
            warnings.warn(
                f"qubit_count is deprecated for {type(self).__name__} and can be set to None"
            )
        self._validate_ir_results_compatibility(
            circuit_ir.results,
            device_action_type=DeviceActionType.JAQCD,
        )
        self._validate_ir_instructions_compatibility(
            circuit_ir,
            device_action_type=DeviceActionType.JAQCD,
        )
        qubit_map = BaseLocalSimulator._map_circuit_to_contiguous_qubits(circuit_ir)
        qubit_count = len(qubit_map)
        BaseLocalSimulator._validate_shots_and_ir_results(shots, circuit_ir.results, qubit_count)

        operations = [
            from_braket_instruction(instruction) for instruction in circuit_ir.instructions
        ]

        if shots > 0 and circuit_ir.basis_rotation_instructions:
            operations.extend(
                from_braket_instruction(instruction)
                for instruction in circuit_ir.basis_rotation_instructions
            )

        simulation = self.initialize_simulation(
            qubit_count=qubit_count, shots=shots, batch_size=batch_size
        )
        simulation.evolve(operations)

        results = []

        if not shots and circuit_ir.results:
            result_types = BaseLocalSimulator._translate_result_types(circuit_ir.results)
            BaseLocalSimulator._validate_result_types_qubits_exist(
                [
                    result_type
                    for result_type in result_types
                    if isinstance(result_type, TargetedResultType)
                ],
                qubit_count,
            )
            results = self._generate_results(
                circuit_ir.results,
                result_types,
                simulation,
            )

        return self._create_results_obj(results, circuit_ir, simulation)
