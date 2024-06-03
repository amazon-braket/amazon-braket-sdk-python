from braket.emulators.criteria import EmulatorCriterion
from networkx import DiGraph, complete_graph, from_dict_of_lists
from networkx.utils import graphs_equal
from typing import Union, Dict
from collections.abc import Iterable
from braket.circuits import Circuit
from braket.circuits.instruction import Instruction
from braket.registers.qubit_set import QubitSet
from braket.circuits.compiler_directives import StartVerbatimBox, EndVerbatimBox
from braket.circuits.gate import Gate




class ConnectivityCriterion(EmulatorCriterion):   
    """
    args: 
        connectivity_graph (Union[Dict[int, List[int]], DiGraph]): Either a sparse matrix or DiGraph 
        representation of the device connectivity. Can be None if fully_connected is true.

        fully_connected (bool): If true, the all qubits in the device are connected.

        num_qubits (int): The number of qubits in the device; if fully_connected is True,
        this is used to create a complete graph with num_qubits nodes; ignored if 
        connectivity_graph is provided and fully_connected if False.

        qubit_labels (Iterable[int]): A set of qubit labels; if fully_connected is True,
        the qubits_labels are used as nodes of a fully connected topology; ignored if 
        connectivity_graph is provided and fully_connected if False.

    """
    def __init__(self,  connectivity_graph: Union[Dict[int, Iterable[int]], DiGraph] = None, 
                        fully_connected = False, 
                        num_qubits: int = None, 
                        qubit_labels: Union[Iterable[int], QubitSet] = None):
        if not (connectivity_graph or fully_connected): 
            raise ValueError("Either the connectivity_graph must be provided or fully_connected must be True.")

        if fully_connected:
            if not (num_qubits or qubit_labels) or (num_qubits and qubit_labels):
                raise ValueError("Either num_qubits or qubit_labels (NOT both) must be provided if fully_connected is True.")
            self._connectivity_graph = complete_graph(num_qubits if num_qubits else qubit_labels, create_using=DiGraph())
        elif not isinstance(connectivity_graph, DiGraph):
            try:
                self._connectivity_graph = from_dict_of_lists(connectivity_graph, create_using=DiGraph())
            except Exception as e: 
                raise ValueError(f"connectivity_graph must be a valid DiGraph or a dictionary mapping integers (nodes) to a list of integers (adjancency lists): {e}")
        else: 
            self._connectivity_graph = connectivity_graph    


    def validate(self, circuit: Circuit) -> None: 
        """
            Verifies that any verbatim box in a circuit is runnable with respect to the 
            device connectivity definied by this criteria. 
        """
        for idx in range(len(circuit.instructions)): 
            instruction = circuit.instructions[idx]
            if isinstance(instruction.operator, StartVerbatimBox):
                idx += 1
                while idx < len(circuit.instructions) and not isinstance(circuit.instructions[idx].operator, EndVerbatimBox):
                    instruction = circuit.instructions[idx]
                    if isinstance(instruction.operator, Gate):
                        if instruction.operator.qubit_count == 2: #Assuming only maximum 2-qubit native gates are supported
                            self.validate_instruction_connectivity(instruction.control, instruction.target)
                        else: 
                            #just check that the target qubit exists in the connectivity graph
                            target_qubit = instruction.target[0]
                            if not target_qubit in self._connectivity_graph:
                                raise ValueError(f"Qubit {target_qubit} does not exist in the device topology.")
                    idx += 1

                if not isinstance(circuit.instructions[idx].operator, EndVerbatimBox):
                    raise ValueError(f"No end verbatim box found at index {idx} in the circuit.")
                idx += 1

    def validate_instruction_connectivity(self, control_qubits: QubitSet, target_qubits: QubitSet): 
        #Create edges between each of the target qubits
        gate_connectivity_graph = DiGraph()

        #Create an edge from each control bit to each target qubit
        if len(control_qubits) == 1 and len(target_qubits) == 1:
            add_edge(control_qubits[0], target_qubits[0])
        elif len(target_qubits) == 2:
            gate_connectivity_graph.add_edges_from([
                (target_qubits[0], target_qubits[1]), 
                (target_qubits[1], target_qubits[0])
            ])
        else: 
            raise ValueError("Unrecognized qubit targetting setup for a 2 qubit gate.")
        #Check that each edge exists in this criterion's connectivity graph
        for e in gate_connectivity_graph.edges:
            if not self._connectivity_graph.has_edge(*e):
                raise ValueError(f"{e[1]} is not connected to qubit {e[0]} in this device.")
        
        
        

    def __eq__(self, other: EmulatorCriterion) -> bool: 
        return  isinstance(other, ConnectivityCriterion) \
                and graphs_equal(self._connectivity_graph, other._connectivity_graph)
