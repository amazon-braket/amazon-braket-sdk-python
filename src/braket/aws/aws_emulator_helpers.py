from braket.emulators import Emulator
from braket.emulators.emulator_passes import (
    SupportedGateCriterion, 
    NativeGateCriterion, 
    ConnectivityCriterion,
    GateConnectivityCriterion, 
    QubitCountCriterion
)
from braket.device_schema import (
    DeviceActionType,
    StandardizedGateModelQpuDeviceProperties,
    DeviceCapabilities
)
from braket.device_schema.ionq import IonqDeviceCapabilities
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.device_schema.iqm import IqmDeviceCapabilities

from functools import singledispatch
from typing import Union
from collections.abc import Iterable
from networkx import DiGraph



def create_supported_gate_criterion(properties: DeviceCapabilities) -> SupportedGateCriterion: 
    supported_gates = properties.action[DeviceActionType.OPENQASM].supportedOperations
    """TODO: Issue in IQM Garnet Supported Operations: Includes "startVerbatimBox" and "endVerbatimBox" instructions in supported operations, 
    which are braket specific pragmas. Filter out explicitly until they are removed from device properties."""     
    
    if isinstance(properties, IqmDeviceCapabilities):
        try: 
            supported_gates.remove("start_verbatim_box")
            supported_gates.remove("end_verbatim_box")
        except ValueError:
            pass
        
    supported_gates_criterion = SupportedGateCriterion(supported_gates)
    return supported_gates_criterion
    
    
def create_qubit_count_criterion(properties: DeviceCapabilities) -> QubitCountCriterion:
    qubit_count = properties.paradigm.qubitCount
    return QubitCountCriterion(qubit_count)

def create_native_gate_criterion(properties: DeviceCapabilities) -> NativeGateCriterion:
    native_gates = properties.paradigm.nativeGateSet
    native_gate_criterion = NativeGateCriterion(native_gates)
    return native_gate_criterion


@singledispatch
def create_connectivity_criterion(properties: DeviceCapabilities, connectivity_graph: DiGraph) -> ConnectivityCriterion: 
    connectivity_criterion = ConnectivityCriterion(connectivity_graph)
    return connectivity_criterion

@create_connectivity_criterion.register(IqmDeviceCapabilities)
def _(properties: IqmDeviceCapabilities, connectivity_graph: DiGraph) -> ConnectivityCriterion:
    """
    IQM qubit connectivity is undirected but the directed graph that represents qubit connectivity 
    does not include back-edges. Thus, we must explicitly introduce back edges before creating
    the ConnectivityCriterion for an IQM device. 
    """
    connectivity_graph = connectivity_graph.copy()
    for edge in connectivity_graph.edges:
        connectivity_graph.add_edge(edge[1], edge[0])
    return ConnectivityCriterion(connectivity_graph)

@singledispatch
def create_gate_connectivity_criterion(properties, connectivity_graph: DiGraph) -> GateConnectivityCriterion:
    raise NotImplementedError

@create_gate_connectivity_criterion.register(RigettiDeviceCapabilities)
def _(properties: RigettiDeviceCapabilities, connectivity_graph: DiGraph) -> GateConnectivityCriterion: 
    """
    Rigetti provides device capabilities using a standardized properties schema for gate devices. 
    
    Rigetti provides both forwards and backwards edges for their undirected gate connectivity graph, so 
    no new needs to be introduced when creating a GateConnectivityCriterion object for a Rigetti QPU.  
    """
    gate_connectivity_graph = connectivity_graph.copy()
    edge_properties = properties.standardized.twoQubitProperties
    for edge in gate_connectivity_graph.edges: 
        edge_key = "-".join([str(qubit) for qubit in edge])
        edge_property  = edge_properties.get(edge_key, list())
        if not edge_property:
            continue
        edge_supported_gates = get_qpu_gate_translation(properties, 
                                                        [property.gateName for property in edge_property.twoQubitGateFidelity])
        gate_connectivity_graph[edge[0]][edge[1]]["supported_gates"] = edge_supported_gates
    
    return GateConnectivityCriterion(gate_connectivity_graph)
    
    
