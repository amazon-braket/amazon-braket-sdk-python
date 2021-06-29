# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from braket.circuits import CompositeOperator, QuantumOperator, Gate, QubitSet


@pytest.fixture
def composite_operator():
    return CompositeOperator(qubit_count=1, ascii_symbols=["foo"])


def test_is_operator(composite_operator):
    assert isinstance(composite_operator, QuantumOperator)


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_ir_not_implemented_by_default(composite_operator):
    composite_operator.to_ir(None)


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_matrix_not_implemented_by_default(composite_operator):
    composite_operator.to_matrix(None)


@pytest.mark.xfail(raises=ValueError)
def test_incorrect_length_ascii():
    CompositeOperator(qubit_count=2, ascii_symbols=["foo", "bar"])


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_matrix_not_implemented_by_default(composite_operator):
    composite_operator.matrix_equivalence(composite_operator)


def test_decompose_return_empty_list_by_default(composite_operator):
    assert composite_operator.decompose(QubitSet([1])) == []


def test_str(composite_operator):
    expected = "{}('qubit_count': {})".format(composite_operator.name, composite_operator.qubit_count)
    assert str(composite_operator) == expected


def test_equality():
    composite_operator_1 = CompositeOperator(qubit_count=1, ascii_symbols=["foo"])
    composite_operator_2 = CompositeOperator(qubit_count=1, ascii_symbols=["bar"])
    other_composite_operator = CompositeOperator.GHZ(qubit_count=2)
    non_composite_operator = Gate.H()

    assert composite_operator_1 == composite_operator_2
    assert composite_operator_1 is not composite_operator_2
    assert composite_operator_1 != other_composite_operator
    assert composite_operator_1 != non_composite_operator


def test_register_composite_operator():
    class _FooCompositeOperator(CompositeOperator):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["foo"])

    CompositeOperator.register_composite_operator(_FooCompositeOperator)
    assert CompositeOperator._FooCompositeOperator().name == _FooCompositeOperator().name
