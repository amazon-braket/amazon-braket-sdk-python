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
        connectivity_graph=device_emu_properties.connectivity_graph,
        num_qubits=device_emu_properties.qubit_count,
        qubit_labels=device_emu_properties.qubit_labels,
        directed=False,
        # Set directed to false because ConnectivityValidator validates
        # the connectivity regardless if the graph is directed or undirected.
    )


def _set_up_gate_connectivity_validator(
    device_emu_properties: DeviceEmulatorProperties,
) -> GateConnectivityValidator:
    directed = device_emu_properties.directed

    if device_emu_properties.fully_connected:
        gate_connectivity_graph = {}
        for qubit_1 in device_emu_properties.qubit_labels:
            for qubit_2 in device_emu_properties.qubit_labels:
                gate_connectivity_graph[qubit_1, qubit_2] = set(
                    device_emu_properties.native_gate_set
                )
    else:
        # For non fully connected graph
        gate_connectivity_graph = {}
        for edge, edge_property in device_emu_properties.two_qubit_properties.items():
            vertices = edge.split("-")
            edge_int = tuple(int(vertex) for vertex in vertices)
            edge_supported_gates = [
                item.gateName.lower()
                for item in edge_property.twoQubitGateFidelity
                if item.gateName.lower() in BRAKET_GATES
            ]
            gate_connectivity_graph[edge_int] = set(edge_supported_gates)

    return GateConnectivityValidator(gate_connectivity_graph, directed=directed)
