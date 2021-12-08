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

from braket.circuits import ParameterizedOperator


@pytest.fixture
def parameterized_operator():
    return ParameterizedOperator()


def test_is_parameterized_operator(parameterized_operator):
    assert isinstance(parameterized_operator, ParameterizedOperator)


def test_parameterized(parameterized_operator):
    expected = False
    assert parameterized_operator.parameterized == expected


def test_parameter(parameterized_operator):
    expected = None
    assert parameterized_operator.parameter == expected
