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

# ruff: noqa: ANN201, PLC2801, S101

import pytest

from braket.circuits.observables import H, Sum, X
from braket.quantum_information import PauliString, PauliStringSum


def test_canonicalizes_duplicate_and_signed_terms():
    pauli_sum = PauliStringSum.from_list([
        (0.25, "XX"),
        (0.75, "+XX"),
        (2, "-YY"),
        (-2, "YY"),
        (0, "ZZ"),
    ])

    assert pauli_sum.to_list() == [(1.0, "XX"), (-4, "YY")]
    assert PauliString("XX") in pauli_sum
    assert PauliString("-YY") in pauli_sum
    assert "ZZ" not in pauli_sum


def test_round_trip_through_weighted_tuple_list_preserves_algebraic_meaning():
    original = PauliStringSum.from_list([(1, "ZX"), (-0.5, "IZ"), (0.5, "-IZ")])

    assert PauliStringSum.from_list(original.to_list()) == original
    assert original.to_list() == [(-1.0, "IZ"), (1, "ZX")]


def test_addition_subtraction_and_scalar_multiplication_are_canonical():
    pauli_sum = PauliString("XX") + PauliString("YY") - PauliString("-YY")

    assert pauli_sum == PauliStringSum.from_list([(1, "XX"), (2, "YY")])
    assert (0.5 * pauli_sum).to_list() == [(0.5, "XX"), (1.0, "YY")]
    assert (pauli_sum * 0).to_list() == []


def test_pauli_string_multiplication_distributes_over_sum():
    pauli_sum = PauliStringSum.from_list([(2, "XI"), (3, "IX")])

    assert (pauli_sum * PauliString("XX")).to_list() == [(2, "IX"), (3, "XI")]
    assert (PauliString("XX") * pauli_sum).to_list() == [(2, "IX"), (3, "XI")]


def test_sum_multiplication_distributes_and_merges_terms():
    left = PauliStringSum.from_list([(1, "XI"), (1, "IX")])
    right = PauliStringSum.from_list([(1, "XX")])

    assert (left * right).to_list() == [(1, "IX"), (1, "XI")]


def test_conversion_to_and_from_observable_sum_preserves_terms():
    pauli_sum = PauliStringSum.from_list([(2, "IX"), (-3, "ZY")])
    observable_sum = pauli_sum.to_sum()

    assert isinstance(observable_sum, Sum)
    assert PauliStringSum.from_sum(observable_sum) == pauli_sum


def test_from_observable_sum_with_manual_weighted_terms():
    observable_sum = Sum([2 * (X() @ X()), -3 * (X() @ X()), 0.5 * X()])

    assert PauliStringSum.from_sum(observable_sum).to_list() == [(0.5, "X"), (-1, "XX")]


def test_empty_sum_has_no_observable_sum_representation():
    with pytest.raises(ValueError, match="Cannot convert an empty PauliStringSum"):
        PauliStringSum.from_list([(1, "XX"), (-1, "XX")]).to_sum()


def test_from_sum_rejects_non_pauli_observables():
    with pytest.raises(ValueError, match="is not a Pauli observable"):
        PauliStringSum.from_sum(Sum([X(), H()]))


def test_commutation_checks():
    commuting = PauliStringSum.from_list([(1, "XX"), (2, "YY"), (3, "ZZ")])
    non_commuting = PauliStringSum.from_list([(1, "XI"), (1, "ZI")])

    assert commuting.is_self_commuting()
    assert commuting.commutes_with(PauliString("ZZ"))
    assert not non_commuting.is_self_commuting()
    assert not non_commuting.commutes_with(PauliString("XI"))


def test_length_mismatch_commutation_fails_explicitly():
    with pytest.raises(ValueError, match="same length"):
        PauliStringSum.from_list([(1, "XX")]).commutes_with(PauliString("X"))


def test_invalid_coefficient_fails_explicitly():
    with pytest.raises(TypeError, match="coefficients must be real numbers"):
        PauliStringSum.from_list([("bad", "XX")])
    with pytest.raises(TypeError, match="coefficients must be real numbers"):
        PauliStringSum.from_list([(1j, "XX")])


def test_indexing_and_iteration_are_deterministic():
    pauli_sum = PauliStringSum.from_list([(2, "ZZ"), (1, "XX")])

    assert pauli_sum[0] == (1, PauliString("XX"))
    assert list(pauli_sum) == [(1, PauliString("XX")), (2, PauliString("ZZ"))]


def test_constructor_variants_are_canonical():
    empty = PauliStringSum(None)
    empty_from_list = PauliStringSum.from_list([])
    single = PauliStringSum(PauliString("-XX"))
    copied = PauliStringSum(single)

    assert empty.to_list() == []
    assert empty_from_list.to_list() == []
    assert single.to_list() == [(-1, "XX")]
    assert copied == single


def test_pauli_string_dunder_methods_with_sums_and_scalars():
    pauli_string = PauliString("XX")
    pauli_sum = PauliStringSum.from_list([(2, "YY")])

    assert (pauli_string * 3).to_list() == [(3, "XX")]
    assert (3 * pauli_string).to_list() == [(3, "XX")]
    assert (pauli_string - PauliString("YY")).to_list() == [(1, "XX"), (-1, "YY")]
    assert (pauli_string + pauli_sum).to_list() == [(1, "XX"), (2, "YY")]
    assert (pauli_string - pauli_sum).to_list() == [(1, "XX"), (-2, "YY")]
    assert pauli_string.__mul__("bad") is NotImplemented
    assert pauli_string.__rmul__("bad") is NotImplemented
    assert pauli_string.__add__("bad") is NotImplemented
    assert pauli_string.__sub__("bad") is NotImplemented


def test_pauli_string_sum_dunder_fallbacks():
    pauli_sum = PauliStringSum.from_list([(1, "XX")])

    assert pauli_sum.__add__("bad") is NotImplemented
    assert pauli_sum.__radd__("bad") is NotImplemented
    assert PauliStringSum.__radd__(pauli_sum, PauliString("YY")).to_list() == [
        (1, "XX"),
        (1, "YY"),
    ]
    assert pauli_sum.__sub__("bad") is NotImplemented
    assert PauliStringSum.__rsub__(pauli_sum, PauliString("YY")).to_list() == [
        (-1, "XX"),
        (1, "YY"),
    ]
    assert pauli_sum.__mul__("bad") is NotImplemented
    assert pauli_sum.__rmul__("bad") is NotImplemented
    assert pauli_sum.__mul__(1j) is NotImplemented
    assert pauli_sum.__rmul__(1j) is NotImplemented
    assert pauli_sum != "bad"
    assert repr(pauli_sum) == "PauliStringSum([(1, 'XX')])"
    with pytest.raises(TypeError):
        1 - pauli_sum


def test_sum_to_sum_commutation_and_invalid_from_sum_input():
    left = PauliStringSum.from_list([(1, "XX"), (1, "YY")])
    right = PauliStringSum.from_list([(1, "ZZ")])

    assert left.commutes_with(right)
    assert not left.commutes_with(PauliStringSum.from_list([(1, "XI")]))
    with pytest.raises(TypeError, match=r"Observable\.Sum"):
        PauliStringSum.from_sum(X())
    with pytest.raises(TypeError, match="Can only check commutation"):
        left.commutes_with("bad")


def test_multiplication_length_mismatch_fails_explicitly():
    with pytest.raises(ValueError, match="length"):
        PauliStringSum.from_list([(1, "XX")]) * PauliString("X")
