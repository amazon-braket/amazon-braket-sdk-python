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
from importlib import import_module

from braket.device_schema.device_capabilities import DeviceCapabilities
from braket.device_schema.error_mitigation.error_mitigation_properties import (
    ErrorMitigationProperties,
)
from braket.device_schema.error_mitigation.error_mitigation_scheme import ErrorMitigationScheme
from braket.device_schema.ionq.ionq_device_capabilities_v1 import IonqDeviceCapabilities
from braket.device_schema.result_type import ResultType
from braket.device_schema.standardized_gate_model_qpu_device_properties_v1 import (
    OneQubitProperties,
    TwoQubitProperties,
)
from pydantic.v1 import BaseModel, conint, constr, root_validator

from braket.circuits.translations import BRAKET_GATES
from braket.emulation.device_emulator_utils import (
    standardize_ionq_device_properties,
)


class DeviceEmulatorProperties(BaseModel):
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
        errorMitigation (dict[ErrorMitigationScheme, ErrorMitigationProperties]): Error mitigation
            settings. If it is an empty dictionary, then no error mitigation. Default is {}.
    """

    NonNegativeIntStr = constr(regex=r"^(0|[1-9][0-9]*)$")  # non-negative integers
    TwoNonNegativeIntsStr = constr(
        regex=r"^(0|[1-9][0-9]*)-(0|[1-9][0-9]*)$"
    )  # two non-negative integers connected by "-"

    qubitCount: conint(strict=True, ge=1)
    nativeGateSet: list[str]
    connectivityGraph: dict[NonNegativeIntStr, list[NonNegativeIntStr]]
    oneQubitProperties: dict[NonNegativeIntStr, OneQubitProperties]
    twoQubitProperties: dict[TwoNonNegativeIntsStr, TwoQubitProperties]
    supportedResultTypes: list[ResultType]
    errorMitigation: dict[type[ErrorMitigationScheme], ErrorMitigationProperties] = {}

    @root_validator
    @classmethod
    def validate_nativeGateSet(cls, values: dict) -> dict:
        nativeGateSet = values.get("nativeGateSet")
        valid_gates = ", ".join(BRAKET_GATES.keys())
        for gate in nativeGateSet:
            if gate not in BRAKET_GATES:
                raise ValueError(
                    f"Gate '{gate}' is not a valid Braket gate. Valid gates are: {valid_gates}"
                )
        return values

    @root_validator
    @classmethod
    def validate_oneQubitProperties(cls, values: dict) -> dict:
        oneQubitProperties = values["oneQubitProperties"]
        qubitCount = values.get("qubitCount")
        if len(oneQubitProperties) != qubitCount:
            raise ValueError("The length of oneQubitProperties should be the same as qubitCount")

        return values

    @classmethod
    def node_validator(cls, node: str, qubit_labels: list[int], field_name: str) -> None:
        if int(node) not in qubit_labels:
            raise ValueError(
                f"Node {node} in {field_name} must represent a valid qubit index in {qubit_labels}."
            )

    @root_validator
    @classmethod
    def validate_connectivityGraph(cls, values: dict) -> dict:
        connectivityGraph = values.get("connectivityGraph")
        oneQubitProperties = values.get("oneQubitProperties")
        indices = list(oneQubitProperties.keys())
        qubit_labels = sorted(int(x) for x in indices)

        for node, neighbors in connectivityGraph.items():
            cls.node_validator(node, qubit_labels, "connectivityGraph")

            for neighbor in neighbors:
                if int(neighbor) not in qubit_labels:
                    raise ValueError(
                        f"Neighbor {neighbor} for node {node} must represent a valid qubit index "
                        f"in `qubit_labels`."
                    )

        return values

    @root_validator
    @classmethod
    def validate_twoQubitProperties(cls, values: dict) -> dict:
        twoQubitProperties = values["twoQubitProperties"]
        oneQubitProperties = values.get("oneQubitProperties")
        indices = list(oneQubitProperties.keys())
        qubit_labels = sorted(int(x) for x in indices)

        for edge in twoQubitProperties:
            node_1, node_2 = edge.split("-")
            cls.node_validator(node_1, qubit_labels, "twoQubitProperties")
            cls.node_validator(node_2, qubit_labels, "twoQubitProperties")

        return values

    @property
    def qubit_labels(self) -> list:
        indices = list(self.oneQubitProperties.keys())
        return sorted(int(x) for x in indices)

    @property
    def fully_connected(self) -> bool:
        """Determine if the connectivity graph is fully connected.

        Note: We treat the graph as undirected, and determine if it is
            a complete graph by counting the number of distinct edges
        """
        if not self.connectivityGraph:
            return True

        edges = set()
        for node, neighbors in self.connectivityGraph.items():
            edges_node = [(int(node), int(neighbor)) for neighbor in neighbors]
            edges_node = [(min(edge), max(edge)) for edge in edges_node]
            edges.update(edges_node)

        return len(edges) == self.qubitCount * (self.qubitCount - 1) / 2

    @property
    def directed(self) -> bool:
        """Determine if the connectivity graph is a directed graph."""
        for node, neighbors in self.connectivityGraph.items():
            for neighbor in neighbors:
                # If neighbor doesn't link back to node, it's directed
                if node not in self.connectivityGraph.get(neighbor, []):
                    return True
        return False

    @classmethod
    def from_device_properties(
        cls, device_properties: DeviceCapabilities
    ) -> "DeviceEmulatorProperties":
        if isinstance(device_properties, IonqDeviceCapabilities):
            device_properties = standardize_ionq_device_properties(device_properties)
        if isinstance(device_properties, DeviceCapabilities):
            return cls.from_json(device_properties.json())
        raise ValueError("device_properties has to be an instance of DeviceCapabilities.")

    @classmethod
    def from_json(cls, device_properties_json: str) -> "DeviceEmulatorProperties":
        properties_dict = json.loads(device_properties_json)
        if not isinstance(properties_dict, dict):
            raise TypeError("device_properties_json must be a json of a dictionary")

        required_keys = ["paradigm", "standardized"]
        for key in required_keys:
            if (key not in properties_dict) or (properties_dict[key] is None):
                raise ValueError(f"device_properties_json have non-empty value for key {key}")

        if "braket.ir.openqasm.program" not in properties_dict["action"]:
            raise ValueError(
                "The action in device_properties_json must have key `braket.ir.openqasm.program`."
            )

        if "provider" in properties_dict:
            if properties_dict["provider"]:
                em = properties_dict["provider"].get("errorMitigation") or {}
            else:
                em = {}
            errorMitigation = {}
            for k, v in em.items():
                split = k.rsplit(".", 1)
                errorMitigation[getattr(import_module(split[0]), split[1])] = (
                    ErrorMitigationProperties(minimumShots=v["minimumShots"])
                )
        else:
            errorMitigation = {}

        return DeviceEmulatorProperties(
            qubitCount=properties_dict["paradigm"]["qubitCount"],
            nativeGateSet=properties_dict["paradigm"]["nativeGateSet"],
            connectivityGraph=properties_dict["paradigm"]["connectivity"]["connectivityGraph"],
            oneQubitProperties=properties_dict["standardized"]["oneQubitProperties"],
            twoQubitProperties=properties_dict["standardized"]["twoQubitProperties"],
            supportedResultTypes=properties_dict["action"]["braket.ir.openqasm.program"][
                "supportedResultTypes"
            ],
            errorMitigation=errorMitigation,
        )
