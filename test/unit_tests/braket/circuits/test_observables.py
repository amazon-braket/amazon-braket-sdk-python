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

import math

import numpy as np
import numpy.testing as npt
import pytest

from braket.circuits import Gate, Observable
from braket.circuits.observables import observable_from_ir
from braket.circuits.quantum_operator_helpers import get_pauli_eigenvalues
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
)

testdata = [
    (Observable.I(), Gate.I(), ["i"], (), np.array([1, 1])),
    (Observable.X(), Gate.X(), ["x"], tuple([Gate.H()]), get_pauli_eigenvalues(1)),
    (
        Observable.Y(),
        Gate.Y(),
        ["y"],
        tuple([Gate.Z(), Gate.S(), Gate.H()]),
        get_pauli_eigenvalues(1),
    ),
    (Observable.Z(), Gate.Z(), ["z"], (), get_pauli_eigenvalues(1)),
    (Observable.H(), Gate.H(), ["h"], tuple([Gate.Ry(-math.pi / 4)]), get_pauli_eigenvalues(1)),
]

invalid_hermitian_matrices = [
    (np.array([[1]])),
    (np.array([1])),
    (np.array([0, 1, 2])),
    (np.array([[0, 1], [1, 2], [3, 4]])),
    (np.array([[0, 1, 2], [2, 3]], dtype=object)),
    (np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]])),
    (Gate.T().to_matrix()),
]


@pytest.mark.parametrize(
    "testobject,gateobject,expected_ir,basis_rotation_gates,eigenvalues", testdata
)
def test_to_ir(testobject, gateobject, expected_ir, basis_rotation_gates, eigenvalues):
    expected = expected_ir
    actual = testobject.to_ir()
    assert actual == expected


