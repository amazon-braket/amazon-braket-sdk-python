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

from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pytest

from braket.circuits import Circuit
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.serialization import IRType, OpenQASMSerializationProperties
from braket.experimental_capabilities import (
    EnableExperimentalCapability,
)
from braket.experimental_capabilities.experimental_capability_context import (
    ExperimentalCapabilityContextError,
)
from braket.experimental_capabilities.iqm.classical_control import CCPRx, MeasureFF
from braket.ir.openqasm import Program as OpenQasmProgram
import numpy as np


def test_ccprx_invalid_capability_context():
    # Without enabling the capability, CCPRx should raise an error
    with pytest.raises(ExperimentalCapabilityContextError):
        CCPRx(0.1, 0.2, 0)


def test_ccprx_with_capability():
    # With capability enabled, CCPRx should work
    with EnableExperimentalCapability():
        cc_prx = CCPRx(0.5, 0.8, 0)
        assert cc_prx.parameters == [0.5, 0.8, 0]
        assert cc_prx.ascii_symbols == ("0→CCPRx(0.50, 0.80)",)

        circuit = Circuit()
        circuit.cc_prx(0, math.pi / 2, math.pi / 4, 0)
        assert len(circuit.instructions) == 1
        assert isinstance(circuit.instructions[0].operator, CCPRx)


def test_ccprx_with_free_parameters():
    with EnableExperimentalCapability():
        # Create CCPRx with FreeParameter
        theta = FreeParameter("theta")
        phi = FreeParameter("phi")
        cc_prx = CCPRx(theta, phi, 0)
        assert cc_prx.parameters == [theta, phi, 0]

        circuit = Circuit()
        circuit.cc_prx(0, theta, phi, 0)
        assert circuit.instructions[0].operator.parameters[0] == theta
        assert circuit.instructions[0].operator.parameters[1] == phi


def test_measure_ff_invalid_capability_context():
    # Without enabling the capability, MeasureFF should raise an error
    with pytest.raises(ExperimentalCapabilityContextError):
        MeasureFF(0)


def test_measure_ff_with_capability():
    # With capability enabled, MeasureFF should work
    with EnableExperimentalCapability():
        measure_ff = MeasureFF(0)
        assert measure_ff.parameters == [0]
        assert measure_ff.ascii_symbols == ("MFF→0",)

        circuit = Circuit()
        circuit.measure_ff(0, 0)
        assert len(circuit.instructions) == 1
        assert isinstance(circuit.instructions[0].operator, MeasureFF)


def test_measure_ff_properties():
    with EnableExperimentalCapability():
        measure_ff = MeasureFF(0)


def test_ccprx_to_ir():
    with EnableExperimentalCapability():
        cc_prx = CCPRx(math.pi / 2, math.pi / 4, 0)
        target = [0]
        serialization_props = OpenQASMSerializationProperties(qubit_reference_type="indexed")

        ir = cc_prx.to_ir(
            target=target, ir_type=IRType.OPENQASM, serialization_properties=serialization_props
        )

        assert ir == "cc_prx(1.5707963267948966, 0.7853981633974483, 0) $0;"


def test_measure_ff_to_ir():
    with EnableExperimentalCapability():
        measure_ff = MeasureFF(0)
        target = [0]
        serialization_props = OpenQASMSerializationProperties(qubit_reference_type="indexed")

        ir = measure_ff.to_ir(
            target=target, ir_type=IRType.OPENQASM, serialization_properties=serialization_props
        )

        assert ir == "measure_ff(0) $0;"


def test_unsupported_ir_type():
    with EnableExperimentalCapability():
        cc_prx = CCPRx(math.pi / 2, math.pi / 4, 0)
        target = [0]

        with pytest.raises(ValueError):
            cc_prx.to_ir(target=target, ir_type=IRType.JAQCD)


def test_mixing_standard_and_experimental_operations():
    with EnableExperimentalCapability():
        circuit = Circuit()
        circuit.h(0)
        circuit.cc_prx(0, math.pi / 2, math.pi / 4, 0)
        circuit.cnot(0, 1)
        circuit.measure_ff(0, 1)

        assert len(circuit.instructions) == 4


@patch("braket.aws.AwsDevice")
def test_circuit_with_classical_control_e2e(mock_aws_device_class):
    expected_measurement_counts = {"0": 46, "1": 54}

    mock_device = MagicMock()
    mock_task = MagicMock()
    mock_result = MagicMock()
    mock_result.measurement_counts = expected_measurement_counts
    mock_task.result.return_value = mock_result
    mock_device.run.return_value = mock_task
    mock_aws_device_class.return_value = mock_device

    device = mock_aws_device_class("arn:aws:braket:us-west-2::device/qpu/iqm/Garnet")

    with EnableExperimentalCapability():
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
    circuit = Circuit()

    with pytest.raises(Exception):
        circuit.cc_prx(1, math.pi / 2, math.pi / 2, 0)
        circuit.measure_ff(1, 0)


def test_measureff_ccprx_from_ir():
    """Test that circuits with both standard and experimental gates can be reconstructed from IR."""
    with EnableExperimentalCapability():
        openqasm_source = """
        OPENQASM 3.0;
        bit[2] b;
        #pragma braket verbatim
        box{
            prx(3.141592653589793, 0.0) $1;
            measure_ff(0) $1;
            cc_prx(3.141592653589793, 0.0, 0) $1;
        }
        """
        ir = OpenQasmProgram(source=openqasm_source)
        circuit_from_ir = Circuit.from_ir(ir)
        assert len(circuit_from_ir.instructions) == 5

        assert circuit_from_ir.instructions[0].operator.name == "StartVerbatimBox"

        assert circuit_from_ir.instructions[1].operator.name == "PRx"
        assert isinstance(circuit_from_ir.instructions[2].operator, MeasureFF)
        assert isinstance(circuit_from_ir.instructions[3].operator, CCPRx)

        assert circuit_from_ir.instructions[4].operator.name == "EndVerbatimBox"

        instruction = circuit_from_ir.instructions[2]
        params = instruction.operator.parameters
        assert params[0] == 0
        assert instruction.target == [1]

        instruction = circuit_from_ir.instructions[3]
        params = instruction.operator.parameters
        assert np.isclose(params[0], 3.141592653589793)
        assert np.isclose(params[1], 0)
        assert params[2] == 0
        assert instruction.target == [1]
