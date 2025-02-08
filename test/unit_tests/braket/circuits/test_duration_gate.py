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

from braket.circuits import FreeParameter, FreeParameterExpression, Gate
from braket.circuits.duration_gate import DurationGate, SiTimeUnit, _duration_str


@pytest.mark.parametrize(
    "si_unit, expected",
    (
        (SiTimeUnit.s, "s"),
        (SiTimeUnit.ms, "ms"),
        (SiTimeUnit.us, "us"),
        (SiTimeUnit.ns, "ns"),
    ),
)
def test_si_unit_str(si_unit, expected):
    str(si_unit) == expected


@pytest.mark.parametrize(
    "si_unit, expected",
    (
        (SiTimeUnit.s, "s"),
        (SiTimeUnit.ms, "ms"),
        (SiTimeUnit.us, "us"),
        (SiTimeUnit.ns, "ns"),
    ),
)
def test_si_repr(si_unit, expected):
    repr(si_unit) == expected


@pytest.fixture
def duration_gate():
    return DurationGate(duration=30e-9, qubit_count=1, ascii_symbols=["delay"])


def test_is_operator(duration_gate):
    assert isinstance(duration_gate, Gate)


def test_repr(duration_gate):
    assert repr(duration_gate) == "DurationGate('duration': 3e-08, 'qubit_count': 1)"


def test_duration_setter(duration_gate):
    with pytest.raises(AttributeError):
        duration_gate.duration = 30e-9


def test_duration_is_none():
    with pytest.raises(ValueError, match="duration must not be None"):
        DurationGate(qubit_count=1, ascii_symbols=["foo"], duration=None)


def test_getters():
    qubit_count = 2
    ascii_symbols = ("foo", "bar")
    duration = 30e-9
    gate = DurationGate(duration=duration, qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    assert gate.qubit_count == qubit_count
    assert gate.ascii_symbols == ascii_symbols
    assert gate.duration == duration


def test_equality():
    gate1 = DurationGate(duration=30e-9, qubit_count=1, ascii_symbols=["delay"])
    gate2 = DurationGate(duration=30e-9, qubit_count=1, ascii_symbols=["bar"])
    gate3 = DurationGate(duration=30e-6, qubit_count=1, ascii_symbols=["foo"])
    non_gate = "non gate"

    assert gate1 == gate2
    assert gate1 is not gate2
    assert gate1 != gate3
    assert gate1 != non_gate


def test_symbolic_equality():
    symbol1 = FreeParameter("theta")
    symbol2 = FreeParameter("phi")
    symbol3 = FreeParameter("theta")
    gate1 = DurationGate(duration=symbol1, qubit_count=1, ascii_symbols=["bar"])
    gate2 = DurationGate(duration=symbol2, qubit_count=1, ascii_symbols=["bar"])
    gate3 = DurationGate(duration=symbol3, qubit_count=1, ascii_symbols=["bar"])
    other_gate = DurationGate(duration=symbol1, qubit_count=1, ascii_symbols=["foo"])

    assert gate1 != gate2
    assert gate1 == gate3
    assert gate1 == other_gate
    assert gate1 is not other_gate


def test_mixed_duration_equality():
    symbol1 = FreeParameter("theta")
    gate1 = DurationGate(duration=symbol1, qubit_count=1, ascii_symbols=["bar"])
    gate2 = DurationGate(duration=30e-9, qubit_count=1, ascii_symbols=["foo"])

    assert gate1 != gate2
    assert gate2 != gate1


def test_hash():
    symbol1 = FreeParameter("theta")
    symbol2 = FreeParameter("phi")
    symbol3 = FreeParameter("theta")
    gate1 = DurationGate(duration=symbol1, qubit_count=1, ascii_symbols=["bar"])
    gate2 = DurationGate(duration=symbol2, qubit_count=1, ascii_symbols=["bar"])
    gate3 = DurationGate(duration=symbol3, qubit_count=1, ascii_symbols=["bar"])

    assert hash(gate1) != hash(gate2)
    assert hash(gate1) == hash(gate3)


def test_bind_values():
    theta = FreeParameter("theta")
    gate = DurationGate(duration=theta, qubit_count=1, ascii_symbols=["bar"])
    with pytest.raises(NotImplementedError):
        gate.bind_values(theta=1)


@pytest.mark.parametrize(
    "duration, expected",
    (
        (30e-0, "30.0s"),
        (30e-3, "30.0ms"),
        (30e-6, "30.0us"),
        (30e-9, "30.0ns"),
        (FreeParameter("td"), "td"),
    ),
)
def test_duration_str(duration, expected):
    actual = _duration_str(duration)
    assert actual == expected


def test_duration_gate_with_expr():
    expr = FreeParameterExpression(FreeParameter("theta") + 1)
    new_expr = expr.subs({"theta": 1})
    gate = DurationGate(duration=new_expr, qubit_count=1, ascii_symbols=["bar"])
    expected = DurationGate(duration=2, qubit_count=1, ascii_symbols=["bar"])

    assert gate == expected
