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

from braket.circuits import Observable, QuantumOperator, StandardObservable
from braket.circuits.serialization import IRType


@pytest.fixture
def observable():
    return Observable(qubit_count=1, ascii_symbols=["foo"])


@pytest.fixture
def standard_observable():
    return StandardObservable(ascii_symbols=["foo"])


@pytest.fixture
def unscaled_observable(observable):
    return observable._unscaled()


@pytest.fixture
def unscaled_standard_observable(standard_observable):
    return standard_observable._unscaled()


def test_is_operator(observable):
    assert isinstance(observable, QuantumOperator)


def test_qubit_count_lt_one():
    with pytest.raises(ValueError):
        Observable(qubit_count=0, ascii_symbols=[])


def test_none_ascii():
    with pytest.raises(ValueError):
        Observable(qubit_count=1, ascii_symbols=None)


def test_mismatch_length_ascii():
    with pytest.raises(ValueError):
        Observable(qubit_count=1, ascii_symbols=["foo", "bar"])


def test_name(observable):
    expected = observable.__class__.__name__
    assert observable.name == expected


def test_getters():
    qubit_count = 2
    ascii_symbols = ("foo", "bar")
    observable = Observable(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    assert observable.qubit_count == qubit_count
    assert observable.ascii_symbols == ascii_symbols


def test_qubit_count_setter(observable):
    with pytest.raises(AttributeError):
        observable.qubit_count = 10


def test_ascii_symbols_setter(observable):
    with pytest.raises(AttributeError):
        observable.ascii_symbols = ["foo", "bar"]


def test_name_setter(observable):
    with pytest.raises(AttributeError):
        observable.name = "hi"


@pytest.mark.parametrize(
    "ir_type, serialization_properties, expected_exception, expected_message",
    [
        (IRType.JAQCD, None, NotImplementedError, "to_jaqcd has not been implemented yet."),
        (IRType.OPENQASM, None, NotImplementedError, "to_openqasm has not been implemented yet."),
        ("invalid-ir-type", None, ValueError, "Supplied ir_type invalid-ir-type is not supported."),
        (
            IRType.OPENQASM,
            "invalid-property-type",
            ValueError,
            "serialization_properties must be of type OpenQASMSerializationProperties for "
            "IRType.OPENQASM.",
        ),
    ],
)
def test_observable_to_ir(
    ir_type, serialization_properties, expected_exception, expected_message, observable
):
    with pytest.raises(expected_exception) as exc:
        observable.to_ir(0, ir_type, serialization_properties=serialization_properties)
    assert exc.value.args[0] == expected_message


def test_to_matrix_not_implemented_by_default(observable):
    with pytest.raises(NotImplementedError):
        observable.to_matrix(None)


def test_basis_rotation_gates_not_implemented_by_default(observable):
    with pytest.raises(NotImplementedError):
        observable.basis_rotation_gates


def test_eigenvalues_not_implemented_by_default(observable):
    with pytest.raises(NotImplementedError):
        observable.eigenvalues


def test_eigenvalue_not_implemented_by_default(observable):
    with pytest.raises(NotImplementedError):
        observable.eigenvalue(0)


def test_str(observable):
    expected = f"{observable.name}('qubit_count': {observable.qubit_count})"
    assert str(observable) == expected
    assert observable.coefficient == 1


def test_register_observable():
    class _FooObservable(Observable):
        def __init__(self):
            super().__init__(qubit_count=1, ascii_symbols=["foo"])

    Observable.register_observable(_FooObservable)
    assert Observable._FooObservable().name == _FooObservable().name


def test_matmul_observable():
    o1 = Observable.I()
    o2 = Observable.Z()
    o3 = o1 @ o2
    assert isinstance(o3, Observable.TensorProduct)
    assert o3.qubit_count == 2
    assert o3.to_ir() == ["i", "z"]
    assert o3.ascii_symbols == ("I@Z", "I@Z")


def test_matmul_non_observable():
    with pytest.raises(TypeError):
        Observable.I() @ "a"


def test_observable_equality():
    o1 = Observable.I()
    o2 = Observable.I()
    o3 = Observable.Z()
    o4 = "a"
    assert o1 == o2
    assert o1 != o3
    assert o1 != o4


def test_standard_observable_subclass_of_observable(standard_observable):
    assert isinstance(standard_observable, Observable)


def test_unscaled_standard_observable_subclass_of_observable(unscaled_standard_observable):
    assert isinstance(unscaled_standard_observable, Observable)


def test_standard_observable_eigenvalues(standard_observable):
    assert np.allclose(standard_observable.eigenvalues, np.array([1, -1]))


def test_unscaled_standard_observable_eigenvalues(unscaled_standard_observable):
    assert np.allclose(unscaled_standard_observable.eigenvalues, np.array([1, -1]))


def test_observable_coeffs(observable):
    observable = 2 * observable
    assert observable.coefficient == 2
    unscaled_observable = observable._unscaled()
    assert unscaled_observable.coefficient == 1
    assert isinstance(unscaled_observable, Observable)


@pytest.mark.parametrize("parameter", ["foo", 1.2, -3])
def test_only_observables_sum_allowed(observable, parameter):
    add_observables_only = "Can only perform addition between observables."
    with pytest.raises(TypeError, match=add_observables_only):
        2 * observable + parameter


@pytest.mark.parametrize("parameter", ["foo", 1.2, -3])
def test_only_observables_subtraction_allowed(observable, parameter):
    add_observables_only = "Can only perform subtraction between observables."
    with pytest.raises(TypeError, match=add_observables_only):
        2 * observable - parameter


def test_sum_observable_with_subtraction():
    obs1 = 6 * Observable.X()
    obs2 = -4 * Observable.Y()
    result = obs1 - obs2
    assert isinstance(result, Observable.Sum)
    assert result.qubit_count == 1
    assert np.array_equal(result.summands, (6 * Observable.X(), -4 * Observable.Y()))
