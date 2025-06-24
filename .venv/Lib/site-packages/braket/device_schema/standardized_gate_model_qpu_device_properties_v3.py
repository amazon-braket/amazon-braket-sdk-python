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

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic.v1 import BaseModel, Field, confloat

from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


class TimeUnit(str, Enum):
    """
    Enum for time unit.
    """

    SECOND = "s"
    MILLISECOND = "ms"
    MICROSECOND = "us"
    NANOSECOND = "ns"


class FidelityUnit(str, Enum):
    """
    Enum for fidelity value unit.
    """

    FRACTION = "fraction"


class FidelityTypeName(str, Enum):
    """
    Enum for fidelity type.
    """

    RANDOMIZED_BENCHMARKING = "RANDOMIZED_BENCHMARKING"


class FidelityType(BaseModel):
    """
    Fidelity measurement types
    Attributes:
        name (str): name of the fidelity type
        description (Optional[str]): description for how the fidelity
            measurement was performed
    """

    name: FidelityTypeName
    description: Optional[str]


class Fidelity(BaseModel):
    """
    Describes fidelity of a component or a system
    Attributes:
        fidelityType (FidelityType): The fidelity measurement technique used
            for the presented value
        fidelity (float): The measured fidelity value
        standardError (Optional[float]): The expected error value reported
            on the measurement
        unit (FidelityUnit): The expected unit for the fidelity
    """

    fidelityType: Optional[FidelityType]
    fidelity: confloat(ge=0, le=1)
    standardError: Optional[confloat(ge=0, le=1)] = None
    unit: FidelityUnit


class Duration(BaseModel):
    """
    Time duration
    Attributes:
        value (float): The measured time duration value
        standardError (Optional[float]): The statistical error or uncertainty in the measured value
        unit (TimeUnit): The unit for the duration value
    """

    value: float
    standardError: Optional[float]
    unit: TimeUnit


class OneQubitProperties(BaseModel):
    """
    The standard one-qubit calibration details for a quantum hardware provider
    Attributes:
        oneQubitFidelity: A list of fidelity measurements for the qubit.
            This typically includes metrics like randomized benchmarking results that
            characterize the performance of single-qubit operations.
    """

    oneQubitFidelity: list[Fidelity]


class StandardizedGateModelQpuDeviceProperties(BraketSchemaBase):
    """
    Braket standarized gate model device qpu properties for the given quantum hardware

    Attributes:
        oneQubitProperties (dict[str, OneQubitProperties]): Dictionary mapping specific qubit
            identifiers (ex: '1') to their calibration property sets, including fidelity measurements.
        T1 (Optional[Duration]): The T1 time of the device.
        T2 (Optional[Duration]): The T2 time of the device.
        ReadoutFidelity (Optional[list[Fidelity]]): The fidelity of the readout operation on the device.
        ReadoutDuration (Optional[Duration]): The time required to perform a measurement/readout operation.
        SingleQubitGateDuration (Optional[Duration]): The typical duration of a single-qubit gate operation.
        TwoQubitGateFidelity (Optional[list[Fidelity]]): The fidelity of two-qubit gate operation.
        TwoQubitGateDuration (Optional[Duration]): The typical duration of a two-qubit gate operation.
    Examples:
        >>> import json
        >>> valid_input = {
        ...     "braketSchemaHeader": {
        ...         "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
        ...         "version": "3"
        ...     },
        ...     "oneQubitProperties": {
        ...         "0": {
        ...             "oneQubitFidelity": [
        ...                 {
        ...                     "fidelityType": {
        ...                         "name": "RANDOMIZED_BENCHMARKING",
        ...                         "description": "Single qubit randomized benchmarking"
        ...                     },
        ...                     "fidelity": 0.9985,
        ...                     "standardError": 0.0003,
        ...                     "unit": "fraction"
        ...                 }
        ...             ]
        ...         },
        ...         "1": {
        ...             "oneQubitFidelity": [
        ...                 {
        ...                     "fidelityType": {
        ...                         "name": "RANDOMIZED_BENCHMARKING",
        ...                         "description": "Single qubit randomized benchmarking"
        ...                     },
        ...                     "fidelity": 0.9982,
        ...                     "standardError": 0.0004,
        ...                     "unit": "fraction"
        ...                 }
        ...             ]
        ...         }
        ...     },
        ...     "T1": {
        ...         "value": 50.0,
        ...         "standardError": 2.5,
        ...         "unit": "s"
        ...     },
        ...     "T2": {
        ...         "value": 30.0,
        ...         "standardError": 1.5,
        ...         "unit": "s"
        ...     },
        ...     "readoutFidelity": [{
        ...         "fidelity": 0.9950,
        ...         "standardError": 0.0010,
        ...         "unit": "fraction"
        ...     }],
        ...     "readoutDuration": {
        ...         "value": 0.000350,
        ...         "standardError": 0.000010,
        ...         "unit": "s"
        ...     },
        ...     "singleQubitGateDuration": {
        ...         "value": 0.000020,
        ...         "standardError": 0.000002,
        ...         "unit": "s"
        ...     },
        ...     "singleQubitFidelity": [{
        ...          "fidelityType": {
        ...             "name": "RANDOMIZED_BENCHMARKING",
        ...             "description": "Single qubit randomized benchmarking"
        ...         },
        ...         "fidelity": 0.9950,
        ...         "standardError": 0.0010,
        ...         "unit": "fraction"
        ...     }],
        ...     "twoQubitGateFidelity": [{
        ...          "fidelityType": {
        ...             "name": "RANDOMIZED_BENCHMARKING",
        ...             "description": "Single qubit randomized benchmarking"
        ...         },
        ...         "fidelity": 0.9950,
        ...         "standardError": 0.0010,
        ...         "unit": "fraction"
        ...     }],
        ...     "twoQubitGateDuration": {
        ...         "value": 0.000200,
        ...         "standardError": 0.000010,
        ...         "unit": "s"
        ...     },
        ...     "updatedAt": "2025-02-22T12:29:03Z"
        ... }
        >>> StandardizedGateModelQpuDeviceProperties.parse_raw_schema(json.dumps(valid_input))
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.standardized_gate_model_qpu_device_properties", version="3"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    oneQubitProperties: Optional[dict[str, OneQubitProperties]]
    T1: Optional[Duration]
    T2: Optional[Duration]
    readoutFidelity: Optional[list[Fidelity]]
    readoutDuration: Optional[Duration]
    singleQubitGateDuration: Optional[Duration]
    singleQubitFidelity: Optional[list[Fidelity]]
    twoQubitGateFidelity: Optional[list[Fidelity]]
    twoQubitGateDuration: Optional[Duration]
    updatedAt: Optional[datetime]
