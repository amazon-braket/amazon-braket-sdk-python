import pytest
import math
from enum import Enum
from unittest.mock import patch, MagicMock

from braket.experimental_capabilities import (
    ExperimentalCapability,
    EnableExperimentalCapability,
    list_capabilities,
    IqmExperimentalCapabilities,
)
from braket.experimental_capabilities.experimental_capability_context import (
    GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT,
    ExperimentalCapabilityContextError,
)
from braket.experimental_capabilities.experimental_capability import register_capabilities
from braket.experimental_capabilities.iqm.classical_control import CCPRx, MeasureFF
from braket.circuits import Circuit
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.serialization import IRType, OpenQASMSerializationProperties


def reset_capabilities_context():
    """Reset the experimental capabilities context."""
    for cap_name in GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.capabilities:
        GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT._capabilities[cap_name] = False


# Tests for CCPRx quantum operator
def test_ccprx_requires_capability():
    reset_capabilities_context()
    # Without enabling the capability, CCPRx should raise an error
    with pytest.raises(ExperimentalCapabilityContextError):
        CCPRx(0.1, 0.2, 0)


def test_ccprx_with_capability():
    reset_capabilities_context()
    # With capability enabled, CCPRx should work
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        cc_prx = CCPRx(math.pi / 2, math.pi / 4, 0)
        assert cc_prx.parameters == [math.pi / 2, math.pi / 4, 0]

        # Test in a circuit
        circuit = Circuit()
        circuit.cc_prx(0, math.pi / 2, math.pi / 4, 0)
        # Check that the circuit has the instruction
        assert len(circuit.instructions) == 1
        assert isinstance(circuit.instructions[0].operator, CCPRx)


def test_ccprx_with_free_parameters():
    reset_capabilities_context()
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        # Create CCPRx with FreeParameter
        theta = FreeParameter("theta")
        phi = FreeParameter("phi")

        cc_prx = CCPRx(theta, phi, 0)
        assert cc_prx.parameters == [theta, phi, 0]

        # Test in a circuit
        circuit = Circuit()
        circuit.cc_prx(0, theta, phi, 0)

        # Check that the parameters are preserved
        assert circuit.instructions[0].operator.parameters[0] == theta
        assert circuit.instructions[0].operator.parameters[1] == phi


# Tests for MeasureFF quantum operator
def test_measure_ff_requires_capability():
    reset_capabilities_context()
    # Without enabling the capability, MeasureFF should raise an error
    with pytest.raises(ExperimentalCapabilityContextError):
        MeasureFF(0)


def test_measure_ff_with_capability():
    reset_capabilities_context()
    # With capability enabled, MeasureFF should work
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        measure_ff = MeasureFF(0)
        assert measure_ff.parameters == [0]

        # Test in a circuit
        circuit = Circuit()
        circuit.measure_ff(0, 0)
        # Check that the circuit has the instruction
        assert len(circuit.instructions) == 1
        assert isinstance(circuit.instructions[0].operator, MeasureFF)


def test_measure_ff_properties():
    reset_capabilities_context()
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        measure_ff = MeasureFF(0)


# Test serialization to IR
def test_ccprx_to_ir():
    reset_capabilities_context()
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        cc_prx = CCPRx(math.pi / 2, math.pi / 4, 0)
        target = [0]
        serialization_props = OpenQASMSerializationProperties(qubit_reference_type="indexed")

        ir = cc_prx.to_ir(
            target=target, ir_type=IRType.OPENQASM, serialization_properties=serialization_props
        )

        # Check the generated IR string
        assert ir == "cc_prx(1.5707963267948966, 0.7853981633974483, 0) $0;"


def test_measure_ff_to_ir():
    reset_capabilities_context()
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        measure_ff = MeasureFF(0)
        target = [0]
        serialization_props = OpenQASMSerializationProperties(qubit_reference_type="indexed")

        ir = measure_ff.to_ir(
            target=target, ir_type=IRType.OPENQASM, serialization_properties=serialization_props
        )

        # Check the generated IR string
        assert ir == "measure_ff(0) $0;"


# Test unsupported IR type
def test_unsupported_ir_type():
    reset_capabilities_context()
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        cc_prx = CCPRx(math.pi / 2, math.pi / 4, 0)
        target = [0]

        # Using JAQCD should raise an error
        with pytest.raises(ValueError):
            cc_prx.to_ir(target=target, ir_type=IRType.JAQCD)


def test_mixing_standard_and_experimental_operations():
    reset_capabilities_context()
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        # Create a circuit with both standard and experimental operations
        circuit = Circuit()
        circuit.h(0)  # Standard Hadamard gate
        circuit.cc_prx(0, math.pi / 2, math.pi / 4, 0)  # Experimental gate
        circuit.cnot(0, 1)  # Standard CNOT gate
        circuit.measure_ff(0, 1)  # Experimental measurement

        # Verify the circuit has all operations
        assert len(circuit.instructions) == 4


# Test integration with AWS device (mocked)
@patch("braket.aws.AwsDevice")
def test_circuit_with_classical_control_e2e(mock_aws_device_class):
    reset_capabilities_context()
    # Mock the device run and result methods
    mock_device = MagicMock()
    mock_task = MagicMock()
    mock_result = MagicMock()
    mock_result.measurement_counts = {"0": 46, "1": 54}
    mock_task.result.return_value = mock_result
    mock_device.run.return_value = mock_task
    mock_aws_device_class.return_value = mock_device

    device = mock_aws_device_class("arn:aws:braket:us-west-2::device/qpu/iqm/Garnet")

    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        circuit = Circuit()
        circuit.cc_prx(1, math.pi / 2, math.pi / 2, 0)
        circuit.measure_ff(1, 0)

    circuit = Circuit().add_verbatim_box(circuit)
    result = device.run(circuit, shots=100).result()

    # Check that the device was called with the right arguments
    device.run.assert_called_once()
    assert device.run.call_args[0][0] == circuit
    assert device.run.call_args[1]["shots"] == 100

    # Check the result
    assert result.measurement_counts == {"0": 46, "1": 54}


# Test for validation of the example.py functionality
def test_example_expected_to_fail():
    reset_capabilities_context()
    # The expected failing example from example.py
    circuit = Circuit()

    # Without enabling the capability, this should fail
    with pytest.raises(Exception):
        circuit.cc_prx(1, math.pi / 2, math.pi / 2, 0)
        circuit.measure_ff(1, 0)