@create_gate_connectivity_criterion.register(IqmDeviceCapabilities)
def _(properties: IqmDeviceCapabilities, connectivity_graph: DiGraph) -> GateConnectivityCriterion: 
    """
    IQM provides device capabilities using a standardized properties schema for gate devices. 

    IQM provides only forward edges for their *undirected* gate connectivity graph, so back-edges must
    be introduced when creating the GateConnectivityCriterion object for an IQM QPU.
    """
    gate_connectivity_graph = connectivity_graph.copy()
    for edge in gate_connectivity_graph.edges:
        gate_connectivity_graph.add_edge(edge[1], edge[0])
    
    edge_properties = properties.standardized.twoQubitProperties
    for edge_property in edge_properties.keys():
        edge = [int(qubit) for qubit in edge_property.split("-")]
        edge_supported_gates = get_qpu_gate_translation(properties,
                                                        [property.gateName for property in edge_properties[edge_property].twoQubitGateFidelity])
        gate_connectivity_graph[edge[0]][edge[1]]["supported_gates"] = edge_supported_gates
        gate_connectivity_graph[edge[1]][edge[0]]["supported_gates"] = edge_supported_gates

    return GateConnectivityCriterion(gate_connectivity_graph)

 
    
@create_gate_connectivity_criterion.register(IonqDeviceCapabilities)
def _(properties: IonqDeviceCapabilities, connectivity_graph: DiGraph) -> GateConnectivityCriterion: 
    """
    Qubits in IonQ's trapped ion devices are all fully connected with identical gate-pair capabilities. 
    Thus, IonQ does not expliclty provide a set of edges for gate connectivity between qubit pairs in 
    their trapped ion QPUs. We extrapolate gate connectivity across all possible qubit edge pairs. 
    """
    gate_connectivity_graph = connectivity_graph.copy()
    native_gates = get_qpu_gate_translation(properties, properties.paradigm.nativeGateSet)
    for edge in gate_connectivity_graph.edges: 
        gate_connectivity_graph[edge[0]][edge[1]]["supported_gates"] = native_gates
    
    return GateConnectivityCriterion(gate_connectivity_graph)

def get_qpu_gate_translation(properties: DeviceCapabilities, gate_name: Union[str, Iterable[str]]) -> Union[str, list[str]]:
    """Returns the translated gate name(s) for a given QPU ARN and gate name(s).

    Args:
        arn (str): The ARN of the QPU
        gate_name (Union[str, Iterable[str]]): The name(s) of the gate(s)

    Returns:
        Union[str, list[str]]: The translated gate name(s)
    """
    if isinstance(gate_name, str):
        return _get_qpu_gate_translation(properties, gate_name)
    else:
        return [_get_qpu_gate_translation(properties, name) for name in gate_name]


@singledispatch
def _get_qpu_gate_translation(properties, gate_name: str) -> str:
    """Returns the translated gate name for a given QPU ARN and gate name.

    Args:
        properties (str): QHP device properties type
        gate_name (str): The name of the gate

    Returns:
        str: The translated gate name
    """
    return gate_name


#TODO: put translations in global dict with explicit QHP names as keys? 

@_get_qpu_gate_translation.register(RigettiDeviceCapabilities)
def _(properties: RigettiDeviceCapabilities, gate_name: str) -> str: 
    translations = {
        "CPHASE": "CPhaseShift"
    }
    return translations.get(gate_name, gate_name)  

@_get_qpu_gate_translation.register(IonqDeviceCapabilities)
def _(properties: IonqDeviceCapabilities, gate_name: str) -> str: 
    translations = {
        "GPI": "GPi", 
        "GPI2": "GPi2"
    }
    return translations.get(gate_name, gate_name)