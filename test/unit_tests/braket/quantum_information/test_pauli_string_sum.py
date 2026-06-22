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

from braket.circuits.observables import H, X, Y, Z
from braket.quantum_information import PauliString, PauliStringSum, PauliSum


def test_initializes_from_weighted_list_and_combines_terms():
    pauli_sum = PauliStringSum.from_list([(1.5, "XZ"), (2.0, "-XZ"), (3.0, "YY")])

    assert pauli_sum.to_list() == [(-0.5, "+XZ"), (3.0, "+YY")]


def test_addition_subtraction_and_scalar_multiplication():
    first = PauliStringSum([(1.0, "XI")])
    second = PauliStringSum([(2.0, "IZ")])

    assert (first + second - PauliString("XI")).to_list() == [(2.0, "+IZ")]
    assert (0.5 * second).to_list() == [(1.0, "+IZ")]
    assert (-second).to_list() == [(-2.0, "+IZ")]


def test_multiplication_by_pauli_string():
    pauli_sum = PauliStringSum([(2.0, "XY"), (3.0, "ZZ")])

    assert (pauli_sum * PauliString("YZ")).to_list() == [(-2.0, "+ZX"), (-3.0, "+XI")]


def test_multiplication_by_pauli_string_pads_mixed_width_terms():
    pauli_sum = PauliStringSum([(1.0, "X"), (2.0, "IZ")])

    assert (pauli_sum * PauliString("ZZ")).to_list() == [(-1.0, "+YZ"), (2.0, "+ZI")]


def test_left_multiplication_by_pauli_string_preserves_order():
    pauli_sum = PauliStringSum([(2.0, "X")])

    assert (pauli_sum * PauliString("Z")).to_list() == [(-2.0, "+Y")]
    assert (PauliString("Z") * pauli_sum).to_list() == [(2.0, "+Y")]


def test_indexing_and_membership():
    pauli_sum = PauliStringSum([(2.0, "XI"), (3.0, "IZ")])

    assert "XI" in pauli_sum
    assert PauliString("-IZ") in pauli_sum
    assert pauli_sum[0] == (2.0, PauliString("XI"))
    assert list(pauli_sum) == [(2.0, PauliString("XI")), (3.0, PauliString("IZ"))]


def test_to_sum_and_from_sum_round_trip():
    pauli_sum = PauliStringSum([(2.0, "XY"), (-3.0, "ZI")])

    observable_sum = pauli_sum.to_sum()

    assert PauliStringSum.from_sum(observable_sum) == pauli_sum


def test_equality_is_independent_of_term_insertion_order():
    first = PauliStringSum([(1.0, "XI"), (2.0, "IZ")])
    second = PauliStringSum([(2.0, "IZ"), (1.0, "XI")])

    assert first == second


def test_reverse_subtraction():
    pauli_sum = PauliStringSum([(2.0, "XI")])

    assert (PauliString("IZ") - pauli_sum).to_list() == [(1, "+IZ"), (-2.0, "+XI")]


def test_from_sum_with_targeted_observables():
    observable_sum = 2.0 * (X(0) @ Y(2)) - 3.0 * Z(1)

    assert PauliStringSum.from_sum(observable_sum).to_list() == [
        (2.0, "+XIY"),
        (-3.0, "+IZ"),
    ]


def test_from_list_alias_and_empty_sum_edges():
    assert PauliStringSum.from_list([(2, "XY"), (-2.0, "XY")]).to_list() == []
    assert len(PauliStringSum.from_list([(2, "XY"), (-2.0, "XY")])) == 0
    assert PauliStringSum().is_self_commuting()
    assert PauliStringSum().commutes_with("I")


def test_from_sum_with_targetless_tensor_product():
    from braket.circuits.observables import Sum

    observable = Sum([1.0 * (X() @ Y())])

    assert PauliStringSum.from_sum(observable).to_list() == [(1.0, "+XY")]


def test_commutation_checks():
    commuting_sum = PauliStringSum([(1.0, "XX"), (2.0, "YY")])
    non_commuting_sum = PauliStringSum([(1.0, "XI"), (2.0, "ZI")])

    assert commuting_sum.is_self_commuting()
    assert commuting_sum.all_terms_commute
    assert commuting_sum.commutes_with("ZZ")
    assert not non_commuting_sum.is_self_commuting()
    assert not non_commuting_sum.commutes_with("YI")


def test_empty_sum_cannot_convert_to_observable_sum():
    with pytest.raises(ValueError, match="empty PauliSum"):
        PauliStringSum().to_sum()


def test_non_numeric_coefficients_are_rejected():
    with pytest.raises(TypeError, match="coefficients must be numbers"):
        PauliStringSum([("weight", "XI")])


def test_from_sum_rejects_non_sum_observable():
    with pytest.raises(TypeError, match="Expected a Sum observable"):
        PauliStringSum.from_sum(X())


def test_from_sum_rejects_non_pauli_observable_terms():
    with pytest.raises(TypeError, match="Unsupported observable factor H"):
        PauliStringSum.from_sum(H() + X())


def test_empty_sum_has_zero_qubit_count_and_repr():
    empty_sum = PauliStringSum()

    assert empty_sum.qubit_count == 0
    assert repr(empty_sum) == "PauliSum([])"


def test_zero_coefficient_terms_cancel_to_empty_sum():
    pauli_sum = PauliStringSum([(1.0, "X"), (-1.0, "X"), (2.0, "Y")])

    assert pauli_sum.to_list() == [(2.0, "+Y")]


def test_zero_coefficient_term_is_ignored():
    pauli_sum = PauliStringSum([(0.0, "X"), (2.0, "Y")])

    assert pauli_sum.to_list() == [(2.0, "+Y")]


def test_radd_and_non_matching_eq_type():
    assert "ZY" + PauliStringSum([(1.0, "X")]) == PauliStringSum([(1.0, "X"), (1.0, "ZY")])
    assert PauliStringSum([(1.0, "X")]) != 1


def test_pauli_sum_export_and_non_commuting_short_circuit():
    non_commuting_sum = PauliSum([(1.0, "XI"), (2.0, "ZI")])

    assert PauliStringSum is PauliSum
    assert isinstance(PauliSum([(1.0, "X")]), PauliSum)
    assert not non_commuting_sum.commutes_with("II")


def test_from_sum_uses_default_target_for_standard_observables_and_rejects_unmapped_observable():
    from braket.circuits.observables import Sum

    from_sum_with_no_targets = PauliStringSum.from_sum(Sum([1.0 * X()]))
    assert from_sum_with_no_targets.to_list() == [(1.0, "+X")]

    class NonStandardObservable:
        coefficient = 1.0

        def _unscaled(self):
            return object()

    with pytest.raises(TypeError, match="Unsupported observable type"):
        PauliStringSum._term_from_observable(NonStandardObservable())
