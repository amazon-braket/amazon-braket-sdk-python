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

import braket.ir.jaqcd as ir
from braket.circuits import Circuit, Observable, ResultType
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.result_type import ObservableParameterResultType
from braket.circuits.result_types import ObservableResultType
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
)

testdata = [
    (ResultType.StateVector, "state_vector", ir.StateVector, {}, {}),
    (ResultType.DensityMatrix, "density_matrix", ir.DensityMatrix, {}, {}),
    (
        ResultType.DensityMatrix,
        "density_matrix",
        ir.DensityMatrix,
        {"target": [0, 1]},
        {"targets": [0, 1]},
    ),
    (ResultType.Amplitude, "amplitude", ir.Amplitude, {"state": ["0"]}, {"states": ["0"]}),
    (
        ResultType.Probability,
        "probability",
        ir.Probability,
        {"target": [0, 1]},
        {"targets": [0, 1]},
    ),
    (
        ResultType.Probability,
        "probability",
        ir.Probability,
        {"target": None},
        {},
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
        ResultType.Expectation,
        "expectation",
        ir.Expectation,
        {"observable": Observable.Hermitian(matrix=Observable.I().to_matrix()), "target": None},
        {"observable": [[[[1.0, 0], [0, 0]], [[0, 0], [1.0, 0]]]]},
    ),
    (
        ResultType.Sample,
        "sample",
        ir.Sample,
        {"observable": Observable.Z(), "target": [0]},
        {"observable": ["z"], "targets": [0]},
    ),
    (
        ResultType.Sample,
        "sample",
        ir.Sample,
        {"observable": Observable.Z(), "target": None},
        {"observable": ["z"]},
    ),
    (
        ResultType.Variance,
        "variance",
        ir.Variance,
        {"observable": Observable.Z(), "target": [0]},
        {"observable": ["z"], "targets": [0]},
    ),
    (
        ResultType.Variance,
        "variance",
        ir.Variance,
        {"observable": Observable.Z(), "target": None},
        {"observable": ["z"]},
    ),
    (
        ResultType.AdjointGradient,
        "adjoint_gradient",
        ir.AdjointGradient,
        {"observable": Observable.Z(), "target": None, "parameters": None},
        {"observable": ["z"]},
    ),
    (
        ResultType.AdjointGradient,
        "adjoint_gradient",
        ir.AdjointGradient,
        {"observable": Observable.Z(), "target": [0], "parameters": ["alpha", "beta"]},
        {"observable": ["z"], "targets": [0], "parameters": ["alpha", FreeParameter("beta")]},
    ),
    (
        ResultType.AdjointGradient,
        "adjoint_gradient",
        ir.AdjointGradient,
        {
            "observable": Observable.Hermitian(matrix=Observable.Z().to_matrix()),
            "target": [0],
            "parameters": ["alpha", "beta"],
        },
        {
            "observable": [[[[1.0, 0], [0, 0]], [[0, 0], [-1.0, 0]]]],
            "targets": [0],
            "parameters": ["alpha", "beta"],
        },
    ),
]


@pytest.mark.parametrize("testclass,subroutine_name,irclass,input,ir_input", testdata)
def test_ir_result_level(testclass, subroutine_name, irclass, input, ir_input):
    if testclass == ResultType.AdjointGradient:
        jaqcd_not_implemented = "to_jaqcd has not been implemented yet."
        with pytest.raises(NotImplementedError, match=jaqcd_not_implemented):
            testclass(**input).to_ir()
    else:
        expected = irclass(**ir_input)
        actual = testclass(**input).to_ir()
        assert actual == expected


