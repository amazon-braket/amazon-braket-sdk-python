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

import pytest

from braket.circuits.measure import Measure
from braket.circuits.quantum_operator import QuantumOperator
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
)


@pytest.fixture
def measure():
    return Measure()


def test_is_operator(measure):
    assert isinstance(measure, QuantumOperator)


def test_equality():
    measure1 = Measure()
    measure2 = Measure()
    non_measure = "non measure"

    assert measure1 == measure2
    assert measure1 is not measure2
    assert measure1 != non_measure


def test_ascii_symbols(measure):
    assert measure.ascii_symbols == ("M",)


def test_str(measure):
    assert str(measure) == measure.name


@pytest.mark.parametrize(
    "ir_type, serialization_properties, expected_exception, expected_message",
    [
        (
            IRType.JAQCD,
            None,
            NotImplementedError,
            "measure instructions are not supported with JAQCD.",
        ),
        ("invalid-ir-type", None, ValueError, "supplied ir_type invalid-ir-type is not supported."),
    ],
)
def test_measure_to_ir(
    ir_type, serialization_properties, expected_exception, expected_message, measure
):
    with pytest.raises(expected_exception) as exc:
        measure.to_ir(ir_type=ir_type, serialization_properties=serialization_properties)
    assert exc.value.args[0] == expected_message


@pytest.mark.parametrize(
    "measure, target, serialization_properties, expected_ir",
    [
        (
            Measure(),
            [0],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "b[0] = measure q[0];",
        ),
        (
            Measure(),
            [1, 4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "\n".join([
                "b[0] = measure $1;",
                "b[1] = measure $4;",
            ]),
        ),
    ],
)
def test_measure_to_ir_openqasm(measure, target, serialization_properties, expected_ir):
    assert (
        measure.to_ir(
            target, ir_type=IRType.OPENQASM, serialization_properties=serialization_properties
        )
        == expected_ir
    )
