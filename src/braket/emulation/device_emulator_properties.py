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

from typing import Dict, List, Any, Type
from importlib import import_module
from braket.circuits.translations import BRAKET_GATES
from braket.device_schema.result_type import ResultType
from braket.device_schema.error_mitigation.error_mitigation_scheme import ErrorMitigationScheme
from braket.device_schema.error_mitigation.error_mitigation_properties import (
    ErrorMitigationProperties,
)
from pydantic.v1 import BaseModel, conint, constr, root_validator, validator
from braket.device_schema.standardized_gate_model_qpu_device_properties_v1 import (
    OneQubitProperties,
    TwoQubitProperties,
)
from braket.device_schema.device_capabilities import DeviceCapabilities
import json
from braket.emulation.device_emulator_utils import DEFAULT_SUPPORTED_RESULT_TYPES


class DeviceEmulatorProperties(BaseModel):
    """Properties for device emulation.

    Args:
        qubitCount (int): Number of qubits in the device
        nativeGateSet (List[str]): List of native gates supported by the device. Must be valid Braket gates.
            Valid gates include: gphase, i, h, x, y, z, cv, cnot, cy, cz, ecr, s, si, t, ti, v, vi,
            phaseshift, cphaseshift, cphaseshift00, cphaseshift01, cphaseshift10, rx, ry, rz, U,
            swap, iswap, pswap, xy, xx, yy, zz, ccnot, cswap, gpi, gpi2, prx, ms, unitary
        connectivityGraph (Dict[str, List[str]]): Graph representing qubit connectivity. If it is an
            empty dictionary, the device is treated as fully connected.
        oneQubitProperties (Dict[str, OneQubitProperties]): Properties of one-qubit calibration details
        twoQubitProperties (Dict[str, TwoQubitProperties]): Properties of two-qubit calibration details
        supportedResultTypes (List[ResultType]): List of supported result types. The valid result types
            include those in the DEFAULT_SUPPORTED_RESULT_TYPES. Default is DEFAULT_SUPPORTED_RESULT_TYPES.
        errorMitigation (Dict[ErrorMitigationScheme, ErrorMitigationProperties]): Error mitigation settings.
            If it is an empty dictionary, then no error mitigation. Default is {}.
    """

    NonNegativeIntStr = constr(regex=r"^(0|[1-9][0-9]*)$")  # non-negative integers
    TwoNonNegativeIntsStr = constr(
        regex=r"^(0|[1-9][0-9]*)-(0|[1-9][0-9]*)$"
    )  # two non-negative integers connected by "-"

    qubitCount: conint(strict=True, ge=1)
    nativeGateSet: List[str]
    connectivityGraph: Dict[NonNegativeIntStr, List[NonNegativeIntStr]]
    oneQubitProperties: Dict[NonNegativeIntStr, OneQubitProperties]
    twoQubitProperties: Dict[TwoNonNegativeIntsStr, TwoQubitProperties]
    supportedResultTypes: List[ResultType] = DEFAULT_SUPPORTED_RESULT_TYPES
    errorMitigation: Dict[type[ErrorMitigationScheme], ErrorMitigationProperties] = {}

    @root_validator
    def validate_nativeGateSet(cls, values):
        nativeGateSet = values.get("nativeGateSet")
        for gate in nativeGateSet:
            if gate not in BRAKET_GATES:
                raise ValueError(
                    f"Gate '{gate}' is not a valid Braket gate. Valid gates are: {', '.join(BRAKET_GATES.keys())}"
                )
        return values

    @root_validator
    def validate_oneQubitProperties(cls, values):
        oneQubitProperties = values["oneQubitProperties"]
        qubitCount = values.get("qubitCount")
        if len(oneQubitProperties) != qubitCount:
            raise ValueError("The length of oneQubitProperties should be the same as qubitCount")

        return values

    @classmethod
    def node_validator(cls, node, qubit_indices, field_name):
        if int(node) not in qubit_indices:
            raise ValueError(
                f"Node {node} in {field_name} must represent a valid qubit index "
                f"in {qubit_indices}."
            )

    @root_validator
    def validate_connectivityGraph(cls, values):
        connectivityGraph = values.get("connectivityGraph")
        oneQubitProperties = values.get("oneQubitProperties")
        indices = list(oneQubitProperties.keys())
        qubit_indices = sorted(int(x) for x in indices)

        for node, neighbors in connectivityGraph.items():
            cls.node_validator(node, qubit_indices, "connectivityGraph")

            for neighbor in neighbors:
                if int(neighbor) not in qubit_indices:
                    raise ValueError(
                        f"Neighbor {neighbor} for node {node} must represent a valid qubit index "
                        f"in `qubit_indices`."
                    )

        return values

    @root_validator
    def validate_twoQubitProperties(cls, values):
        twoQubitProperties = values["twoQubitProperties"]
        oneQubitProperties = values.get("oneQubitProperties")
        indices = list(oneQubitProperties.keys())
        qubit_indices = sorted(int(x) for x in indices)

        for edge, _ in twoQubitProperties.items():
            node_1, node_2 = edge.split("-")
            cls.node_validator(node_1, qubit_indices, "twoQubitProperties")
            cls.node_validator(node_2, qubit_indices, "twoQubitProperties")

        ## TODO: Add validation that all edges have calibration data
        return values

    @validator("supportedResultTypes", pre=False)
    def validate_supportedResultTypes(cls, supportedResultTypes: List):
        valid_result_types = [rt.name for rt in DEFAULT_SUPPORTED_RESULT_TYPES]

        for result_type in supportedResultTypes:
            # Check if result type is one of the valid types
            if result_type.name not in valid_result_types:
                raise ValueError(
                    f"Invalid result type. Must be one of: {', '.join(valid_result_types)}"
                )
        return supportedResultTypes

    @property
    def qubit_indices(self) -> list:
        indices = list(self.oneQubitProperties.keys())
        return sorted(int(x) for x in indices)

    @property
    def fully_connected(self) -> bool:
        """Determine if the connectivity graph is fully connected.
        
        Note: We determine if a node shares an edge, regardless its direction,
            with every other node in the graph.
        """
        if not self.connectivityGraph:
            return True

        visited = set()
        start_node = next(iter(self.connectivityGraph))  # pick any starting node

        def dfs(node):
            if node not in visited:
                visited.add(node)
                for neighbor in self.connectivityGraph.get(node, []):
                    dfs(neighbor)

        dfs(start_node)
        return len(visited) == len(self.connectivityGraph)

    @property
    def directed(self) -> bool:
        """Determine if the connectivity graph is a directed graph.
        """
        for node, neighbors in self.connectivityGraph.items():
            for neighbor in neighbors:
                # If neighbor doesn't link back to node, it's directed
                if node not in self.connectivityGraph.get(neighbor, []):
                    return True
        return False

    @classmethod
    def from_device_properties(cls, device_properties: DeviceCapabilities):
        if isinstance(device_properties, DeviceCapabilities):
            return cls.from_json(device_properties.json())
        else:
            raise ValueError(f"device_properties has to be an instance of DeviceCapabilities.")

    @classmethod
    def from_json(cls, device_properties_json: str):
        properties_dict = json.loads(device_properties_json)
        if not isinstance(properties_dict, dict):
            raise ValueError(f"device_properties_json must be a json of a dictionary")

        required_keys = ["paradigm", "standardized"]
        for key in required_keys:
            if (key not in properties_dict) or (properties_dict[key] is None):
                raise ValueError(f"device_properties_json have non-empty value for key {key}")

        if "braket.ir.openqasm.program" not in properties_dict["action"]:
            raise ValueError(
                f"The action in device_properties_json must have key `braket.ir.openqasm.program`."
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

        device_emulator_properties = DeviceEmulatorProperties(
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

        return device_emulator_properties
