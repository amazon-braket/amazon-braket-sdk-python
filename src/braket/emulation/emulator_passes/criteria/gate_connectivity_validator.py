from typing import Any, Dict, Iterable, Tuple, Union

from networkx import DiGraph
from networkx.utils import graphs_equal

from braket.circuits.circuit import Circuit
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.circuits.gate import Gate
from braket.emulation.emulator_passes.criteria.validation_pass import ValidationPass
from braket.registers.qubit_set import QubitSet


class GateConnectivityValidator(ValidationPass[Circuit]):
    def __init__(
        self,
        gate_connectivity_graph: Union[Dict[Tuple[Any, Any], Iterable[str]], DiGraph],
        directed=True,
    ):
        super().__init__()
        if isinstance(gate_connectivity_graph, dict):
            self._gate_connectivity_graph = DiGraph()
            for (u, v), supported_gates in gate_connectivity_graph.items():
                self._gate_connectivity_graph.add_edge(u, v, supported_gates=supported_gates)
        elif isinstance(gate_connectivity_graph, DiGraph):
            self._gate_connectivity_graph = gate_connectivity_graph
        else:
            raise TypeError(
                "Gate_connectivity_graph must either be a dictionary of edges mapped to \
supported gates lists, or a DiGraph with supported gates \
provided as edge attributes."
            )

        if not directed:
            """
            Add reverse edges and check that any supplied reverse edges have
            identical supported gate sets to their corresponding forwards edge.
            """
            for u, v in self._gate_connectivity_graph.edges:
                back_edge = (v, u)
                if back_edge not in self._gate_connectivity_graph.edges:
                    supported_gates = self._gate_connectivity_graph[u][v]["supported_gates"]
                    self._gate_connectivity_graph.add_edge(
                        *back_edge, supported_gates=supported_gates
                    )
                else:
                    # check that the supported gate sets are identical
                    if (
                        self._gate_connectivity_graph[u][v]["supported_gates"]
                        != self._gate_connectivity_graph[v][u]["supported_gates"]
                    ):
                        raise ValueError(
                            f"Connectivity Graph marked as undirected\
                                but edges ({u}, {v}) and ({v}, {u}) have different supported\
                                gate sets."
                        )

    def validate(self, program: Circuit) -> None:
        """
        Verifies that any multiqubit gates used within a verbatim box are supported
        by the devices gate connectivity defined by this criteria.

        Args:
            program (Circuit): The circuit whose gate instructions need to be validated
                against this validator's gate connectivity graph.

        Raises:
            ValueError if any of the gate operations use qubits or qubit edges that don't exist
            in the qubit connectivity graph or the gate operation is not supported by the edge.
        """
        for idx in range(len(program.instructions)):
            instruction = program.instructions[idx]
            if isinstance(instruction.operator, StartVerbatimBox):
                idx += 1
                while idx < len(program.instructions) and not isinstance(
                    program.instructions[idx].operator, EndVerbatimBox
                ):
                    instruction = program.instructions[idx]
                    if isinstance(instruction.operator, Gate):
                        if (
                            instruction.operator.qubit_count == 2
                        ):  # Assuming only maximum 2-qubit native gates are supported
                            self._validate_instruction_connectivity(
                                instruction.operator.name, instruction.control, instruction.target
                            )
                        else:
                            # just check that the target qubit exists in the connectivity graph
                            target_qubit = instruction.target[0]
                            if target_qubit not in self._gate_connectivity_graph:
                                raise ValueError(
                                    f"Qubit {target_qubit} does not exist in the device topology."
                                )
                    idx += 1
                idx += 1

    def _validate_instruction_connectivity(
        self, gate_name: str, control_qubits: QubitSet, target_qubits: QubitSet
    ) -> None:
        """
        Checks if a specific is able to be applied to the control and target qubits based
        on this validator's gate connectivity graph.

        Args:
            gate_name (str): The name of the gate being applied.
            control_qubits (QubitSet): The set of control qubits used by this gate operation.
            target_qubits (QubitSet): The set of target qubits used by this gate operation.

        Raises:
            ValueError if the gate operation is not possible on the qubit connectivity graph.
        """
        # Create edges between each of the target qubits
        if len(control_qubits) == 1 and len(target_qubits) == 1:
            e = (control_qubits[0], target_qubits[0])
        elif len(control_qubits) == 0 and len(target_qubits) == 2:
            e = (target_qubits[0], target_qubits[1])
        else:
            raise ValueError("Unrecognized qubit targetting setup for a 2 qubit gate.")

        # Check that each edge exists in this validator's connectivity graph
        if not self._gate_connectivity_graph.has_edge(*e):
            raise ValueError(f"{e[0]} is not connected to {e[1]} on this device.")
        supported_gates = self._gate_connectivity_graph[e[0]][e[1]]["supported_gates"]
        if gate_name not in supported_gates:
            raise ValueError(
                f"Qubit pair ({e[0]}, {e[1]}) does not support gate {gate_name} on this device."
            )

    def __eq__(self, other: ValidationPass) -> bool:
        return isinstance(other, GateConnectivityValidator) and graphs_equal(
            self._gate_connectivity_graph, other._gate_connectivity_graph
        )
