from braket.emulators.pytket_translator import PYTKET_TO_QASM
from pytket.circuit import Circuit, OpType, Node
from sympy import Expr, pi, Symbol
from typing import Dict, Union, List, Set, Optional
from dataclasses import dataclass
from functools import singledispatchmethod
from braket.emulators.pytket_translator.qasm3_gen.qasm_context import QasmContext



@dataclass
class Qasm3:
    program: str
    
    
def tket_to_qasm3(
    circuit: Circuit, 
    input_parameters: Dict[str, str]=None, 
    gate_overrides: Dict[OpType, str]=None
) -> Qasm3: 
    ticket_visitor = TketCircuitVisitor(QasmContext(input_parameters), gate_overrides)
    ticket_visitor.walk_circuit(circuit)
    return ticket_visitor.context

class TketCircuitVisitor: 
    def __init__(self, context, gate_overrides):
        self.context = context
        self.gate_overrides = gate_overrides
        self._measured_nodes: Set[Node] = set()
        
        
    def walk_circuit(self, circuit: Circuit):
        self.context.set_num_bits(len(circuit.bits))
        for command in circuit:
            self._visit_command(command)

    def _visit_command(self, command: Node):
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
                        
    
    def _visit_box(self, command: Node, optype):
        circ = command.op.get_circuit()
        for command in circ:
            self._visit_command(command)
    
    def _visit_measure(self, command: Node, optype):
        qubit_node = command.args[0]
        qubit = qubit_node.index[0]
        cbit = command.args[1].index
        self.context.add_measurement(qubit, cbit)
        self._measured_nodes.add(qubit_node)
    
    # @_visit_op.register
    # def _(self, command: Node, optype: OpType.CustomGate):
    #     gate_name = command.op.gate.name
    #     if gate_name not in SUPPORTED_CUSTOM_GATES:
    #         raise ValueError(f"Encountered unsupported custom gate {gate_name}")
    #     self._visit_gate(gate_name, command.op.params, command.args)
    
    
    def _visit_gate(self, command: Node, optype): 
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
        print("args: ", params)
        print("qubits: ", qubits)

        params = self._gate_angles_in_radians(params)
        qubits = [q.index[0] for q in qubits]
        self.context.add_gate(gate_name, params, qubits)
        
        
        
        
    def _gate_angles_in_radians(self, params):
        return [self._tau_to_radians(param) for param in params]
    
    def _tau_to_radians(self, arg: Union[float, Expr, Symbol]):
        return pi * arg
    