@pytest.mark.parametrize(
    "observable, observable_with_targets, serialization_properties, target, expected_ir",
    [
        (
            Observable.I(),
            Observable.I(3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "i(q[3])",
        ),
        (
            Observable.I(),
            Observable.I(3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "i($3)",
        ),
        (
            Observable.I(),
            None,
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            None,
            "i all",
        ),
        (
            Observable.X(),
            Observable.X(3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "x(q[3])",
        ),
        (
            Observable.X(),
            Observable.X(3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "x($3)",
        ),
        (
            Observable.X(),
            None,
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            None,
            "x all",
        ),
        (
            Observable.Y(),
            Observable.Y(3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "y(q[3])",
        ),
        (
            Observable.Y(),
            Observable.Y(3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "y($3)",
        ),
        (
            Observable.Y(),
            None,
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            None,
            "y all",
        ),
        (
            Observable.Z(),
            Observable.Z(3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "z(q[3])",
        ),
        (
            Observable.Z(),
            Observable.Z(3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "z($3)",
        ),
        (
            Observable.Z(),
            None,
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            None,
            "z all",
        ),
        (
            Observable.H(),
            Observable.H(3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3],
            "h(q[3])",
        ),
        (
            Observable.H(),
            Observable.H(3),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "h($3)",
        ),
        (
            Observable.H(),
            None,
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            None,
            "h all",
        ),
        (
            Observable.Hermitian(np.eye(4)),
            Observable.Hermitian(np.eye(4), targets=[1, 2]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [1, 2],
            "hermitian([[1+0im, 0im, 0im, 0im], [0im, 1+0im, 0im, 0im], "
            "[0im, 0im, 1+0im, 0im], [0im, 0im, 0im, 1+0im]]) q[1], q[2]",
        ),
        (
            Observable.Hermitian(np.eye(4)),
            Observable.Hermitian(np.eye(4), targets=[1, 2]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [1, 2],
            "hermitian([[1+0im, 0im, 0im, 0im], [0im, 1+0im, 0im, 0im], "
            "[0im, 0im, 1+0im, 0im], [0im, 0im, 0im, 1+0im]]) $1, $2",
        ),
        (
            Observable.Hermitian(np.eye(2)),
            None,
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            None,
            "hermitian([[1+0im, 0im], [0im, 1+0im]]) all",
        ),
        (
            Observable.H() @ Observable.Z(),
            Observable.H(3) @ Observable.Z(0),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3, 0],
            "h(q[3]) @ z(q[0])",
        ),
        (
            Observable.H() @ Observable.Z(),
            Observable.H(3) @ Observable.Z(0),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3, 0],
            "h($3) @ z($0)",
        ),
        (
            Observable.H() @ Observable.Z() @ Observable.I(),
            Observable.H(3) @ Observable.Z(0) @ Observable.I(1),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3, 0, 1],
            "h(q[3]) @ z(q[0]) @ i(q[1])",
        ),
        (
            Observable.H() @ Observable.Z() @ Observable.I(),
            Observable.H(3) @ Observable.Z(0) @ Observable.I(1),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3, 0, 1],
            "h($3) @ z($0) @ i($1)",
        ),
        (
            Observable.Hermitian(np.eye(4)) @ Observable.I(),
            Observable.Hermitian(np.eye(4), targets=[3, 0]) @ Observable.I(1),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
            [3, 0, 1],
            "hermitian([[1+0im, 0im, 0im, 0im], [0im, 1+0im, 0im, 0im], "
            "[0im, 0im, 1+0im, 0im], [0im, 0im, 0im, 1+0im]]) q[3], q[0]"
            " @ i(q[1])",
        ),
        (
            Observable.I() @ Observable.Hermitian(np.eye(4)),
            Observable.I(3) @ Observable.Hermitian(np.eye(4), targets=[0, 1]),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3, 0, 1],
            "i($3) @ "
            "hermitian([[1+0im, 0im, 0im, 0im], [0im, 1+0im, 0im, 0im], "
            "[0im, 0im, 1+0im, 0im], [0im, 0im, 0im, 1+0im]]) $0, $1",
        ),
        (
            3 * (2 * Observable.Z()),
            3 * (2 * Observable.Z(3)),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3],
            "6 * z($3)",
        ),
        (
            (2 * Observable.I()) @ (2 * Observable.Hermitian(np.eye(4))),
            (2 * Observable.I(3)) @ (2 * Observable.Hermitian(np.eye(4), targets=[0, 1])),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [3, 0, 1],
            "4 * i($3) @ "
            "hermitian([[1+0im, 0im, 0im, 0im], [0im, 1+0im, 0im, 0im], "
            "[0im, 0im, 1+0im, 0im], [0im, 0im, 0im, 1+0im]]) $0, $1",
        ),
        (
            Observable.Z() + 2 * Observable.H(),
            Observable.Z(3) + 2 * Observable.H(4),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [[3], [4]],
            "z($3) + 2 * h($4)",
        ),
        (
            3 * (Observable.H() + 2 * Observable.X()),
            3 * (Observable.H(3) + 2 * Observable.X(0)),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [[3], [0]],
            "3 * h($3) + 6 * x($0)",
        ),
        (
            3 * (Observable.H() + 2 * Observable.H()),
            3 * (Observable.H(3) + 2 * Observable.H(3)),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [[3], [3]],
            "3 * h($3) + 6 * h($3)",
        ),
        (
            3 * (Observable.H() + 2 * Observable.H()),
            3 * (Observable.H(3) + 2 * Observable.H(5)),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [[3], [5]],
            "3 * h($3) + 6 * h($5)",
        ),
        (
            (2 * Observable.Y()) @ (3 * Observable.I()) + 0.75 * Observable.Y() @ Observable.Z(),
            (2 * Observable.Y(0)) @ (3 * Observable.I(1))
            + 0.75 * Observable.Y(0) @ Observable.Z(1),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [[0, 1], [0, 1]],
            "6 * y($0) @ i($1) + 0.75 * y($0) @ z($1)",
        ),
        (
            (-2 * Observable.Y()) @ (3 * Observable.I()) + -0.75 * Observable.Y() @ Observable.Z(),
            (-2 * Observable.Y(0)) @ (3 * Observable.I(1))
            + -0.75 * Observable.Y(0) @ Observable.Z(1),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [[0, 1], [0, 1]],
            "-6 * y($0) @ i($1) - 0.75 * y($0) @ z($1)",
        ),
        (
            4 * (2 * Observable.Z() + 2 * (3 * Observable.X() @ (2 * Observable.Y()))),
            4 * (2 * Observable.Z(0) + 2 * (3 * Observable.X(1) @ (2 * Observable.Y(2)))),
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [[0], [1, 2]],
            "8 * z($0) + 48 * x($1) @ y($2)",
        ),
        (
            4 * (2 * Observable.Z(0) + 2 * (3 * Observable.X(1) @ (2 * Observable.Y(2)))),
            None,
            OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.PHYSICAL),
            [[5], [4, 3]],
            "8 * z($5) + 48 * x($4) @ y($3)",
        ),
    ],
)
def test_observables_to_ir_openqasm(
    observable,
    observable_with_targets,
    serialization_properties,
    target,
    expected_ir,
):
    assert (
        observable.to_ir(
            target, ir_type=IRType.OPENQASM, serialization_properties=serialization_properties
        )
        == expected_ir
    )
    if observable_with_targets:
        assert (
            observable_with_targets.to_ir(
                None, ir_type=IRType.OPENQASM, serialization_properties=serialization_properties
            )
            == expected_ir
        )


@pytest.mark.parametrize(
    "observable",
    [
        2 * Observable.H(),
        3 * Observable.Z(),
        2 * Observable.I(),
        3 * Observable.X(),
        2 * Observable.Y(),
        2 * Observable.Hermitian(matrix=np.array([[0, 1], [1, 0]])),
        2 * Observable.TensorProduct([Observable.Z(), Observable.H()]),
    ],
)
def test_observable_coef_jaqcd(observable):
    coef_not_supported_with_jaqcd = "Observable coefficients not supported with Jaqcd"
    with pytest.raises(ValueError, match=coef_not_supported_with_jaqcd):
        observable.to_ir(target=0, ir_type=IRType.JAQCD)


@pytest.mark.parametrize(
    "expression, observable",
    [
        ([], Observable.X()),
        ([2], Observable.Y()),
        ([2, "invalid_str"], Observable.Z()),
        ([2.0], Observable.Hermitian(matrix=np.array([[0, 1], [1, 0]]))),
        ([2], Observable.Sum([Observable.X() + Observable.Y()])),
        ([2], Observable.Y() + 0.75 * Observable.Y() @ Observable.Z()),
    ],
)
def test_invalid_scalar_multiplication(expression, observable):
    with pytest.raises(TypeError, match="Observable coefficients must be numbers."):
        expression * observable


@pytest.mark.parametrize(
    "observable, matrix",
    [
        (
            (-3 * Observable.H()).to_matrix(),
            np.array([
                [-2.12132034 + 0.0j, -2.12132034 + 0.0j],
                [-2.12132034 + 0.0j, 2.12132034 - 0.0j],
            ]),
        ),
        (
            (3 * Observable.Z()).to_matrix(),
            np.array([[3.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -3.0 + 0.0j]]),
        ),
        (
            (2 * Observable.I()).to_matrix(),
            np.array([[2.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 2.0 + 0.0j]]),
        ),
        (
            (1.2 * Observable.X()).to_matrix(),
            np.array([[0.0 + 0.0j, 1.2 + 0.0j], [1.2 + 0.0j, 0.0 + 0.0j]]),
        ),
        (
            (1e-2 * Observable.Y()).to_matrix(),
            np.array([[0.0 + 0.0j, 0.0 - 0.01j], [0 + 0.01j, 0.0 + 0.0j]]),
        ),
        (
            (np.array(1.3) * Observable.Hermitian(matrix=np.array([[0, 1], [1, 0]]))).to_matrix(),
            np.array([[0.0 + 0.0j, 1.3 + 0.0j], [1.3 + 0.0j, 0.0 + 0.0j]]),
        ),
        (
            (2 * Observable.TensorProduct([Observable.Z(), Observable.H()])).to_matrix(),
            np.array(
                [
                    [1.41421356 + 0.0j, 1.41421356 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j],
                    [1.41421356 + 0.0j, -1.41421356 + 0.0j, 0.0 + 0.0j, -0.0 + 0.0j],
                    [0.0 + 0.0j, 0.0 + 0.0j, -1.41421356 + 0.0j, -1.41421356 + 0.0j],
                    [0.0 + 0.0j, -0.0 + 0.0j, -1.41421356 + 0.0j, 1.41421356 + 0.0j],
                ],
            ),
        ),
    ],
)
def test_valid_scaled_matrix(observable, matrix):
    npt.assert_allclose(observable, matrix)


@pytest.mark.parametrize(
    "observable, eigenvalue",
    [
        (-2 * Observable.I().eigenvalues, np.array([-2.0, -2.0])),
        (
            3e-2 * Observable.Hermitian(matrix=np.array([[0, 1], [1, 0]])).eigenvalues,
            np.array([-0.03, 0.03]),
        ),
    ],
)
def test_valid_scaled_eigenvalues(observable, eigenvalue):
    npt.assert_allclose(observable, eigenvalue)


@pytest.mark.parametrize(
    "testobject,gateobject,expected_ir,basis_rotation_gates,eigenvalues", testdata
)
def test_gate_equality(testobject, gateobject, expected_ir, basis_rotation_gates, eigenvalues):
    assert testobject.qubit_count == gateobject.qubit_count
    assert testobject.ascii_symbols == gateobject.ascii_symbols
    assert testobject.matrix_equivalence(gateobject)
    assert testobject.basis_rotation_gates == basis_rotation_gates
    assert np.allclose(testobject.eigenvalues, eigenvalues)


@pytest.mark.parametrize(
    "testobject,gateobject,expected_ir,basis_rotation_gates,eigenvalues", testdata
)
def test_basis_rotation_gates(
    testobject, gateobject, expected_ir, basis_rotation_gates, eigenvalues
):
    assert testobject.basis_rotation_gates == basis_rotation_gates


@pytest.mark.parametrize(
    "testobject,gateobject,expected_ir,basis_rotation_gates,eigenvalues", testdata
)
def test_eigenvalues(testobject, gateobject, expected_ir, basis_rotation_gates, eigenvalues):
    compare_eigenvalues(testobject, eigenvalues)


@pytest.mark.parametrize(
    "testobject,gateobject,expected_ir,basis_rotation_gates,eigenvalues", testdata
)
def test_observable_from_ir(testobject, gateobject, expected_ir, basis_rotation_gates, eigenvalues):
    assert testobject == observable_from_ir(expected_ir)


# Hermitian


@pytest.mark.parametrize("matrix", invalid_hermitian_matrices)
def test_hermitian_invalid_matrix(matrix):
    with pytest.raises(ValueError):
        Observable.Hermitian(matrix=matrix)


def test_hermitian_equality():
    matrix = Observable.H().to_matrix()
    a1 = Observable.Hermitian(matrix=matrix)
    a2 = Observable.Hermitian(matrix=matrix)
    a3 = Observable.Hermitian(matrix=Observable.I().to_matrix())
    a4 = "hi"
    assert a1 == a2
    assert a1 != a3
    assert a1 != a4


def test_hermitian_to_ir():
    matrix = Observable.I().to_matrix()
    obs = Observable.Hermitian(matrix=matrix)
    assert obs.to_ir() == [[[[1, 0], [0, 0]], [[0, 0], [1, 0]]]]


@pytest.mark.parametrize(
    "matrix,eigenvalues",
    [
        (np.array([[1.0, 0.0], [0.0, 1.0]]), np.array([1, 1])),
        (np.array([[0, -1j], [1j, 0]]), np.array([-1.0, 1.0])),
        (np.array([[1, 1 - 1j], [1 + 1j, -1]]), np.array([-np.sqrt(3), np.sqrt(3)])),
    ],
)
def test_hermitian_eigenvalues(matrix, eigenvalues):
    compare_eigenvalues(Observable.Hermitian(matrix=matrix), eigenvalues)


def test_hermitian_matrix_target_mismatch():
    with pytest.raises(ValueError):
        Observable.Hermitian(np.eye(4), targets=[0, 1, 2])


def test_flattened_tensor_product():
    observable_one = Observable.Z() @ Observable.Y()
    observable_two = Observable.X() @ Observable.H()
    actual = Observable.TensorProduct([observable_one, observable_two])
    expected = Observable.TensorProduct([
        Observable.Z(),
        Observable.Y(),
        Observable.X(),
        Observable.H(),
    ])
    assert expected == actual


@pytest.mark.parametrize(
    "matrix,basis_rotation_matrix",
    [
        (
            np.array([[0.0, 1.0], [1.0, 0.0]]),
            np.array([[-0.70710678, 0.70710678], [0.70710678, 0.70710678]]).conj().T,
        ),
        (
            np.array([[0, -1j], [1j, 0]]),
            np.array([
                [-0.70710678 + 0.0j, -0.70710678 + 0.0j],
                [0.0 + 0.70710678j, 0.0 - 0.70710678j],
            ])
            .conj()
            .T,
        ),
        (
            np.array([[1, 1 - 1j], [1 + 1j, -1]]),
            np.array([
                [-0.45970084 - 0.0j, 0.62796303 - 0.62796303j],
                [-0.88807383 - 0.0j, -0.32505758 + 0.32505758j],
            ]),
        ),
    ],
)
def test_hermitian_basis_rotation_gates(matrix, basis_rotation_matrix):
    expected_unitary = Gate.Unitary(matrix=basis_rotation_matrix)
    actual_rotation_gates = Observable.Hermitian(matrix=matrix).basis_rotation_gates
    assert actual_rotation_gates == (expected_unitary,)
    assert expected_unitary.matrix_equivalence(actual_rotation_gates[0])


def test_observable_from_ir_hermitian_value_error():
    ir_observable = [[[[1.0, 0], [0, 1]], [[0.0, 1], [1, 0]]]]
    with pytest.raises(ValueError):
        observable_from_ir(ir_observable)


def test_observable_from_ir_hermitian():
    ir_observable = [[[[1, 0], [0, 0]], [[0, 0], [1, 0]]]]
    actual_observable = observable_from_ir(ir_observable)
    assert actual_observable == Observable.Hermitian(matrix=np.array([[1.0, 0.0], [0.0, 1.0]]))


def test_hermitian_str():
    assert (
        str(Observable.Hermitian(matrix=np.array([[1.0, 0.0], [0.0, 1.0]])))
        == "Hermitian('qubit_count': 1, 'matrix': [[1.+0.j 0.+0.j], [0.+0.j 1.+0.j]])"
    )


# TensorProduct


def test_tensor_product_to_ir():
    t = Observable.TensorProduct([Observable.Z(), Observable.I(), Observable.X()])
    assert t.to_ir() == ["z", "i", "x"]
    assert t.qubit_count == 3
    assert t.ascii_symbols == tuple(["Z@I@X"] * 3)


def test_tensor_product_matmul_tensor():
    t1 = Observable.TensorProduct([Observable.Z(), Observable.I(), Observable.X()])
    t2 = Observable.TensorProduct([
        Observable.Hermitian(matrix=Observable.I().to_matrix()),
        Observable.Y(),
    ])
    t3 = t1 @ t2
    assert t3.to_ir() == ["z", "i", "x", [[[1.0, 0], [0, 0]], [[0, 0], [1.0, 0]]], "y"]
    assert t3.qubit_count == 5
    assert t3.ascii_symbols == tuple(["Z@I@X@Hermitian@Y"] * 5)


def test_tensor_product_matmul_observable():
    t1 = Observable.TensorProduct([Observable.Z(), Observable.I(), Observable.X()])
    o1 = Observable.I()
    t = t1 @ o1
    assert t.to_ir() == ["z", "i", "x", "i"]
    assert t.qubit_count == 4
    assert t.ascii_symbols == tuple(["Z@I@X@I"] * 4)


def test_tensor_product_eigenvalue_index_out_of_bounds():
    obs = Observable.TensorProduct([Observable.Z(), Observable.I(), Observable.X()])
    with pytest.raises(ValueError):
        obs.eigenvalue(8)


def test_tensor_product_value_error():
    with pytest.raises(TypeError):
        Observable.TensorProduct([Observable.Z(), Observable.I(), Observable.X()]) @ "a"


def test_tensor_product_rmatmul_observable():
    t1 = Observable.TensorProduct([Observable.Z(), Observable.I(), Observable.X()])
    o1 = Observable.I()
    t = o1 @ t1
    assert t.to_ir() == ["i", "z", "i", "x"]
    assert t.qubit_count == 4
    assert t.ascii_symbols == tuple(["I@Z@I@X"] * 4)


@pytest.mark.parametrize(
    "observable,eigenvalues",
    [
        (Observable.X() @ Observable.Y(), np.array([1, -1, -1, 1])),
        (Observable.X() @ Observable.Y() @ Observable.Z(), np.array([1, -1, -1, 1, -1, 1, 1, -1])),
        (Observable.X() @ Observable.Y() @ Observable.I(), np.array([1, 1, -1, -1, -1, -1, 1, 1])),
        (
            Observable.X()
            @ Observable.Hermitian(
                np.array([[-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
            )
            @ Observable.Y(),
            np.array([-1, 1, -1, 1, 1, -1, 1, -1, 1, -1, 1, -1, -1, 1, -1, 1]),
        ),
    ],
)
def test_tensor_product_eigenvalues(observable, eigenvalues):
    compare_eigenvalues(observable, eigenvalues)
    # Test caching
    observable._factors = ()
    compare_eigenvalues(observable, eigenvalues)


@pytest.mark.parametrize(
    "observable,basis_rotation_gates",
    [
        (Observable.X() @ Observable.Y(), (Gate.H(), Gate.Z(), Gate.S(), Gate.H())),
        (
            Observable.X() @ Observable.Y() @ Observable.Z(),
            (Gate.H(), Gate.Z(), Gate.S(), Gate.H()),
        ),
        (
            Observable.X() @ Observable.Y() @ Observable.I(),
            (Gate.H(), Gate.Z(), Gate.S(), Gate.H()),
        ),
        (Observable.X() @ Observable.H(), (Gate.H(), Gate.Ry(-np.pi / 4))),
    ],
)
def test_tensor_product_basis_rotation_gates(observable, basis_rotation_gates):
    assert observable.basis_rotation_gates == basis_rotation_gates


def test_tensor_product_repeated_qubits():
    with pytest.raises(ValueError):
        (2 * Observable.Z(3)) @ (3 * Observable.H(3))


def test_tensor_product_with_and_without_targets():
    with pytest.raises(ValueError):
        (2 * Observable.Z(3)) @ (3 * Observable.H())


def test_observable_from_ir_tensor_product():
    expected_observable = Observable.TensorProduct([Observable.Z(), Observable.I(), Observable.X()])
    actual_observable = observable_from_ir(["z", "i", "x"])
    assert expected_observable == actual_observable


def test_observable_from_ir_tensor_product_value_error():
    with pytest.raises(ValueError):
        observable_from_ir(["z", "i", "foo"])


def compare_eigenvalues(observable, expected):
    assert np.allclose(observable.eigenvalues, expected)
    assert np.allclose(
        np.array([observable.eigenvalue(i) for i in range(2**observable.qubit_count)]),
        expected,
    )


def test_sum_not_allowed_in_tensor_product():
    sum_not_allowed_in_tensor_product = "Sum observables not allowed in TensorProduct"
    with pytest.raises(TypeError, match=sum_not_allowed_in_tensor_product):
        Observable.TensorProduct([Observable.X() + Observable.Y()])


# Sum of observables


@pytest.mark.parametrize(
    "observable,basis_rotation_gates",
    [(Observable.X() + Observable.Y(), (Gate.H(), Gate.Z(), Gate.S(), Gate.H()))],
)
def test_no_basis_rotation_support_for_sum(observable, basis_rotation_gates):
    no_basis_rotation_support_for_sum = "Basis rotation calculation not supported for Sum"
    with pytest.raises(NotImplementedError, match=no_basis_rotation_support_for_sum):
        observable.basis_rotation_gates


def test_no_eigenvalues_support_for_sum():
    no_eigen_value_support = "Eigenvalue calculation not supported for Sum"
    with pytest.raises(NotImplementedError, match=no_eigen_value_support):
        (Observable.X() + Observable.Y()).eigenvalues


def test_matrix_not_supported_for_sum():
    matrix_not_supported = "Matrix operation is not supported for Sum"
    with pytest.raises(NotImplementedError, match=matrix_not_supported):
        (Observable.X() + Observable.Y()).to_matrix()


def test_invalid_targets_config_for_sum_obs():
    observable, serialization_properties = (
        2 * Observable.X() @ Observable.Y() + 0.75 * Observable.Y() @ Observable.Z(),
        OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
    )
    target = [[0, 1]]

    target_len_mismatch_for_sum_terms = "Invalid target of length 1 for Sum with 2 terms"

    with pytest.raises(ValueError, match=target_len_mismatch_for_sum_terms):
        observable.to_ir(
            target, ir_type=IRType.OPENQASM, serialization_properties=serialization_properties
        )


def test_sum_obs_str():
    assert (
        str(Observable.Sum([2 * Observable.X() + 3 * Observable.Y()]))
        == "Sum(X('qubit_count': 1), Y('qubit_count': 1))"
    )


def test_str_equality_sum_obs():
    t1 = Observable.Sum([2 * Observable.X() + 3 * Observable.Y()])
    t2 = Observable.Sum([2 * Observable.X() + 3 * Observable.Y()])
    t3 = Observable.Sum([2 * Observable.Z() + 3 * Observable.H()])
    t4 = Observable.Sum([Observable.Z() + Observable.H()])
    assert t1 == t2
    assert t2 != t3
    assert t1 != t3
    assert t3 == t4


def test_invalid_target_length_for_sum_obs_term():
    observable, serialization_properties = (
        2 * Observable.Y() + 0.75 * Observable.Y() @ Observable.Z(),
        OpenQASMSerializationProperties(qubit_reference_type=QubitReferenceType.VIRTUAL),
    )
    target = [[0, 1], [0, 1]]

    invalid_target_len_for_term = "Invalid target for term 0 of Sum. Expected 1 targets, got 2"

    with pytest.raises(ValueError, match=invalid_target_len_for_term):
        observable.to_ir(
            target, ir_type=IRType.OPENQASM, serialization_properties=serialization_properties
        )


def test_unscaled_tensor_product():
    observable = 3 * ((2 * Observable.X()) @ (5 * Observable.Y()))
    assert observable == 30 * (Observable.X() @ Observable.Y())
    assert observable._unscaled() == Observable.X() @ Observable.Y()


def test_sum_with_and_without_targets():
    with pytest.raises(ValueError):
        Observable.X() + 3 * Observable.Y(4)
