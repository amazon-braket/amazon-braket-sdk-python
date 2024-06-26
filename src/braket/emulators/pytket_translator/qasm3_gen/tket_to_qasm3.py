from typing import Dict, List, Set, Union

from pytket.circuit import Circuit, Command, Node, OpType, UnitID
from sympy import Expr, Symbol, pi

from braket.emulators.pytket_translator.translations import PYTKET_TO_QASM
from braket.emulators.pytket_translator.qasm3_gen.qasm_context import QasmContext
from braket.emulators.pytket_translator.qasm3_gen.qasm_writer import BasicQasmWriter


def tket_to_qasm3(
    circuit: Circuit,
    input_parameters: Dict[str, str] = dict(),
    gate_overrides: Dict[OpType, str] = dict(),
) -> str:
    """
    Converts a Pytket circuit to an OpenQASM 3.0 string.

    Args:
        circuit (Circuit): The Pytket circuit to translate.
        input_parameters (Dict[str, str]): Program parameters to declare at the beginning
            of the OpenQASM 3.0 program.
        gate_overrides (Dict[OpType, str]): Gate names overrides that take precedence
            over the default OpenQASM 3.0 gate names.

    Returns:
        str: An OpenQASM 3.0 program string.
    """
    ticket_visitor = TketCircuitVisitor(QasmContext(input_parameters), gate_overrides)
    ticket_visitor.walk_circuit(circuit)
    writer = BasicQasmWriter(ticket_visitor.context)
    return writer.get_program()


class TketCircuitVisitor:
    def __init__(self, context, gate_overrides: Dict[OpType, str] = dict()):
        self.context = context
        self.gate_overrides = gate_overrides
        self._measured_nodes: Set[Node] = set()

    def walk_circuit(self, circuit: Circuit) -> None:
        """
        Visits all the commands in the circuit and processes them by their
        operation type.

        Args:
            circuit (Circuit): The Pytket circuit to perform the walk on.
        """
        self.context.set_num_bits(len(circuit.bits))
        for command in circuit:
            self._visit_command(command)

    def _visit_command(self, command: Command) -> None:
        """
        Calls the appropriate visit function based on the operation type of the given
        command.

        Args:
            command (Command): The circuit instruction to process.
        """
        op = command.op
        self._validate_args_not_measured(command.args)
        optype = op.type
        if optype == OpType.CircBox:
            self._visit_box(command)
        elif optype == OpType.Measure:
            self._visit_measure(command)
        else:
            self._visit_gate(command, optype)

    def _validate_args_not_measured(self, args: List[UnitID]) -> None:
        """
        Checks that all qubits used in the instruction have not already been measured.

        Args:
            args (List[UnitID]): List of targets to validate.
        """
        for arg in args:
            if arg in self._measured_nodes:
                raise ValueError(
                    "Circuit QASM cannot be generated as circuit contains midcircuit "
                    f"measurements on qubit: {arg}"
                )

    def _visit_box(self, command: Command) -> None:
        """
        Visits all the instructions inside a Pytket boxed circuit.

        Args:
            command (Command): Contains the instructions of the boxed circuit.
        """
        circ = command.op.get_circuit()
        for command in circ:
            self._visit_command(command)

    def _visit_measure(self, command: Command) -> None:
        """
        Adds a measure instruction to the QASM context being built.

        Args:
            command (Command): Specifies the classical and qubit indices targeted
                in this measurement instruction.
        """
        qubit_node = command.args[0]
        qubit = qubit_node.index[0]
        cbit = command.args[1].index[0]
        self.context.add_measurement(qubit, cbit)
        self._measured_nodes.add(qubit_node)

    def _visit_gate(self, command: Command, optype: OpType) -> None:
        """
        Check to see if this operation is a gate known by OpenQASM3.0; if it is,
        retrieve the appropriate translation and add the operation to the context.

        Args:
            command (Command): The Pytket instruction containing the gate targets.
            optype (OpType): Specifies the gate operation being used in this
                instruction.
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

        # Look for any free parameters and add them to the context for initialization
        for param in params:
            if isinstance(param, Expr):
                for symbol in param.free_symbols:
                    if symbol != pi:
                        self.context.add_parameter(str(symbol), "float")
        params = self._gate_angles_in_radians(params)
        qubits = [q.index[0] for q in qubits]
        self.context.add_gate(gate_name, params, qubits)

    def _gate_angles_in_radians(self, params: List[Union[Expr, float]]) -> List[Expr]:
        """
        Converts a list of expressions or values in half-angle units to radians.

        Args:
            params (List[Union[Expr, float]]): List of angle arguments to convert
                to radians.

        Returns:
            List[Expr]: A list of gate angle arguments with radian units.
        """
        return [self._tau_to_radians(param) for param in params]

    def _tau_to_radians(self, arg: Union[float, Expr, Symbol]) -> Expr:
        """
        Converts expressions from half-angle units to radians.

        Args:
            arg (Union[float, Expr, Symbol]): expression to convert.

        Returns:
            Expr: Returns an expression with radian units.
        """
        return pi * arg
