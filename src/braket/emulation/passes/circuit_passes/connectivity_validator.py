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

from networkx import DiGraph, complete_graph, from_dict_of_lists

from braket.circuits import Circuit
from braket.circuits.compiler_directives import StartVerbatimBox
from braket.circuits.gate import Gate
from braket.emulation.passes import ValidationPass
from braket.registers.qubit_set import QubitSet


class ConnectivityValidator(ValidationPass):
    def __init__(
        self,
        connectivity_graph: dict[int, Iterable[int]] | DiGraph | None = None,
        fully_connected: bool = False,
        num_qubits: int | None = None,
        qubit_labels: Iterable[int] | QubitSet | None = None,
        directed: bool = True,
    ):
        """
        A ConnectivityValidator instance takes in a qubit connectivity graph and validates that
        a circuit that uses verbatim circuits makes valid hardware qubit references in single
        and two-qubit gate operations.

        Args:
            connectivity_graph (dict[int, Iterable[int]], DiGraph | None):
                Either a sparse matrix or DiGraph representation of the device connectivity.
                Can be None if fully_connected is true.

            fully_connected (bool): If true, the all qubits in the device are connected.

            num_qubits (int | None): The number of qubits in the device; if fully_connected is
                True, create a complete graph with num_qubits nodes; ignored if
                connectivity_graph is provided and fully_connected if False.

            qubit_labels (Iterable[int], QubitSet | None): A set of qubit labels; if
                fully_connected is True, the qubits_labels are used as nodes of a fully connected
                topology; ignored if connectivity_graph is provided and fully_connected if False.

            directed (bool): Denotes if the connectivity graph is directed or undirected. If
                the connectivity graph is undirected, this constructor attempts to fill in any
                missing back edges.

        Raises:
            ValueError: If the inputs do not correctly yield a connectivity graph; i.e.
            fully_connected is true but neither/both num qubits and qubit labels are defined
            or a valid DiGraph or dict representation of a connectivity graph is not provided.
        """

        if not ((connectivity_graph is not None) ^ fully_connected):
            raise ValueError(
                "Either the connectivity_graph must be provided OR fully_connected must be True\
                    (not both)."
            )

        if fully_connected:
            if not ((num_qubits is None) ^ (qubit_labels is None)):
                raise ValueError(
                    "Either num_qubits or qubit_labels (NOT both) must be \
                        provided if fully_connected is True."
                )
            self._connectivity_graph = complete_graph(
                num_qubits or qubit_labels, create_using=DiGraph()
            )
        elif not isinstance(connectivity_graph, DiGraph):
            try:
                self._connectivity_graph = from_dict_of_lists(
                    connectivity_graph, create_using=DiGraph()
                )
            except Exception as e:
                raise ValueError(
                    f"connectivity_graph must be a valid DiGraph or a dictionary\
                        mapping integers (nodes) to a list of integers (adjancency lists): {e}"
                ) from e
        else:
            self._connectivity_graph = connectivity_graph

        if not directed:
            for edge in self._connectivity_graph.edges:
                self._connectivity_graph.add_edge(edge[1], edge[0])

    def _graph_node_type(self) -> type:
        return type(next(iter(self._connectivity_graph.nodes)))

    def validate(self, circuit: Circuit) -> None:
        """
        Verifies that any verbatim box in a circuit is runnable with respect to the
        device connectivity definied by this validator. If any sub-circuit of the
        input circuit is verbatim, we validate the connectivity of all gate operations
        in the circuit.

        Args:
            circuit (Circuit): The Braket circuit whose gate operations to
                validate.

        Raises:
            ValueError: If a hardware qubit reference does not exist in the connectivity graph.
        """
        # If any of the instructions are in verbatim mode, all qubit references
        # must point to hardware qubits. Otherwise, this circuit need not be validated.
        if not any(
            isinstance(instruction.operator, StartVerbatimBox)
            for instruction in circuit.instructions
        ):
            return
        for idx in range(len(circuit.instructions)):
            instruction = circuit.instructions[idx]
            if isinstance(instruction.operator, Gate):
                if (
                    instruction.operator.qubit_count == 2
                ):  # Assuming only maximum 2-qubit native gates are supported
                    self._validate_instruction_connectivity(instruction.control, instruction.target)
                else:
                    # just check that the target qubit exists in the connectivity graph
                    target_qubit = instruction.target[0]
                    if self._graph_node_type()(int(target_qubit)) not in self._connectivity_graph:
                        raise ValueError(
                            f"Qubit {target_qubit} does not exist in the device topology."
                        )

    def _validate_instruction_connectivity(
        self, control_qubits: QubitSet, target_qubits: QubitSet
    ) -> None:
        """
        Checks if a two-qubit instruction is valid based on this validator's connectivity
        graph.

        Args:
            control_qubits (QubitSet): The control qubits used in this multi-qubit
                operation.
            target_qubits (QubitSet): The target qubits of this operation. For many gates,
                both the control and target are stored in "target_qubits", so we may
                see target_qubits have length 2.

        Raises:
            ValueError: If any two-qubit gate operation uses a qubit edge that does not exist
            in the qubit connectivity graph.
        """
        # Create edges between each of the target qubits
        gate_connectivity_graph = DiGraph()
        # Create an edge from each control bit to each target qubit
        if len(control_qubits) == 1 and len(target_qubits) == 1:
            gate_connectivity_graph.add_edge(control_qubits[0], target_qubits[0])
        elif len(control_qubits) == 0 and len(target_qubits) == 2:
            gate_connectivity_graph.add_edges_from([
                (target_qubits[0], target_qubits[1]),
                (target_qubits[1], target_qubits[0]),
            ])
        else:
            raise ValueError("Unrecognized qubit targetting setup for a 2 qubit gate.")
        # Check that each edge exists in this validator's connectivity graph
        for edge in gate_connectivity_graph.edges:
            typed_edge = (
                self._graph_node_type()(int(edge[0])),
                self._graph_node_type()(int(edge[1])),
            )
            if not self._connectivity_graph.has_edge(*typed_edge):
                raise ValueError(
                    f"{typed_edge[0]} is not connected to qubit {typed_edge[1]} in this device."
                )
