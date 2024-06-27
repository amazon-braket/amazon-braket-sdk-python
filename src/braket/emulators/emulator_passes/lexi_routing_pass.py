from collections.abc import Iterable
from functools import singledispatchmethod
from typing import Dict, Union

from networkx import DiGraph
from pytket import Circuit as PytketCircuit
from pytket.architecture import Architecture
from pytket.mapping import LexiLabellingMethod, LexiRouteRoutingMethod, MappingManager

from braket.circuits import Circuit
from braket.circuits.serialization import IRType
from braket.default_simulator.openqasm.interpreter import Interpreter
from braket.emulators.emulator_passes import EmulatorPass
from braket.emulators.pytket_translator import PytketProgramContext, PytketProgramTranslation, tket_to_qasm3
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.circuits.compiler_directives import StartVerbatimBox


class LexiRoutingPass(EmulatorPass):
    def __init__(self, hardware_topology: Union[Dict[int, Iterable[int]], DiGraph]):
        super().__init__()
        self._mapping_manager = MappingManager(self._get_architecture(hardware_topology))
        self._lexi_label = LexiLabellingMethod()
        self._lexi_route = LexiRouteRoutingMethod()

    def _get_architecture(self, hardware_topology: Union[Dict[int, Iterable[int]], DiGraph]):
        if isinstance(hardware_topology, dict):
            edge_list = [(q1, q2) for q1, edges in hardware_topology.items() for q2 in edges]
        elif isinstance(hardware_topology, DiGraph):
            edge_list = list(hardware_topology.edges)

        return Architecture(edge_list)

    @singledispatchmethod
    def run(self, task_specification):
        raise NotImplementedError(
            f"LexiRoutingPass does not support task specification type: {type(task_specification)}"
        )

    @run.register
    def _(self, task_specification: Circuit) -> Circuit:
        has_verbatim = any([isinstance(instruction.operator, StartVerbatimBox) \
                        for instruction in task_specification.instructions])
        
        #If the circuit has a verbatim box, don't perform circuit mapping. 
        if has_verbatim:
            return task_specification
        
        open_qasm_program = task_specification.to_ir(ir_type=IRType.OPENQASM)
        mapped_open_qasm_program = self.run(open_qasm_program)
        resulting_circuit = Circuit.from_ir(mapped_open_qasm_program)
        return resulting_circuit

    @run.register
    def _(self, task_specification: OpenQasmProgram, is_verbatim=False) -> OpenQasmProgram:
        pytket_translation: PytketProgramTranslation = Interpreter(PytketProgramContext()).build_circuit(
            task_specification.source
        )
        if pytket_translation.is_verbatim:
            return task_specification
        
        pytket_circuit = pytket_translation.circuit
        pytket_circuit = self.run(pytket_circuit)
        open_qasm_program_string = tket_to_qasm3(pytket_circuit)
        return OpenQasmProgram(source=open_qasm_program_string)

    @run.register
    def _(self, task_specification: PytketCircuit, is_verbatim=False) -> PytketCircuit:
        self._mapping_manager.route_circuit(
            task_specification, [self._lexi_label, self._lexi_route]
        )
        return task_specification
