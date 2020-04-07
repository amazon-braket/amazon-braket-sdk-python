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
from braket.circuits import Circuit, Observable, ResultType
from braket.circuits.result_types import ObservableResultType

testdata = [
    (ResultType.StateVector, "state_vector", ir.StateVector, {}, {}),
    (ResultType.Amplitude, "amplitude", ir.Amplitude, {"state": ["0"]}, {"states": ["0"]}),
    (
        ResultType.Probability,
        "probability",
        ir.Probability,
        {"target": [0, 1]},
        {"targets": [0, 1]},
    ),
    (
        ResultType.Expectation,
        "expectation",
        ir.Expectation,
        {"observable": Observable.Z(), "target": [0]},
        {"observable": ["z"], "targets": [0]},
    ),
    (
        ResultType.Expectation,
        "expectation",
        ir.Expectation,
        {"observable": Observable.Z() @ Observable.I() @ Observable.X(), "target": [0, 1, 2]},
        {"observable": ["z", "i", "x"], "targets": [0, 1, 2]},
    ),
    (
        ResultType.Expectation,
        "expectation",
        ir.Expectation,
        {"observable": Observable.Hermitian(matrix=Observable.I().to_matrix()), "target": [0]},
        {"observable": [[[[1.0, 0], [0, 0]], [[0, 0], [1.0, 0]]]], "targets": [0]},
    ),
    (
        ResultType.Sample,
        "sample",
        ir.Sample,
        {"observable": Observable.Z(), "target": [0]},
        {"observable": ["z"], "targets": [0]},
    ),
    (
        ResultType.Variance,
        "variance",
        ir.Variance,
        {"observable": Observable.Z(), "target": [0]},
        {"observable": ["z"], "targets": [0]},
    ),
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
    ResultType.Amplitude(state=None)


def test_amplitude_equality():
    a1 = ResultType.Amplitude(state=["0", "1"])
    a2 = ResultType.Amplitude(state=["0", "1"])
    a3 = ResultType.Amplitude(state=["01", "11", "10"])
    a4 = "hi"
    assert a1 == a2
    assert a1 != a3
    assert a1 != a4


# Probability


def test_probability_equality():
    a1 = ResultType.Probability([0, 1])
    a2 = ResultType.Probability([0, 1])
    a3 = ResultType.Probability([0, 1, 2])
    a4 = "hi"
    assert a1 == a2
    assert a1 != a3
    assert a1 != a4


# ObservableResultType


@pytest.mark.xfail(raises=ValueError)
def test_expectation_init_value_error_target():
    ObservableResultType(ascii_symbol="Obs", observable=Observable.X() @ Observable.Y(), target=[])


@pytest.mark.xfail(raises=ValueError)
def test_obs_rt_init_value_error_qubit_count():
    ObservableResultType(ascii_symbol="Obs", observable=Observable.X(), target=[0, 1])


def test_obs_rt_equality():
    a1 = ObservableResultType(ascii_symbol="Obs", observable=Observable.X(), target=0)
    a2 = ObservableResultType(ascii_symbol="Obs", observable=Observable.X(), target=0)
    a3 = ObservableResultType(ascii_symbol="Obs", observable=Observable.X(), target=1)
    a4 = "hi"
    assert a1 == a2
    assert a1 != a3
    assert a1 != a4


def test_obs_rt_repr():
    a1 = ObservableResultType(ascii_symbol="Obs", observable=Observable.X(), target=0)
    assert (
        str(a1)
        == f"ObservableResultType(observable=X('qubit_count': 1), target=QubitSet([Qubit(0)]))"
    )


# Expectation


def test_expectation_parent_class():
    assert isinstance(
        ResultType.Expectation(observable=Observable.X(), target=0), ObservableResultType
    )


# Sample


def test_sample_parent_class():
    assert isinstance(ResultType.Sample(observable=Observable.X(), target=0), ObservableResultType)


# Variance


def test_variance_parent_class():
    assert isinstance(
        ResultType.Variance(observable=Observable.X(), target=0), ObservableResultType
    )
