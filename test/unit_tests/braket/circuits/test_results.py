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

import braket.ir.jaqcd as ir
import pytest
from braket.circuits import Circuit, Result

testdata = [
    (Result.StateVector, "state_vector", ir.StateVector, {}, {}),
    (Result.Amplitude, "amplitude", ir.Amplitude, {"state": ["0"]}, {"states": ["0"]}),
    (Result.Probability, "probability", ir.Probability, {"target": [0, 1]}, {"targets": [0, 1]}),
]


@pytest.mark.parametrize("testclass,subroutine_name,irclass,input,ir_input", testdata)
def test_ir_result_level(testclass, subroutine_name, irclass, input, ir_input):
    expected = irclass(**ir_input)
    actual = testclass(**input).to_ir()
    assert actual == expected


@pytest.mark.parametrize("testclass,subroutine_name,irclass,input,ir_input", testdata)
def test_result_subroutine(testclass, subroutine_name, irclass, input, ir_input):
    subroutine = getattr(Circuit(), subroutine_name)
    assert subroutine(**input) == Circuit(testclass(**input))


@pytest.mark.parametrize("testclass,subroutine_name,irclass,input,ir_input", testdata)
def test_result_equality(testclass, subroutine_name, irclass, input, ir_input):
    a1 = testclass(**input)
    a2 = a1.copy()
    assert a1 == a2
    assert a1 is not a2


# Amplitude


@pytest.mark.xfail(raises=ValueError)
def test_amplitude_init_value_error():
    Result.Amplitude(state=None)


def test_amplitude_equality():
    a1 = Result.Amplitude(state=["0", "1"])
    a2 = Result.Amplitude(state=["0", "1"])
    a3 = Result.Amplitude(state=["01", "11", "10"])
    a4 = "hi"
    assert a1 == a2
    assert a1 != a3
    assert a1 != a4


# Probability


def test_probability_equality():
    a1 = Result.Probability([0, 1])
    a2 = Result.Probability([0, 1])
    a3 = Result.Probability([0, 1, 2])
    a4 = "hi"
    assert a1 == a2
    assert a1 != a3
    assert a1 != a4
