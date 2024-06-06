from braket.emulators.emulator_passes import EmulatorPass
from braket.circuits import Circuit
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.emulators.pytket_translator import PytketProgramContext
from braket.circuits.serialization import IRType
from pytket.mapping import LexiLabellingMethod, LexiRouteRoutingMethod, MappingManager
from pytket.architecture import Architecture
from typing import Union, Dict
from collections.abc import Iterable
from networkx import DiGraph
from braket.default_simulator.openqasm.interpreter import Interpreter
from functools import singledispatchmethod

class LexiRoutingPass(EmulatorPass):
    def __init__(self, hardware_topology:Union[Dict[int, Iterable[int]], DiGraph]):
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
    def run_pass(self, task_specification):
        raise NotImplementedError(f"LexiRoutingPass does not support task specification type: {type(task_specification)}")
    
    
    @run_pass.register
    def _(self, task_specification: Circuit) -> Circuit:
        open_qasm_program = task_specification.to_ir(ir_type=IRType.OPENQASM)
        mapped_open_qasm_program = self.run_pass(open_qasm_program)
        resulting_circuit = Circuit.from_ir(mapped_open_qasm_program)
        return resulting_circuit
    
    @run_pass.register
    def _(self, task_specification: OpenQasmProgram) -> OpenQasmProgram:
        pytket_circuit = Interpreter(PytketProgramContext()).build_circuit(task_specification.source)
        self._mapping_manager.route_circuit(pytket_circuit, [self._lexi_label, self._lexi_route])
        #TODO convert back to openqasm
        return pytket_circuit 