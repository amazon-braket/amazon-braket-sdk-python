# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import json

from braket.device_schema.device_capabilities import DeviceCapabilities
from braket.device_schema.ionq.ionq_device_capabilities_v1 import IonqDeviceCapabilities
from braket.device_schema.result_type import ResultType
from braket.device_schema.standardized_gate_model_qpu_device_properties_v1 import (
    OneQubitProperties,
    TwoQubitProperties,
)
from braket.schema_common.schema_base import BraketSchemaBase

from braket.circuits.translations import BRAKET_GATES
from braket.emulation._standardization import _standardize_ionq_device_properties


class DeviceEmulatorProperties:
    """Properties for device emulation.

    Args:
        qubitCount (int): Number of qubits in the device
        nativeGateSet (list[str]): List of native gates supported by the device. Must be valid
            Braket gates. Valid gates include: gphase, i, h, x, y, z, cv, cnot, cy, cz, ecr, s, si,
            t, ti, v, vi, phaseshift, cphaseshift, cphaseshift00, cphaseshift01, cphaseshift10, rx,
            ry, rz, U, swap, iswap, pswap, xy, xx, yy, zz, ccnot, cswap, gpi, gpi2, prx, ms, unitary
        connectivityGraph (dict[str, list[str]]): Graph representing qubit connectivity. If it is an
            empty dictionary, the device is treated as fully connected.
        oneQubitProperties (dict[str, OneQubitProperties]): Properties of one-qubit calibration
            details
        twoQubitProperties (dict[str, TwoQubitProperties]): Properties of two-qubit calibration
            details
        supportedResultTypes (list[ResultType]): List of supported result types.
    """

    def __init__(
        self,
        qubitCount: int,
        nativeGateSet: list[str],
        connectivityGraph: dict[str, list[str]],
        oneQubitProperties: dict[str, OneQubitProperties],
        twoQubitProperties: dict[str, TwoQubitProperties],
        supportedResultTypes: list[ResultType],
    ):
        """Initialize a DeviceEmulatorProperties instance."""
        # Validate inputs
        self._validate_native_gate_set(nativeGateSet)
        self._validate_one_qubit_properties(oneQubitProperties, qubitCount)

        # Get qubit labels for further validation
        indices = list(oneQubitProperties.keys())
        qubit_labels = sorted(int(x) for x in indices)

        self._validate_connectivity_graph(connectivityGraph, qubit_labels)
        self._validate_two_qubit_properties(twoQubitProperties, qubit_labels)

        # Store properties
        self._qubit_count = qubitCount
        self._native_gate_set = nativeGateSet
        self._connectivity_graph = connectivityGraph
        self._one_qubit_properties = oneQubitProperties
        self._two_qubit_properties = twoQubitProperties
        self._supported_result_types = supportedResultTypes

    @staticmethod
    def _validate_native_gate_set(nativeGateSet: list[str]) -> None:
        """Validate that all gates in nativeGateSet are valid Braket gates."""
        valid_gates = ", ".join(BRAKET_GATES.keys())
        for gate in nativeGateSet:
            if gate not in BRAKET_GATES:
                raise ValueError(
                    f"Gate '{gate}' is not a valid Braket gate. Valid gates are: {valid_gates}"
                )

    @staticmethod
    def _validate_one_qubit_properties(
        oneQubitProperties: dict[str, OneQubitProperties], qubitCount: int
    ) -> None:
        """Validate oneQubitProperties."""
        if len(oneQubitProperties) != qubitCount:
            raise ValueError("The length of oneQubitProperties should be the same as qubitCount")

    @staticmethod
    def _node_validator(node: str, qubit_labels: list[int], field_name: str) -> None:
        """Validate that a node represents a valid qubit index."""
        if int(node) not in qubit_labels:
            raise ValueError(
                f"Node {node} in {field_name} must represent a valid qubit index in {qubit_labels}."
            )

    @classmethod
    def _validate_connectivity_graph(
        cls, connectivityGraph: dict[str, list[str]], qubit_labels: list[int]
    ) -> None:
        """Validate connectivityGraph."""
        for node, neighbors in connectivityGraph.items():
            cls._node_validator(node, qubit_labels, "connectivityGraph")

            for neighbor in neighbors:
                if int(neighbor) not in qubit_labels:
                    raise ValueError(
                        f"Neighbor {neighbor} for node {node} must represent a valid qubit index "
                        f"in `qubit_labels`."
                    )

    @classmethod
    def _validate_two_qubit_properties(
        cls, twoQubitProperties: dict[str, TwoQubitProperties], qubit_labels: list[int]
    ) -> None:
        """Validate twoQubitProperties."""
        for edge in twoQubitProperties:
            node_1, node_2 = edge.split("-")
            cls._node_validator(node_1, qubit_labels, "twoQubitProperties")
            cls._node_validator(node_2, qubit_labels, "twoQubitProperties")

    @property
    def qubit_labels(self) -> list[int]:
        """Get the sorted list of qubit indices."""
        indices = list(self.one_qubit_properties.keys())
        return sorted(int(x) for x in indices)

    @property
    def fully_connected(self) -> bool:
        """Determine if the connectivity graph is fully connected.

        Note: We treat the graph as undirected, and determine if it is
            a complete graph by counting the number of distinct edges
        """
        if not self.connectivity_graph:
            return True

        edges = set()
        for node, neighbors in self.connectivity_graph.items():
            edges_node = [(int(node), int(neighbor)) for neighbor in neighbors]
            edges_node = [(min(edge), max(edge)) for edge in edges_node]
            edges.update(edges_node)

        return len(edges) == self.qubit_count * (self.qubit_count - 1) / 2

    @property
    def directed(self) -> bool:
        """Determine if the connectivity graph is a directed graph."""
        for node, neighbors in self.connectivity_graph.items():
            for neighbor in neighbors:
                # If neighbor doesn't link back to node, it's directed
                if node not in self.connectivity_graph.get(neighbor, []):
                    return True
        return False

    @property
    def qubit_count(self) -> int:
        return self._qubit_count

    @property
    def native_gate_set(self) -> list[str]:
        return self._native_gate_set

    @property
    def connectivity_graph(self) -> list[str]:
        return self._connectivity_graph

    @property
    def one_qubit_properties(self) -> dict[str, OneQubitProperties]:
        return self._one_qubit_properties

    @property
    def two_qubit_properties(self) -> dict[str, TwoQubitProperties]:
        return self._two_qubit_properties

    @property
    def supported_result_types(self) -> list[ResultType]:
        return self._supported_result_types

    @classmethod
    def from_device_properties(
        cls, device_properties: DeviceCapabilities
    ) -> "DeviceEmulatorProperties":
        """Create a DeviceEmulatorProperties instance from DeviceCapabilities."""

        if not isinstance(device_properties, DeviceCapabilities):
            raise TypeError("device_properties has to be an instance of DeviceCapabilities.")

        if isinstance(device_properties, IonqDeviceCapabilities):
            device_properties = _standardize_ionq_device_properties(device_properties)

        device_properties_json = device_properties.json()
        properties_dict = json.loads(device_properties_json)

        required_keys = ["paradigm", "standardized"]
        for key in required_keys:
            if (key not in properties_dict) or (properties_dict[key] is None):
                raise ValueError(f"device_properties_json must have non-empty value for key {key}")

        if "braket.ir.openqasm.program" not in properties_dict["action"]:
            raise ValueError(
                "The action in device_properties_json must have key `braket.ir.openqasm.program`."
            )

        # Convert dictionary representations to OneQubitProperties and TwoQubitProperties objects
        one_qubit_props = {}
        for key, value in properties_dict["standardized"]["oneQubitProperties"].items():
            one_qubit_props[key] = OneQubitProperties.parse_obj(value)

        two_qubit_props = {}
        for key, value in properties_dict["standardized"]["twoQubitProperties"].items():
            two_qubit_props[key] = TwoQubitProperties.parse_obj(value)

        # Convert dictionary representations to ResultType objects
        result_types = [
            ResultType.parse_obj(value)
            for value in properties_dict["action"]["braket.ir.openqasm.program"][
                "supportedResultTypes"
            ]
        ]

        return DeviceEmulatorProperties(
            qubitCount=properties_dict["paradigm"]["qubitCount"],
            nativeGateSet=properties_dict["paradigm"]["nativeGateSet"],
            connectivityGraph=properties_dict["paradigm"]["connectivity"]["connectivityGraph"],
            oneQubitProperties=one_qubit_props,
            twoQubitProperties=two_qubit_props,
            supportedResultTypes=result_types,
        )

    @classmethod
    def from_json(cls, device_properties_json: str) -> "DeviceEmulatorProperties":
        """Create a DeviceEmulatorProperties instance from a JSON string."""

        return cls.from_device_properties(BraketSchemaBase.parse_raw_schema(device_properties_json))
