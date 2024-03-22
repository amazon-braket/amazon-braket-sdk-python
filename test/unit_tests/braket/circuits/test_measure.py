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
def ascii_symbols():
    return ["foo"]


@pytest.fixture
def measure(ascii_symbols):
    return Measure(qubit_count=1, ascii_symbols=ascii_symbols)


def test_is_operator(measure):
    assert isinstance(measure, QuantumOperator)


def test_ascii_symbols(measure, ascii_symbols):
    assert measure.ascii_symbols == tuple(ascii_symbols)


def test_none_ascii():
    with pytest.raises(ValueError):
        Measure(ascii_symbols=None)


def test_equality():
    measure1 = Measure()
    measure2 = Measure(qubit_count=1, ascii_symbols=["M"])
    non_measure = "non measure"

    assert measure1 == measure2
    assert measure1 is not measure2
    assert measure1 != non_measure


def test_str(measure):
    assert str(measure) == measure.name


@pytest.mark.parametrize(
    "ir_type, serialization_properties, expected_exception, expected_message",
    [
        (
            IRType.JAQCD,
            None,
            NotImplementedError,
            "Measure instructions are not supported with JAQCD.",
        ),
        ("invalid-ir-type", None, ValueError, "Supplied ir_type invalid-ir-type is not supported."),
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
            Measure(qubit_count=4, ascii_symbols=["M", "M", "M", "M"]),
            [1, 4],
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "b[0] = measure $1;b[1] = measure $4;",
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
