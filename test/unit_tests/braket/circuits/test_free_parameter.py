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

import numpy as np
import pytest

from braket.circuits import FreeParameter

valid_params = [
    1,
    np.pi,
]


@pytest.fixture
def free_parameter():
    return FreeParameter("theta")


def test_is_free_param(free_parameter):
    assert isinstance(free_parameter, FreeParameter)


def test_equality():
    param_1 = FreeParameter("theta")
    param_2 = FreeParameter("theta")
    param_3 = FreeParameter("theta")
    other_param = FreeParameter("phi")
    non_param = "non circuit"

    param_3.fix_value(0)

    assert param_1 == param_2
    assert param_1 == param_3
    assert param_1 is not param_2
    assert param_1 != other_param
    assert param_1 != non_param


def test_str(free_parameter):
    expected = "theta"
    assert str(free_parameter) == expected


def test_hash(free_parameter):
    assert hash(free_parameter) == hash(tuple(free_parameter.name))


@pytest.mark.xfail(raises=ValueError)
def test_invalid_params(free_parameter):
    param_values = {1, 2, "braket"}
    free_parameter.fix_value(param_values)


@pytest.mark.parametrize("param_vals", valid_params)
def test_valid_params(param_vals):
    theta = FreeParameter("theta")
    theta.fix_value(param_vals)


@pytest.mark.parametrize("param_value", valid_params)
def test_fix_value(param_value):
    theta = FreeParameter("theta")
    theta.fix_value(param_value)

    assert theta.parameter_value == float(param_value)
