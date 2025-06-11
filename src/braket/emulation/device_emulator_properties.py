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
    errorMitigation: Dict[
        str, ErrorMitigationProperties
    ] = {}  # We will convert the key of the dict to ErrorMitigationScheme below

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
    def validate_connectivityGraph(cls, values):
        connectivityGraph = values.get("connectivityGraph")
        qubitCount = values.get("qubitCount")
        for node, neighbors in connectivityGraph.items():
            node_int = int(node)
            if not 0 <= node_int < qubitCount:
                raise ValueError(
                    f"Node {node} in connectivityGraph must represent a valid qubit index "
                    f"in range [0, {qubitCount - 1}]"
                )
            for neighbor in neighbors:
                edge_int = int(neighbor)
                if not 0 <= edge_int < qubitCount:
                    raise ValueError(
                        f"Neighbor {neighbor} for node {node} must represent a valid qubit index "
                        f"in range [0, {qubitCount - 1}]"
                    )
        return values

    @classmethod
    def node_validator(cls, node, qubitCount):
        if not 0 <= int(node) < qubitCount:
            raise ValueError(
                f"Node {node} in oneQubitProperties must represent a valid qubit index "
                f"in range [0, {qubitCount - 1}]"
            )

    @root_validator
    def validate_oneQubitProperties(cls, values):
        oneQubitProperties = values["oneQubitProperties"]
        qubitCount = values.get("qubitCount")
        for node, _ in oneQubitProperties.items():
            cls.node_validator(node, qubitCount)

        for node in range(qubitCount):
            if str(node) not in oneQubitProperties.keys():
                raise ValueError(f"The qubit property for node {node} is not provided.")

        return values

    @root_validator
    def validate_twoQubitProperties(cls, values):
        twoQubitProperties = values["twoQubitProperties"]
        qubitCount = values.get("qubitCount")

        for edge, _ in twoQubitProperties.items():
            node_1, node_2 = edge.split("-")
            cls.node_validator(node_1, qubitCount)
            cls.node_validator(node_1, qubitCount)

        ## TODO: Add validation that all edges have calibration data
        return values

    @root_validator
    def validate_supportedResultTypes(cls, values):
        supportedResultTypes = values["supportedResultTypes"]
        valid_result_types = [rt.name for rt in DEFAULT_SUPPORTED_RESULT_TYPES]

        for result_type in supportedResultTypes:
            # Check if result type is one of the valid types
            if result_type.name not in valid_result_types:
                raise ValueError(
                    f"Invalid result type. Must be one of: {', '.join(valid_result_types)}"
                )
        return values

    @validator("errorMitigation", pre=True)
    def normalize_keys(cls, v: Any):
        """
        Pre-validator to convert class keys (e.g., Debias) to string keys ('Debias').

        This allows using class objects in input even though Pydantic requires
        string keys in JSON-compatible structures.
        """

        if not isinstance(v, dict):
            raise TypeError("errorMitigation must be a dict")
        return {(k.__name__ if isinstance(k, type) else str(k)): val for k, val in v.items()}

    @classmethod
    def get_error_mitigation_class(cls, name: str) -> Type[ErrorMitigationScheme]:
        """
        Lookup method to resolve a class name string back to its class type.

        Raises:
            ValueError: if the name doesn't correspond to a known subclass.
        """

        subclasses = {sub.__name__: sub for sub in ErrorMitigationScheme.__subclasses__()}
        if name not in subclasses:
            raise ValueError(f"Unknown ErrorMitigationScheme subclass: {name}")
        return subclasses[name]

    def get_error_mitigation_resolved(
        self,
    ) -> Dict[Type[ErrorMitigationScheme], ErrorMitigationProperties]:
        """
        Converts the internal string-keyed errorMitigation map back to one keyed by class types.

        Returns:
            Dict[Type[ErrorMitigationScheme], ErrorMitigationProperties]
        """

        return {self.get_error_mitigation_class(k): v for k, v in self.errorMitigation.items()}


def distill_device_emulator_properties(
    device_properties: DeviceCapabilities,
) -> DeviceEmulatorProperties:
    """Distill information from device properties for device emulation

    Args:
        device_properties (DeviceCapabilities): The device properties to use for emulation.

    Returns:
        DeviceEmulatorProperties: An instance of DeviceEmulatorProperties for device emulation
    """

    if isinstance(device_properties, DeviceCapabilities):
        if hasattr(device_properties.provider, "errorMitigation"):
            errorMitigation = device_properties.provider.errorMitigation
        else:
            errorMitigation = {}

        device_emulator_properties = DeviceEmulatorProperties(
            qubitCount=device_properties.paradigm.qubitCount,
            nativeGateSet=device_properties.paradigm.nativeGateSet,
            connectivityGraph=device_properties.paradigm.connectivity.connectivityGraph,
            oneQubitProperties=device_properties.standardized.oneQubitProperties,
            twoQubitProperties=device_properties.standardized.twoQubitProperties,
            supportedResultTypes=device_properties.action[
                "braket.ir.openqasm.program"
            ].supportedResultTypes,
            errorMitigation=errorMitigation,
        )
    else:
        raise ValueError(f"device_properties has to be an instance of DeviceCapabilities.")

    return device_emulator_properties
