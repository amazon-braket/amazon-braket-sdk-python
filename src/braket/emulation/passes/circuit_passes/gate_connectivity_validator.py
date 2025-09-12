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

from collections.abc import Iterable
from typing import Any

from networkx import DiGraph

from braket.circuits.circuit import Circuit
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.circuits.gate import Gate
from braket.emulation.passes import ValidationPass
from braket.registers.qubit_set import QubitSet


class GateConnectivityValidator(ValidationPass):
    def __init__(
        self,
        gate_connectivity_graph: dict[tuple[Any, Any], Iterable[str]] | DiGraph,
        directed: bool = True,
    ):
        """
        A GateConnectivityValidator instance takes in a gate connectivity graph and validates that
        a circuit that uses verbatim circuits makes valid hardware gate references in single
        and two-qubit gate operations on the corresponding edges.

        Args:
            gate_connectivity_graph (dict[tuple[Any, Any], Iterable[str]], DiGraph, optional):
                Either a sparse matrix or DiGraph representation of the supported gates for the
                edges on the device.
            directed (bool): Denotes if the connectivity graph is directed or undirected. If
                the connectivity graph is undirected, this constructor attempts to fill in any
                missing back edges.

        Raises:
            ValueError: If the inputs do not correctly yield a gate connectivity graph.
        """
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
                # check that the supported gate sets are identical
                elif (
                    self._gate_connectivity_graph[u][v]["supported_gates"]
                    != self._gate_connectivity_graph[v][u]["supported_gates"]
                ):
                    raise ValueError(
                        f"Connectivity Graph marked as undirected\
                                but edges ({u}, {v}) and ({v}, {u}) have different supported\
                                gate sets."
                    )

    def _graph_node_type(self) -> type:
        return type(next(iter(self._gate_connectivity_graph.nodes)))

    def validate(self, circuit: Circuit) -> None:
        """
        Verifies that any multiqubit gates used within a verbatim box are supported
        by the devices gate connectivity defined by this criteria.

        Args:
            circuit (Circuit): The circuit whose gate instructions need to be validated
                against this validator's gate connectivity graph.

        Raises:
            ValueError if any of the gate operations use qubits or qubit edges that don't exist
            in the qubit connectivity graph or the gate operation is not supported by the edge.
        """

        in_verbatim = False
        for instruction in circuit.instructions:
            operator = instruction.operator
            if isinstance(operator, Gate) and in_verbatim:
                self._validate_gate_in_verbatim(instruction)
            elif isinstance(operator, StartVerbatimBox):
                if in_verbatim:
                    raise ValueError("Already in verbatim box")
                in_verbatim = True
            elif isinstance(operator, EndVerbatimBox):
                if not in_verbatim:
                    raise ValueError("Already outside of verbatim box")
                in_verbatim = False

        # Check for unclosed verbatim box
        if in_verbatim:
            raise ValueError("No end verbatim box found for the circuit.")

    def _validate_gate_in_verbatim(self, instruction: Any) -> None:
        """
        Validate a gate instruction within a verbatim box.

        Args:
            instruction: The gate instruction to validate

        Raises:
            ValueError: If the gate is not supported by the device topology
        """
        if (
            instruction.operator.qubit_count == 2
        ):  # Assuming only maximum 2-qubit native gates are supported
            self._validate_instruction_connectivity(
                instruction.operator.name, instruction.control, instruction.target
            )
        else:
            # just check that the target qubit exists in the connectivity graph
            target_qubit = instruction.target[0]
            if self._graph_node_type()(int(target_qubit)) not in self._gate_connectivity_graph:
                raise ValueError(f"Qubit {target_qubit} does not exist in the device topology.")

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

        e = (self._graph_node_type()(int(e[0])), self._graph_node_type()(int(e[1])))

        # Check that each edge exists in this validator's connectivity graph
        if self._gate_connectivity_graph.has_edge(*e):
            supported_gates = self._gate_connectivity_graph[e[0]][e[1]]["supported_gates"]
        else:
            raise ValueError(f"{e[0]} is not connected to {e[1]} on this device.")

        supported_gates = [gate.lower() for gate in supported_gates]
        if gate_name.lower() not in supported_gates:
            raise ValueError(
                f"Qubit pair ({e[0]}, {e[1]}) does not support gate {gate_name} on this device."
            )
