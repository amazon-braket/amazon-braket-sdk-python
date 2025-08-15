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

from braket.circuits.translations import BRAKET_GATES
from braket.emulation.device_emulator_properties import DeviceEmulatorProperties
from braket.emulation.passes.circuit_passes import ConnectivityValidator, GateConnectivityValidator


def _set_up_connectivity_validator(
    device_emu_properties: DeviceEmulatorProperties,
) -> ConnectivityValidator:
    if device_emu_properties.fully_connected:
        return ConnectivityValidator(
            qubit_labels=device_emu_properties.qubit_labels,
            fully_connected=True,
            directed=False,
            # Set directed to false because ConnectivityValidator validates
            # the connectivity regardless if the graph is directed or undirected.
        )
    return ConnectivityValidator(
        connectivity_graph=device_emu_properties.connectivityGraph,
        num_qubits=device_emu_properties.qubitCount,
        qubit_labels=device_emu_properties.qubit_labels,
        directed=False,
        # Set directed to false because ConnectivityValidator validates
        # the connectivity regardless if the graph is directed or undirected.
    )


def _set_up_gate_connectivity_validator(
    device_emu_properties: DeviceEmulatorProperties,
) -> GateConnectivityValidator:
    if device_emu_properties.fully_connected:
        gate_connectivity_graph = {}
        for qubit_1 in device_emu_properties.qubit_labels:
            for qubit_2 in device_emu_properties.qubit_labels:
                gate_connectivity_graph[qubit_1, qubit_2] = set(device_emu_properties.nativeGateSet)
    else:
        twoQubitProperties = device_emu_properties.twoQubitProperties
        # For non fully connected graph
        gate_connectivity_graph = {}
        for node, neighbors in device_emu_properties.connectivityGraph.items():
            for neighbor in neighbors:
                edge = (int(node), int(neighbor))
                edge_key = "-".join([str(qubit) for qubit in edge])
                edge_property = twoQubitProperties.get(edge_key)
                if not edge_property:
                    gate_connectivity_graph[edge] = set()
                    continue

                edge_supported_gates = [
                    item.gateName.lower()
                    for item in edge_property.twoQubitGateFidelity
                    if item.gateName.lower() in BRAKET_GATES
                ]
                gate_connectivity_graph[edge] = set(edge_supported_gates)

        reversed_gate_connectivity_graph = {}
        for edge, edge_property in gate_connectivity_graph.items():
            reversed_edge = (edge[1], edge[0])
            if reversed_edge not in gate_connectivity_graph:
                reversed_gate_connectivity_graph[reversed_edge] = edge_property

        gate_connectivity_graph.update(reversed_gate_connectivity_graph)

    return GateConnectivityValidator(gate_connectivity_graph)
