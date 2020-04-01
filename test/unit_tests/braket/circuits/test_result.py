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
from braket.circuits import Result


@pytest.fixture
def result():
    return Result(ascii_symbol="foo")


@pytest.fixture
def prob():
    return Result.Probability([0, 1])


@pytest.fixture
def sv():
    return Result.StateVector()


@pytest.mark.xfail(raises=ValueError)
def test_none_ascii():
    Result(ascii_symbol=None)


def test_name(result):
    expected = result.__class__.__name__
    assert result.name == expected


def test_ascii_symbol():
    ascii_symbol = "foo"
    result = Result(ascii_symbol=ascii_symbol)
    assert result.ascii_symbol == ascii_symbol


def test_equality():
    result1 = Result.StateVector()
    result2 = Result.StateVector()
    result3 = Result.Probability([1])
    result4 = "hi"
    assert result1 == result2
    assert result1 != result3
    assert result1 != result4


@pytest.mark.xfail(raises=AttributeError)
def test_ascii_symbol_setter(result):
    result.ascii_symbol = "bar"


@pytest.mark.xfail(raises=AttributeError)
def test_name_setter(result):
    result.name = "hi"


@pytest.mark.xfail(raises=NotImplementedError)
def test_to_ir_not_implemented_by_default(result):
    result.to_ir(None)


def test_register_result():
    class _FooResult(Result):
        def __init__(self):
            super().__init__(ascii_symbol="foo")

    Result.register_result(_FooResult)
    assert Result._FooResult().name == _FooResult().name


def test_copy_creates_new_object(prob):
    copy = prob.copy()
    assert copy == prob
    assert copy is not prob


def test_copy_with_mapping_target(sv):
    target_mapping = {0: 10, 1: 11}
    expected = Result.StateVector()
    assert sv.copy(target_mapping=target_mapping) == expected


def test_copy_with_mapping_target_hasattr(prob):
    target_mapping = {0: 10, 1: 11}
    expected = Result.Probability([10, 11])
    assert prob.copy(target_mapping=target_mapping) == expected


def test_copy_with_target_hasattr(prob):
    target = [10, 11]
    expected = Result.Probability(target)
    assert prob.copy(target=target) == expected


def test_copy_with_target(sv):
    target = [10, 11]
    expected = Result.StateVector()
    assert sv.copy(target=target) == expected


@pytest.mark.xfail(raises=TypeError)
def test_copy_with_target_and_mapping(prob):
    prob.copy(target=[10], target_mapping={0: 10})
