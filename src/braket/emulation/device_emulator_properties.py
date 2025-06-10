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

from typing import Dict, List, Optional

from braket.circuits.translations import BRAKET_GATES
from braket.circuits import result_types
from braket.device_schema.result_type import ResultType
from braket.device_schema.error_mitigation.error_mitigation_scheme import ErrorMitigationScheme
from braket.device_schema.error_mitigation.error_mitigation_properties import ErrorMitigationProperties
from pydantic.v1 import BaseModel
from braket.device_schema.standardized_gate_model_qpu_device_properties_v1 import (
    OneQubitProperties,
    TwoQubitProperties
)

from device_emulator_utils import DEFAULT_SUPPORTED_RESULT_TYPES


class DeviceEmulatorProperties(BaseModel):
    """Properties for device emulation.

    Args:
        qubitCount (int): Number of qubits in the device
        nativeGateSet (List[str]): List of native gates supported by the device. Must be valid Braket gates.
            Valid gates include: gphase, i, h, x, y, z, cv, cnot, cy, cz, ecr, s, si, t, ti, v, vi,
            phaseshift, cphaseshift, cphaseshift00, cphaseshift01, cphaseshift10, rx, ry, rz, U,
            swap, iswap, pswap, xy, xx, yy, zz, ccnot, cswap, gpi, gpi2, prx, ms, unitary
        connectivityGraph (Dict[str, List[str]]): Graph representing qubit connectivity. If it is an 
            empty dictionary, the device is treated fully connected.
        oneQubitProperties (Dict[str, OneQubitProperties]): Properties of one-qubit calibration details
        twoQubitProperties (Dict[str, TwoQubitProperties]): Properties of two-qubit calibration details
        supportedResultTypes (List[ResultType]): List of supported result types. The valid result types 
            include those in the DEFAULT_SUPPORTED_RESULT_TYPES. Default is DEFAULT_SUPPORTED_RESULT_TYPES.
        errorMitigation (Dict[ErrorMitigationScheme, ErrorMitigationProperties]): Error mitigation settings. 
            If it is an empty dictionary, then no error mitigation. Default is {}.
    """

    qubitCount: int
    nativeGateSet: List[str]
    connectivityGraph: Dict[str, List[str]]
    oneQubitProperties: Dict[str, OneQubitProperties]
    twoQubitProperties: Dict[str, TwoQubitProperties]
    supportedResultTypes: List[ResultType] = DEFAULT_SUPPORTED_RESULT_TYPES
    errorMitigation: Dict[ErrorMitigationScheme, ErrorMitigationProperties] = {}

    def __post_init__(self):
        """Validate the properties after initialization."""

        # Validate the input qubitCount
        if not isinstance(self.qubitCount, int) or self.qubitCount < 1:
            raise ValueError("qubitCount must be a positive integer")

        # Validate the input nativeGateSet
        if not isinstance(self.nativeGateSet, list):
            raise ValueError("nativeGateSet must be a list of strings")
        
        for gate in self.nativeGateSet:
            if gate.lower() not in BRAKET_GATES:
                raise ValueError(
                    f"Gate '{gate}' is not a valid Braket gate. Valid gates are: {', '.join(BRAKET_GATES.keys())}"
                )

        # Validate the input connectivityGraph
        if not isinstance(self.connectivityGraph, dict):
            raise ValueError("connectivityGraph must be a dictionary")

        for node, neighbors in self.connectivityGraph.items():
            if (not isinstance(node, str)) or (not node.isdigit()):
                raise ValueError(f"Node {node} in connectivityGraph must be a string of digits")
            node_int = int(node)
            if not 0 <= node_int < self.qubitCount:
                raise ValueError(
                    f"Node {node} in connectivityGraph must represent a valid qubit index "
                    f"in range [0, {self.qubitCount-1}]"
                )
            
            if not isinstance(neighbors, list):
                raise ValueError(f"Neighbors for node {node} must be a list")
            
            for neighbor in neighbors:
                if (not isinstance(neighbor, str)) or (not neighbor.isdigit()):
                    raise ValueError(f"Neighbor {neighbor} for node {node} must be a string of digits")
                edge_int = int(neighbor)
                if not 0 <= edge_int < self.qubitCount:
                    raise ValueError(
                        f"Neighbor {neighbor} for node {node} must represent a valid qubit index "
                        f"in range [0, {self.qubitCount-1}]"
                    )

        # Validate the input oneQubitProperties and twoQubitProperties
        if not isinstance(self.oneQubitProperties, dict):
            raise ValueError("oneQubitProperties must be a dictionary")
        
        if not isinstance(self.twoQubitProperties, dict):
            raise ValueError("twoQubitProperties must be a dictionary")
        
        for twoQubitProperty in self.twoQubitProperties:
            if not isinstance(twoQubitProperty, TwoQubitProperties):
                raise ValueError("Each element in twoQubitProperties must be a TwoQubitProperties")

        for oneQubitProperty in self.oneQubitProperties:
            if not isinstance(oneQubitProperty, OneQubitProperties):
                raise ValueError("Each element in oneQubitProperties must be a OneQubitProperties")

        # Validate the input supported result type
        if not isinstance(self.supportedResultTypes, list):
            raise ValueError("supportedResultTypes must be a list")

        # Validate result types
        valid_result_types = [rt.name for rt in DEFAULT_SUPPORTED_RESULT_TYPES]

        for result_type in self.supportedResultTypes:
            if not isinstance(result_type, ResultType):
                raise ValueError("Each element in supportedResultTypes must be a ResultType")

            # Check if result type is one of the valid types
            if result_type.name not in valid_result_types:
                raise ValueError(
                    f"Invalid result type. Must be one of: {', '.join(valid_result_types)}"
                )

        # Validate error mitigation settings if provided
        if not isinstance(self.errorMitigation, dict):
            raise ValueError("errorMitigation must be a dictionary")

        if self.errorMitigation:
            for scheme, properties in self.errorMitigation.items():
                if not isinstance(scheme, ErrorMitigationScheme):
                    raise ValueError(f"Error mitigation scheme must be of type ErrorMitigationScheme")
                if not isinstance(properties, ErrorMitigationProperties):
                    raise ValueError(f"Error mitigation properties must be of type ErrorMitigationProperties")
