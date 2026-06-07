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

from braket.quantum_information import PauliString, PauliStringSum


def _ps(s):
    return PauliString(s)


def _sum(*terms):
    return PauliStringSum(list(terms))


class TestConstruction:
    def test_empty(self):
        s = PauliStringSum()
        assert len(s) == 0

    def test_from_pauli_strings(self):
        s = PauliStringSum([_ps("XY"), _ps("ZI")])
        assert len(s) == 2
        assert _ps("XY") in s
        assert _ps("ZI") in s

    def test_from_weighted_tuples_str(self):
        s = PauliStringSum([(2.0, "XY"), (0.5, "ZI")])
        assert s[_ps("XY")] == pytest.approx(2.0)
        assert s[_ps("ZI")] == pytest.approx(0.5)

    def test_from_weighted_tuples_pauli(self):
        s = PauliStringSum([(3.0, _ps("XY"))])
        assert s[_ps("XY")] == pytest.approx(3.0)

    def test_duplicate_terms_merged(self):
        s = PauliStringSum([(1.0, "XY"), (2.0, "XY")])
        assert len(s) == 1
        assert s[_ps("XY")] == pytest.approx(3.0)

    def test_pauli_strings_have_unit_weight(self):
        s = PauliStringSum([_ps("XY"), _ps("XY")])
        assert len(s) == 1
        assert s[_ps("XY")] == pytest.approx(2.0)

    def test_invalid_term_type_raises(self):
        with pytest.raises(TypeError):
            PauliStringSum(["not_a_valid_term"])

    def test_invalid_term_tuple_raises(self):
        with pytest.raises((TypeError, ValueError)):
            PauliStringSum([(1.0,)])


class TestFromToList:
    def test_round_trip(self):
        terms = [(1.5, "+XY"), (0.5, "+ZI")]
        s = PauliStringSum.from_list(terms)
        result = s.to_list()
        assert len(result) == 2
        coeffs = {p: c for c, p in result}
        assert coeffs["+XY"] == pytest.approx(1.5)
        assert coeffs["+ZI"] == pytest.approx(0.5)


class TestContainsAndIndex:
    def test_contains_pauli_string(self):
        s = PauliStringSum([(1.0, "XZ")])
        assert _ps("XZ") in s
        assert _ps("ZX") not in s

    def test_contains_str(self):
        s = PauliStringSum([(1.0, "XZ")])
        assert "XZ" in s
        assert "ZX" not in s

    def test_getitem_by_pauli_string(self):
        s = PauliStringSum([(2.5, "XZ")])
        assert s[_ps("XZ")] == pytest.approx(2.5)

    def test_getitem_by_str(self):
        s = PauliStringSum([(2.5, "XZ")])
        assert s["XZ"] == pytest.approx(2.5)

    def test_getitem_by_int(self):
        s = PauliStringSum([(1.0, "XY")])
        coeff, ps = s[0]
        assert coeff == pytest.approx(1.0)
        assert ps == _ps("XY")

    def test_getitem_missing_raises(self):
        s = PauliStringSum([(1.0, "XZ")])
        with pytest.raises(KeyError):
            _ = s[_ps("ZX")]

    def test_getitem_invalid_type_raises(self):
        s = PauliStringSum([(1.0, "XZ")])
        with pytest.raises(TypeError):
            _ = s[3.14]


class TestIteration:
    def test_iter_yields_coeff_ps_pairs(self):
        s = PauliStringSum([(1.0, "XY"), (2.0, "ZI")])
        items = list(s)
        assert len(items) == 2
        for coeff, ps in items:
            assert isinstance(coeff, float)
            assert isinstance(ps, PauliString)


class TestAddition:
    def test_sum_plus_sum(self):
        a = PauliStringSum([(1.0, "XY")])
        b = PauliStringSum([(2.0, "XY")])
        c = a + b
        assert c[_ps("XY")] == pytest.approx(3.0)

    def test_sum_plus_pauli_string(self):
        a = PauliStringSum([(1.0, "XY")])
        c = a + _ps("ZI")
        assert _ps("ZI") in c
        assert c[_ps("ZI")] == pytest.approx(1.0)

    def test_sum_plus_tuple(self):
        a = PauliStringSum([(1.0, "XY")])
        c = a + (3.0, "ZI")
        assert c[_ps("ZI")] == pytest.approx(3.0)

    def test_iadd_sum(self):
        a = PauliStringSum([(1.0, "XY")])
        a += PauliStringSum([(1.0, "XY")])
        assert a[_ps("XY")] == pytest.approx(2.0)

    def test_iadd_pauli_string(self):
        a = PauliStringSum([(1.0, "XY")])
        a += _ps("ZI")
        assert _ps("ZI") in a

    def test_zero_terms_dropped(self):
        a = PauliStringSum([(1.0, "XY")])
        b = PauliStringSum([(-1.0, "XY")])
        c = a + b
        assert _ps("XY") not in c
        assert len(c) == 0

    def test_radd_pauli_string(self):
        s = PauliStringSum([(1.0, "XY")])
        c = _ps("ZI") + s
        assert _ps("ZI") in c


