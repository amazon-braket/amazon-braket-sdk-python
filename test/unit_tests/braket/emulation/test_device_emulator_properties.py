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

import pytest
from braket.device_schema.device_capabilities import DeviceCapabilities
from braket.device_schema.device_paradigm import DeviceParadigm
from braket.device_schema.device_connectivity import DeviceConnectivity
from braket.device_schema.device_action_properties import DeviceActionProperties
from braket.device_schema.device_service_properties import DeviceServiceProperties
from braket.device_schema.standardized_gate_model_qpu_device_properties_v1 import (
    StandardizedGateModelQpuDeviceProperties,
    OneQubitProperties,
    TwoQubitProperties,
)
from braket.device_schema.result_type import ResultType
from braket.device_schema.error_mitigation.error_mitigation_scheme import ErrorMitigationScheme
from braket.device_schema.error_mitigation.error_mitigation_properties import (
    ErrorMitigationProperties,
)
from braket.emulation.device_emulator_properties import (
    DeviceEmulatorProperties,
    distill_device_emulator_properties,
)
from braket.emulation.device_emulator_utils import DEFAULT_SUPPORTED_RESULT_TYPES


def test_valid_initialization():
    """Test valid initialization of DeviceEmulatorProperties"""
    props = DeviceEmulatorProperties(
        qubitCount=2,
        nativeGateSet=["h", "cnot"],
        connectivityGraph={"0": ["1"], "1": ["0"]},
        oneQubitProperties={
            "0": OneQubitProperties(t1=100, t2=100),
            "1": OneQubitProperties(t1=100, t2=100),
        },
        twoQubitProperties={"0-1": TwoQubitProperties(fidelity=0.99)},
    )
    assert props.qubitCount == 2
    assert props.nativeGateSet == ["h", "cnot"]
    assert props.connectivityGraph == {"0": ["1"], "1": ["0"]}
    assert isinstance(props.oneQubitProperties["0"], OneQubitProperties)
    assert isinstance(props.twoQubitProperties["0-1"], TwoQubitProperties)
    assert props.supportedResultTypes == DEFAULT_SUPPORTED_RESULT_TYPES
    assert props.errorMitigation == {}


def test_invalid_qubit_count():
    """Test initialization with invalid qubit count"""
    with pytest.raises(ValueError, match="qubitCount must be a positive integer"):
        DeviceEmulatorProperties(
            qubitCount=0,
            nativeGateSet=["h"],
            connectivityGraph={},
            oneQubitProperties={},
            twoQubitProperties={},
        )


def test_invalid_native_gate():
    """Test initialization with invalid native gate"""
    with pytest.raises(ValueError, match="Gate 'invalid_gate' is not a valid Braket gate"):
        DeviceEmulatorProperties(
            qubitCount=1,
            nativeGateSet=["invalid_gate"],
            connectivityGraph={},
            oneQubitProperties={},
            twoQubitProperties={},
        )


def test_invalid_connectivity_graph_node():
    """Test initialization with invalid connectivity graph node"""
    with pytest.raises(
        ValueError, match="Node abc in connectivityGraph must be a string of digits"
    ):
        DeviceEmulatorProperties(
            qubitCount=2,
            nativeGateSet=["h"],
            connectivityGraph={"abc": ["1"]},
            oneQubitProperties={},
            twoQubitProperties={},
        )


def test_invalid_connectivity_graph_neighbor():
    """Test initialization with invalid connectivity graph neighbor"""
    with pytest.raises(ValueError, match="Neighbor xyz for node 0 must be a string of digits"):
        DeviceEmulatorProperties(
            qubitCount=2,
            nativeGateSet=["h"],
            connectivityGraph={"0": ["xyz"]},
            oneQubitProperties={},
            twoQubitProperties={},
        )


