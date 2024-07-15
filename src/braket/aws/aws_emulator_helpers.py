from collections.abc import Iterable
from functools import singledispatch
from typing import Union

from networkx import DiGraph

from braket.device_schema import DeviceActionType, DeviceCapabilities
from braket.device_schema.ionq import IonqDeviceCapabilities
from braket.device_schema.iqm import IqmDeviceCapabilities
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.emulators.emulator_passes import (
    ConnectivityCriterion,
    GateConnectivityCriterion,
    GateCriterion,
    QubitCountCriterion,
)


def create_qubit_count_criterion(properties: DeviceCapabilities) -> QubitCountCriterion:
    """
    Create a QubitCountCriterion pass which checks that the number of qubits used in a program does
    not exceed the number of qubits allowed by a QPU, as defined in the device properties.

    Args:
        properties (DeviceCapabilities): QPU Device Capabilities object with a
            QHP-specific schema.

    Returns:
        QubitCountCriterion: An eulator pass that checks that the number of qubits used in a program
        does not exceed that of the max qubit count on the device.
    """
    qubit_count = properties.paradigm.qubitCount
    return QubitCountCriterion(qubit_count)


def create_gate_criterion(properties: DeviceCapabilities) -> GateCriterion:
    supported_gates = properties.action[DeviceActionType.OPENQASM].supportedOperations
    """
    Create a GateCriterion pass which defines what supported and native gates are allowed in a
    program based on the provided device properties.

    Args:
        properties (DeviceCapabilities): QPU Device Capabilities object with a
            QHP-specific schema.

    Returns:
        GateCriterion: An emulator pass that checks that a circuit only uses supported gates and
        verbatim circuits only use native gates.
    """

    if isinstance(properties, IqmDeviceCapabilities):
        try:
            supported_gates.remove("start_verbatim_box")
            supported_gates.remove("end_verbatim_box")
        except ValueError:
            pass

    native_gates = properties.paradigm.nativeGateSet

    return GateCriterion(supported_gates=supported_gates, native_gates=native_gates)


@singledispatch
def create_connectivity_criterion(
    properties: DeviceCapabilities, connectivity_graph: DiGraph
) -> ConnectivityCriterion:
    """
    Creates a ConnectivityCriterion pass which validates that multi-qubit gates are applied to
    connected qubits based on this device's connectivity graph.

    Args:
        properties (DeviceCapabilities): QPU Device Capabilities object with a
            QHP-specific schema.

        connectivity_graph (DiGraph): Connectivity graph for this device.

    Returns:
        ConnectivityCriterion: An emulator pass that checks that a circuit only applies two-qubit
        gates to connected qubits on the device.
    """
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
def create_gate_connectivity_criterion(
    properties: DeviceCapabilities, connectivity_graph: DiGraph
) -> GateConnectivityCriterion:
    raise NotImplementedError


@create_gate_connectivity_criterion.register(IqmDeviceCapabilities)
@create_gate_connectivity_criterion.register(RigettiDeviceCapabilities)
def _(
    properties: RigettiDeviceCapabilities, connectivity_graph: DiGraph
) -> GateConnectivityCriterion:
    """
    Both IQM and Rigetti have undirected connectivity graphs; Rigetti device capabilities
    provide back edges, but the calibration data only provides edges in one direction.
    Additionally, IQM does not provide back edges in its connectivity_graph (nor is this
    resolved manually by AwsDevice at the moment).
    """
    gate_connectivity_graph = connectivity_graph.copy()
    edge_properties = properties.standardized.twoQubitProperties
    for u, v in gate_connectivity_graph.edges:
        edge_key = "-".join([str(qubit) for qubit in (u, v)])
        edge_property = edge_properties.get(edge_key)
        if not edge_property:
            gate_connectivity_graph[u][v]["supported_gates"] = set()
            continue
        edge_supported_gates = get_qpu_gate_translation(
            properties, [property.gateName for property in edge_property.twoQubitGateFidelity]
        )
        gate_connectivity_graph[u][v]["supported_gates"] = set(edge_supported_gates)

    for u, v in gate_connectivity_graph.edges:
        if (v, u) not in gate_connectivity_graph.edges or gate_connectivity_graph[v][u].get(
            "supported_gates"
        ) in [None, set()]:
            gate_connectivity_graph.add_edge(
                v, u, supported_gates=set(gate_connectivity_graph[u][v]["supported_gates"])
            )

    return GateConnectivityCriterion(gate_connectivity_graph)


@create_gate_connectivity_criterion.register(IonqDeviceCapabilities)
def _(properties: IonqDeviceCapabilities, connectivity_graph: DiGraph) -> GateConnectivityCriterion:
    """
    Qubits in IonQ's trapped ion devices are all fully connected with identical
    gate-pair capabilities. IonQ does not expliclty provide a set of edges for
    gate connectivity between qubit pairs in their trapped ion QPUs.
    We extrapolate gate connectivity across all possible qubit edge pairs.
    """
    gate_connectivity_graph = connectivity_graph.copy()
    native_gates = get_qpu_gate_translation(properties, properties.paradigm.nativeGateSet)

    for edge in gate_connectivity_graph.edges:
        gate_connectivity_graph[edge[0]][edge[1]]["supported_gates"] = set(native_gates)

    return GateConnectivityCriterion(gate_connectivity_graph)


def get_qpu_gate_translation(
    properties: DeviceCapabilities, gate_name: Union[str, Iterable[str]]
) -> Union[str, list[str]]:
    """Returns the translated gate name(s) for a given QPU device capabilities schema type
        and gate name(s).

    Args:
        properties (DeviceCapabilities): Device capabilities object based on a
            device-specific schema.
        gate_name (Union[str, Iterable[str]]): The name(s) of the gate(s)

    Returns:
        Union[str, list[str]]: The translated gate name(s)
    """
    if isinstance(gate_name, str):
        return _get_qpu_gate_translation(properties, gate_name)
    else:
        return [_get_qpu_gate_translation(properties, name) for name in gate_name]


@singledispatch
def _get_qpu_gate_translation(properties: DeviceCapabilities, gate_name: str) -> str:
    """Returns the translated gate name for a given QPU ARN and gate name.

    Args:
        properties (DeviceCapabilities): QPU Device Capabilities object with a
            QHP-specific schema.
        gate_name (str): The name of the gate

    Returns:
        str: The translated gate name
    """
    return gate_name


@_get_qpu_gate_translation.register(RigettiDeviceCapabilities)
def _(properties: RigettiDeviceCapabilities, gate_name: str) -> str:
    translations = {"CPHASE": "CPhaseShift"}
    return translations.get(gate_name, gate_name)


@_get_qpu_gate_translation.register(IonqDeviceCapabilities)
def _(properties: IonqDeviceCapabilities, gate_name: str) -> str:
    translations = {"GPI": "GPi", "GPI2": "GPi2"}
    return translations.get(gate_name, gate_name)