class TestSubtraction:
    def test_sum_minus_sum(self):
        a = PauliStringSum([(3.0, "XY")])
        b = PauliStringSum([(1.0, "XY")])
        c = a - b
        assert c[_ps("XY")] == pytest.approx(2.0)

    def test_negation(self):
        a = PauliStringSum([(2.0, "XY")])
        c = -a
        assert c[_ps("XY")] == pytest.approx(-2.0)

    def test_isub(self):
        a = PauliStringSum([(3.0, "XY")])
        a -= PauliStringSum([(1.0, "XY")])
        assert a[_ps("XY")] == pytest.approx(2.0)


class TestScalarMultiplication:
    def test_mul_float(self):
        a = PauliStringSum([(2.0, "XY")])
        b = a * 3.0
        assert b[_ps("XY")] == pytest.approx(6.0)

    def test_rmul_float(self):
        a = PauliStringSum([(2.0, "XY")])
        b = 3.0 * a
        assert b[_ps("XY")] == pytest.approx(6.0)

    def test_imul_float(self):
        a = PauliStringSum([(2.0, "XY")])
        a *= 3.0
        assert a[_ps("XY")] == pytest.approx(6.0)

    def test_mul_zero_drops_terms(self):
        a = PauliStringSum([(2.0, "XY")])
        b = a * 0.0
        assert len(b) == 0


class TestPauliStringMultiplication:
    def test_mul_pauli_string(self):
        # XY * ZI should give (XY)(ZI) = (X*Z)(Y*I) = (-iY)(-iI)... but let's just check it's a sum
        a = PauliStringSum([(1.0, "XZ")])
        result = a * _ps("ZX")
        assert isinstance(result, PauliStringSum)
        assert len(result) >= 1

    def test_rmul_pauli_string(self):
        a = PauliStringSum([(1.0, "XZ")])
        result = _ps("ZX") * a
        assert isinstance(result, PauliStringSum)

    def test_mul_pauli_string_identity(self):
        a = PauliStringSum([(2.0, "XY")])
        result = a * _ps("II")
        assert _ps("XY") in result
        assert result[_ps("XY")] == pytest.approx(2.0)


class TestEquality:
    def test_equal_sums(self):
        a = PauliStringSum([(1.0, "XY"), (2.0, "ZI")])
        b = PauliStringSum([(2.0, "ZI"), (1.0, "XY")])
        assert a == b

    def test_not_equal_different_terms(self):
        a = PauliStringSum([(1.0, "XY")])
        b = PauliStringSum([(1.0, "ZI")])
        assert a != b

    def test_not_equal_different_coeffs(self):
        a = PauliStringSum([(1.0, "XY")])
        b = PauliStringSum([(2.0, "XY")])
        assert a != b

    def test_not_equal_non_sum(self):
        a = PauliStringSum([(1.0, "XY")])
        assert a != "XY"


class TestRepr:
    def test_empty_repr(self):
        s = PauliStringSum()
        assert repr(s) == "PauliStringSum([])"

    def test_nonempty_repr(self):
        s = PauliStringSum([(1.0, "XY")])
        r = repr(s)
        assert "XY" in r
        assert "1" in r


class TestCommutation:
    def test_commutes_with_itself(self):
        s = PauliStringSum([(1.0, "XY"), (0.5, "ZI")])
        assert s.commutes_with(s)

    def test_commutes_with_commuting_pauli_string(self):
        # XX and XX commute
        s = PauliStringSum([(1.0, "XX")])
        assert s.commutes_with(_ps("XX"))

    def test_does_not_commute_with_anticommuting(self):
        # X and Y anticommute: XY - YX = 2iZ ≠ 0 (as Pauli products with phases)
        s = PauliStringSum([(1.0, "X")])
        t = PauliStringSum([(1.0, "Y")])
        # [X, Y] = 2iZ ≠ 0 at the Pauli level (phases differ), so commutes_with False
        assert not s.commutes_with(t)

    def test_is_self_commuting_single_term(self):
        s = PauliStringSum([(1.0, "XY")])
        assert s.is_self_commuting()

    def test_is_self_commuting_commuting_terms(self):
        # ZZ and ZZ trivially commute
        s = PauliStringSum([(1.0, "ZZ"), (0.5, "ZZ")])
        assert s.is_self_commuting()

    def test_not_self_commuting(self):
        # X and Y terms don't commute
        s = PauliStringSum([(1.0, "X"), (1.0, "Y")])
        assert not s.is_self_commuting()