@pytest.mark.parametrize(
    "result_type, serialization_properties, expected_ir",
    [
        (
            ResultType.Expectation(Observable.I(), target=0),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result expectation i(q[0])",
        ),
        (
            ResultType.Expectation(Observable.I()),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result expectation i all",
        ),
        (
            ResultType.StateVector(),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result state_vector",
        ),
        (
            ResultType.DensityMatrix(),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result density_matrix all",
        ),
        (
            ResultType.DensityMatrix([0, 2]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result density_matrix q[0], q[2]",
        ),
        (
            ResultType.DensityMatrix(0),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "#pragma braket result density_matrix $0",
        ),
        (
            ResultType.Amplitude(["01", "10"]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            '#pragma braket result amplitude "01", "10"',
        ),
        (
            ResultType.Probability(),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result probability all",
        ),
        (
            ResultType.Probability([0, 2]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result probability q[0], q[2]",
        ),
        (
            ResultType.Probability(0),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            "#pragma braket result probability $0",
        ),
        (
            ResultType.Sample(Observable.I(), target=0),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result sample i(q[0])",
        ),
        (
            ResultType.Sample(Observable.I()),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result sample i all",
        ),
        (
            ResultType.Variance(Observable.I(), target=0),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result variance i(q[0])",
        ),
        (
            ResultType.Variance(Observable.I()),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result variance i all",
        ),
        (
            ResultType.AdjointGradient(Observable.I(), target=0, parameters=["alpha", "beta"]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result adjoint_gradient expectation(i(q[0])) alpha, beta",
        ),
        (
            ResultType.AdjointGradient(Observable.I(), target=0, parameters=["alpha"]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result adjoint_gradient expectation(i(q[0])) alpha",
        ),
        (
            ResultType.AdjointGradient(
                Observable.H() @ Observable.I(),
                target=[0, 1],
                parameters=[FreeParameter("alpha"), "beta", FreeParameter("gamma")],
            ),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result adjoint_gradient expectation(h(q[0]) @ i(q[1])) "
            "alpha, beta, gamma",
        ),
        (
            ResultType.AdjointGradient(
                Observable.H() @ Observable.I() + 2 * Observable.Z(),
                target=[[0, 1], [2]],
                parameters=[FreeParameter("alpha"), "beta", FreeParameter("gamma")],
            ),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result adjoint_gradient expectation(h(q[0]) @ i(q[1]) + 2 * z(q[2])) "
            "alpha, beta, gamma",
        ),
        (
            ResultType.AdjointGradient(Observable.I(), target=0, parameters=[]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result adjoint_gradient expectation(i(q[0])) all",
        ),
        (
            ResultType.AdjointGradient(
                Observable.X() @ Observable.Y(), target=[0, 1], parameters=[]
            ),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result adjoint_gradient expectation(x(q[0]) @ y(q[1])) all",
        ),
        (
            ResultType.AdjointGradient(
                Observable.Hermitian(matrix=Observable.I().to_matrix()), target=0, parameters=[]
            ),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result adjoint_gradient expectation(hermitian([[1+0im, 0im], "
            "[0im, 1+0im]]) q[0]) all",
        ),
        (
            ResultType.AdjointGradient(
                Observable.H(0) @ Observable.I(1) + 2 * Observable.Z(2),
                parameters=[FreeParameter("alpha"), "beta", FreeParameter("gamma")],
            ),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result adjoint_gradient expectation(h(q[0]) @ i(q[1]) + 2 * z(q[2])) "
            "alpha, beta, gamma",
        ),
        (
            ResultType.AdjointGradient(
                Observable.H(0) @ Observable.I(1) + 2 * Observable.Z(2),
                target=[[3, 4], [5]],
                parameters=[FreeParameter("alpha"), "beta", FreeParameter("gamma")],
            ),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            "#pragma braket result adjoint_gradient expectation(h(q[3]) @ i(q[4]) + 2 * z(q[5])) "
            "alpha, beta, gamma",
        ),
    ],
)
def test_result_to_ir_openqasm(result_type, serialization_properties, expected_ir):
    assert (
        result_type.to_ir(IRType.OPENQASM, serialization_properties=serialization_properties)
        == expected_ir
    )


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


@pytest.mark.parametrize(
    "state",
    ((["2", "11"]), ([1, 0]), ([0.1, 0]), ("-0", "1"), (["", ""]), (None), ([None, None]), ("10")),
)
def test_amplitude_init_invalid_state_value_error(state):
    with pytest.raises(ValueError):
        ResultType.Amplitude(state=state)


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


# AdjointGradient


def test_adjoint_gradient_parent_class():
    assert isinstance(
        ResultType.AdjointGradient(
            observable=Observable.X(), target=0, parameters=["alpha", FreeParameter("beta")]
        ),
        ObservableParameterResultType,
    )


@pytest.mark.parametrize(
    "target",
    (
        [[0], [0, 1], [2]],
        [[0, 1], [0, 1]],
    ),
)
def test_incorrect_target_adjoint_gradient(target):
    match = (
        "Sum observable's target shape must be a nested list "
        "where each term's target length is equal to the observable term's qubits count."
    )
    with pytest.raises(ValueError, match=match):
        ResultType.AdjointGradient(
            2 * Observable.Z() + 3 * Observable.X() @ Observable.Y(),
            target,
        )
