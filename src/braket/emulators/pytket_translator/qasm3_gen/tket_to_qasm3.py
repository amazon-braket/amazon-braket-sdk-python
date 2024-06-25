from braket.emulators.pytket_translator import PYTKET_TO_QASM
from pytket.circuit import Circuit, OpType, Command, Node
from sympy import Expr, pi, Symbol
from typing import Dict, Union, List, Set, Optional
from dataclasses import dataclass
from functools import singledispatchmethod
from braket.emulators.pytket_translator.qasm3_gen.qasm_context import QasmContext
from braket.emulators.pytket_translator.qasm3_gen.qasm_writer import BasicQasmWriter


@dataclass
class Qasm3:
    program: str
    
    
def tket_to_qasm3(
    circuit: Circuit, 
    input_parameters: Dict[str, str]=dict(), 
    gate_overrides: Dict[OpType, str]=dict()
) -> str: 
    ticket_visitor = TketCircuitVisitor(QasmContext(input_parameters), gate_overrides)
    ticket_visitor.walk_circuit(circuit)
    writer = BasicQasmWriter(ticket_visitor.context)
    return writer.get_program()

class TketCircuitVisitor: 
    def __init__(self, context, gate_overrides: Dict[OpType, str]=dict()):
        self.context = context
        self.gate_overrides = gate_overrides
        self._measured_nodes: Set[Node] = set()
        
        
    def walk_circuit(self, circuit: Circuit):
        self.context.set_num_bits(len(circuit.bits))
        for command in circuit:
            self._visit_command(command)

    def _visit_command(self, command: Command):
        op = command.op
        self._validate_args_not_measured(command.args)
        optype = op.type
        if optype == OpType.CircBox:
            self._visit_box(command, optype)
        elif optype == OpType.Measure:
            self._visit_measure(command, optype)
        else:
            self._visit_gate(command, optype)
        
    def _validate_args_not_measured(self, args):
        for arg in args:
            if arg in self._measured_nodes:
                raise ValueError(
                    "Circuit QASM cannot be generated as circuit contains midcircuit "
                    f"measurements on qubit: {arg}"
                )        
    
    def _visit_box(self, command: Command, optype):
        circ = command.op.get_circuit()
        for command in circ:
            self._visit_command(command)
    
    def _visit_measure(self, command: Command, optype):
        qubit_node = command.args[0]
        qubit = qubit_node.index[0]
        cbit = command.args[1].index[0]
        self.context.add_measurement(qubit, cbit)
        self._measured_nodes.add(qubit_node)
    
    
    def _visit_gate(self, command: Command, optype): 
        """
        Check to see if this operation is a gate known by OpenQASM3.0; if it is, retrieve the appropriate translation
        and add the operation to the context. 
        """
        gate_name: str 
        if optype in self.gate_overrides:
            gate_name = self.gate_overrides[optype]
        elif optype in PYTKET_TO_QASM:
            gate_name = PYTKET_TO_QASM[optype]
        else:
            raise ValueError(f"Operation {optype} cannot be translated to OpenQASM3.0.")
        
        qubits = command.args
        params = command.op.params
     
        
        #Look for any free parameters and add them to the context for initialization
        for param in params:
            if isinstance(param, Expr):
                for symbol in param.free_symbols:
                    if symbol != pi:
                        self.context.add_parameter(str(symbol), "float")
        params = self._gate_angles_in_radians(params)
        qubits = [q.index[0] for q in qubits]
        self.context.add_gate(gate_name, params, qubits)

    def _gate_angles_in_radians(self, params):
        return [self._tau_to_radians(param) for param in params]
    
    def _tau_to_radians(self, arg: Union[float, Expr, Symbol]):
        return pi * arg
    