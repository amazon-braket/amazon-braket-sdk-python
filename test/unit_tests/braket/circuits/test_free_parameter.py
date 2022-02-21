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

from braket.circuits import FreeParameter


@pytest.fixture
def free_parameter():
    return FreeParameter("theta")


@pytest.mark.xfail(raises=TypeError)
def test_bad_input():
    FreeParameter(6)


def test_is_free_param(free_parameter):
    assert isinstance(free_parameter, FreeParameter)


def test_equality():
    param_1 = FreeParameter("theta")
    param_2 = FreeParameter("theta")
    other_param = FreeParameter("phi")
    non_param = "non circuit"

    assert param_1 == param_2
    assert param_1 is not param_2
    assert param_1 != other_param
    assert param_1 != non_param


def test_str(free_parameter):
    expected = "theta"
    assert str(free_parameter) == expected


def test_hash(free_parameter):
    assert hash(free_parameter) == hash(tuple(free_parameter.name))


def test_rep(free_parameter):
    assert repr(free_parameter) == free_parameter.name


def test_sub_successful(free_parameter):
    assert free_parameter.subs({"theta": 1}) == 1


def test_sub_wrong_param(free_parameter):
    assert free_parameter.subs({"alpha": 1}) == FreeParameter("theta")
