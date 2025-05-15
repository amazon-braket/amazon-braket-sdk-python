from __future__ import annotations
import math
from unittest.mock import MagicMock, patch

import pytest

from braket.circuits import Circuit
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.serialization import IRType, OpenQASMSerializationProperties
from braket.experimental_capabilities import (
    EnableExperimentalCapability,
    IqmExperimentalCapabilities,
)
from braket.experimental_capabilities.experimental_capability_context import (
    GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT,
    ExperimentalCapabilityContextError,
)
from braket.experimental_capabilities.iqm.classical_control import CCPRx, MeasureFF


def reset_capabilities_context():
    """Reset the experimental capabilities context."""
    for cap_name in GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.capabilities:
        GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT._capabilities[cap_name] = False


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

        circuit = Circuit()
        circuit.cc_prx(0, math.pi / 2, math.pi / 4, 0)
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

        circuit = Circuit()
        circuit.cc_prx(0, theta, phi, 0)
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

        circuit = Circuit()
        circuit.measure_ff(0, 0)
        assert len(circuit.instructions) == 1
        assert isinstance(circuit.instructions[0].operator, MeasureFF)


def test_measure_ff_properties():
    reset_capabilities_context()
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        measure_ff = MeasureFF(0)


def test_ccprx_to_ir():
    reset_capabilities_context()
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        cc_prx = CCPRx(math.pi / 2, math.pi / 4, 0)
        target = [0]
        serialization_props = OpenQASMSerializationProperties(qubit_reference_type="indexed")

        ir = cc_prx.to_ir(
            target=target, ir_type=IRType.OPENQASM, serialization_properties=serialization_props
        )

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

        assert ir == "measure_ff(0) $0;"


def test_unsupported_ir_type():
    reset_capabilities_context()
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        cc_prx = CCPRx(math.pi / 2, math.pi / 4, 0)
        target = [0]

        with pytest.raises(ValueError):
            cc_prx.to_ir(target=target, ir_type=IRType.JAQCD)


def test_mixing_standard_and_experimental_operations():
    reset_capabilities_context()
    with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
        circuit = Circuit()
        circuit.h(0)
        circuit.cc_prx(0, math.pi / 2, math.pi / 4, 0)
        circuit.cnot(0, 1)
        circuit.measure_ff(0, 1)

        assert len(circuit.instructions) == 4


@patch("braket.aws.AwsDevice")
def test_circuit_with_classical_control_e2e(mock_aws_device_class):
    reset_capabilities_context()

    expected_measurement_counts = {"0": 46, "1": 54}

    mock_device = MagicMock()
    mock_task = MagicMock()
    mock_result = MagicMock()
    mock_result.measurement_counts = expected_measurement_counts
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

    device.run.assert_called_once()
    assert device.run.call_args[0][0] == circuit
    assert device.run.call_args[1]["shots"] == 100
    assert result.measurement_counts == expected_measurement_counts


def test_example_expected_to_fail():
    reset_capabilities_context()
    circuit = Circuit()

    with pytest.raises(Exception):
        circuit.cc_prx(1, math.pi / 2, math.pi / 2, 0)
        circuit.measure_ff(1, 0)
