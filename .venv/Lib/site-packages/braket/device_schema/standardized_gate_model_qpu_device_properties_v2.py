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

from enum import Enum
from typing import Optional

from pydantic.v1 import BaseModel, Field, confloat

from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


class UnitType(str, Enum):
    """
    Enum for unit type.
    """

    ### Time
    SECOND = "s"

    ### Error
    FRACTION = "fraction"


class QubitDirection(str, Enum):
    """
    Enum for qubit direction labels for two-qubit fidelity details
    """

    CONTROL = "control"
    TARGET = "target"


class FidelityType(BaseModel):
    """
    Fidelity measurement types
    Attributes:
        name (str): description of the fidelity measurement
        description (Optional[str]): Optional description for how the fidelity
            measurement was performed
    """

    name: str
    description: Optional[str]


class GateFidelity2Q(BaseModel):
    """
    Describes the fidelity of two-qubit pairing
    Attributes:
        direction (Optional[Dict[QubitDirection, int]]): Describes which qubit is
            control/target for the pair. If direction is None the pair is considered
            bi-directional.
        gateName (str): the 2-qubit gate that the fidelity measurement was performed on
        fidelity (float): the fidelity value
        standardError (Optional[float]): Describes the error value on the fidelity measurement
        fidelityType (FidelityType): The fidelity measurement technique used
            for the presented value
    """

    direction: Optional[dict[QubitDirection, int]] = None
    gateName: str
    fidelity: confloat(ge=0, le=1)
    standardError: Optional[confloat(ge=0, le=1)] = None
    fidelityType: FidelityType
    unit: UnitType


class TwoQubitProperties(BaseModel):
    """
    The standard two-qubit calibration details for a quantum hardware provider
    Attributes:
        twoQubitGateFidelity: two qubit fidelity properties
    """

    twoQubitGateFidelity: list[GateFidelity2Q]


class Fidelity1Q(BaseModel):
    """
    Describes one qubit fidelity measured on a qubit
    Attributes:
        fidelityType (FidelityType): The fidelity measurement technique used
            for the presented value
        fidelity (float): The measured fidelity value
        standardError (Optional[float]): The expected error value reported
            on the measurement
        unit (UnitType): The expected unit for the fidelity
    """

    fidelityType: FidelityType
    fidelity: confloat(ge=0, le=1)
    standardError: Optional[confloat(ge=0, le=1)] = None
    unit: UnitType


class CoherenceTime(BaseModel):
    """
    The coherence time values provided for the device
    Attributes:
        value (str):  The coherence time value
        standardError (str): The error/confidence in coherence measurement provided
        unit (str): The unit for the described value
    """

    value: float
    standardError: Optional[float]
    unit: UnitType


class OneQubitProperties(BaseModel):
    """
    The standard one-qubit calibration details for a quantum hardware provider
    Attributes:
        T1: The T1 decoherence/relaxation time data structure
        T2: The T2 coherence/dephasing time
        oneQubitFidelity: one qubit fidelity properties
    """

    T1: CoherenceTime
    T2: CoherenceTime
    oneQubitFidelity: list[Fidelity1Q]


class StandardizedGateModelQpuDeviceProperties(BraketSchemaBase):
    """
 
    Braket standarized gate model device qpu properties for the given quantum hardware
 
    Attributes:
        oneQubitProperties (Dict[str, OneQubitProperties]): Dictionary describing a qubit
            identifier (ex: '1'), to the calibration property set
        twoQubitProperties (Dict[str, TwoQubitProperties]): Dictionary describing the
            two-qubit identifier (ex: '0-1'), to the calibration property set
    Examples:
        >>> import json
        >>> valid_input = {
        ...         "braketSchemaHeader": {
        ...             "name": \
        ...             "braket.device_schema.standardized_gate_model_qpu_device_properties",
        ...             "version": "2",
        ...         },
        ...         "oneQubitProperties": {
        ...             "0": {
        ...                 "T1": {"value": 28.9, "standardError": 0.01, "unit": "us"},
        ...                 "T2": {"value": 44.5, "standardError": 0.02, "unit": "us"},
        ...                 "oneQubitFidelity": [
        ...                     {
        ...                         "fidelityType": {
        ...                             "name": "RANDOMIZED_BENCHMARKING",
        ...                             "description": "uses a standard RB technique",
        ...                         },
        ...                         "fidelity": 0.9993,
        ...                     },
        ...                     {
        ...                         "fidelityType": {"name": "READOUT"},
        ...                         "fidelity": 0.903,
        ...                         "standardError": None,
        ...                     },
        ...                 ],
        ...             },
        ...             "1": {
        ...                 "T1": {"value": 28.9, "unit": "us"},
        ...                 "T2": {"value": 44.5, "standardError": 0.02, "unit": "us"},
        ...                 "oneQubitFidelity": [
        ...                     {
        ...                         "fidelityType": {"name": "RANDOMIZED_BENCHMARKING"},
        ...                         "fidelity": 0.9986,
        ...                         "standardError": None,
        ...                     },
        ...                     {
        ...                         "fidelityType": {"name": "READOUT"},
        ...                         "fidelity": 0.867,
        ...                         "standardError": None,
        ...                     },
        ...                 ],
        ...             },
        ...         },
        ...         "twoQubitProperties": {
        ...             "0-1": {
        ...                 "twoQubitGateFidelity": [
        ...                     {
        ...                         "direction": {"control": 0, "target": 1},
        ...                         "gateName": "CNOT",
        ...                         "fidelity": 0.877,
        ...                         "fidelityType": {"name": "INTERLEAVED_RANDOMIZED_BENCHMARKING"},
        ...                     }
        ...                 ]
        ...             },
        ...             "0-7": {
        ...                 "twoQubitGateFidelity": [
        ...                     {
        ...                         "direction": {"control": 0, "target": 7},
        ...                         "gateName": "CNOT",
        ...                         "fidelity": 0.877,
        ...                         "standardError": 0.001,
        ...                         "fidelityType": {"name": "INTERLEAVED_RANDOMIZED_BENCHMARKING"},
        ...                     }
        ...                 ]
        ...             },
        ...         },
        ...     }
        >>> StandardizedGateModelQpuDeviceProperties.parse_raw_schema(json.dumps(valid_input))
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.standardized_gate_model_qpu_device_properties", version="2"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    oneQubitProperties: dict[str, OneQubitProperties]
    twoQubitProperties: dict[str, TwoQubitProperties]