def test_invalid_connectivity_graph_qubit_range():
    """Test initialization with invalid qubit index in connectivity graph"""
    with pytest.raises(
        ValueError, match="Node 2 in connectivityGraph must represent a valid qubit index"
    ):
        DeviceEmulatorProperties(
            qubitCount=2,
            nativeGateSet=["h"],
            connectivityGraph={"2": ["0"]},
            oneQubitProperties={},
            twoQubitProperties={},
        )


def test_invalid_one_qubit_properties():
    """Test initialization with invalid one qubit properties"""
    with pytest.raises(
        ValueError, match="Each element in oneQubitProperties must be a OneQubitProperties"
    ):
        DeviceEmulatorProperties(
            qubitCount=1,
            nativeGateSet=["h"],
            connectivityGraph={},
            oneQubitProperties={"0": "invalid"},
            twoQubitProperties={},
        )


def test_invalid_two_qubit_properties():
    """Test initialization with invalid two qubit properties"""
    with pytest.raises(
        ValueError, match="Each element in twoQubitProperties must be a TwoQubitProperties"
    ):
        DeviceEmulatorProperties(
            qubitCount=2,
            nativeGateSet=["cnot"],
            connectivityGraph={},
            oneQubitProperties={},
            twoQubitProperties={"0-1": "invalid"},
        )


def test_invalid_result_types():
    """Test initialization with invalid result types"""
    invalid_result_type = ResultType(name="invalid_type")
    with pytest.raises(ValueError, match="Invalid result type"):
        DeviceEmulatorProperties(
            qubitCount=1,
            nativeGateSet=["h"],
            connectivityGraph={},
            oneQubitProperties={},
            twoQubitProperties={},
            supportedResultTypes=[invalid_result_type],
        )


def test_invalid_error_mitigation():
    """Test initialization with invalid error mitigation"""
    with pytest.raises(
        ValueError, match="Error mitigation scheme must be of type ErrorMitigationScheme"
    ):
        DeviceEmulatorProperties(
            qubitCount=1,
            nativeGateSet=["h"],
            connectivityGraph={},
            oneQubitProperties={},
            twoQubitProperties={},
            errorMitigation={"invalid": {}},
        )


def test_distill_device_emulator_properties():
    """Test distilling device emulator properties from device capabilities"""
    # Create mock device capabilities
    device_capabilities = DeviceCapabilities(
        provider=DeviceServiceProperties(
            errorMitigation={
                ErrorMitigationScheme.DEBIAS: ErrorMitigationProperties(minimumShots=1000)
            }
        ),
        paradigm=DeviceParadigm(
            qubitCount=2,
            nativeGateSet=["h", "cnot"],
            connectivity=DeviceConnectivity(connectivityGraph={"0": ["1"], "1": ["0"]}),
        ),
        standardized=StandardizedGateModelQpuDeviceProperties(
            oneQubitProperties={"0": OneQubitProperties(t1=100, t2=100)},
            twoQubitProperties={"0-1": TwoQubitProperties(fidelity=0.99)},
        ),
        action={
            "braket.ir.openqasm.program": DeviceActionProperties(
                supportedResultTypes=DEFAULT_SUPPORTED_RESULT_TYPES
            )
        },
    )

    props = distill_device_emulator_properties(device_capabilities)

    assert props.qubitCount == 2
    assert props.nativeGateSet == ["h", "cnot"]
    assert props.connectivityGraph == {"0": ["1"], "1": ["0"]}
    assert isinstance(props.oneQubitProperties["0"], OneQubitProperties)
    assert isinstance(props.twoQubitProperties["0-1"], TwoQubitProperties)
    assert props.supportedResultTypes == DEFAULT_SUPPORTED_RESULT_TYPES
    assert ErrorMitigationScheme.DEBIAS in props.errorMitigation


def test_distill_device_emulator_properties_invalid_input():
    """Test distilling device emulator properties with invalid input"""
    with pytest.raises(
        ValueError, match="device_properties has to be an instance of DeviceCapabilities"
    ):
        distill_device_emulator_properties("invalid")
