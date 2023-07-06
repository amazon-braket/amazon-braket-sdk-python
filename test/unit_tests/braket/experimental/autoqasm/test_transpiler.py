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

"""Tests for transpiler."""

import functools

import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.autograph import ag_logging
from braket.experimental.autoqasm.autograph.core.ag_ctx import ControlStatusCtx, Status
from braket.experimental.autoqasm.gates import cnot, h, measure, x


def test_convert_invalid_object() -> None:
    """Tests the aq.function decorator on something that is not a function."""

    @aq.function
    class MyClass:
        pass

    with pytest.raises(ValueError):
        MyClass()


def test_autograph_disabled() -> None:
    """Tests the aq.function decorator with autograph disabled by control status,
    and verifies that the function is not converted."""

    @aq.function
    def my_program():
        h(0)
        if measure(0):
            x(0)

    with ControlStatusCtx(Status.DISABLED):
        with pytest.raises(RuntimeError):
            my_program()


def test_partial_function() -> None:
    """Tests aq.function decorator application to a partial function."""

    def bell(q0: int, q1: int):
        h(q0)
        cnot(q0, q1)

    expected = """OPENQASM 3.0;
qubit[4] __qubits__;
h __qubits__[1];
cnot __qubits__[1], __qubits__[3];"""
    bell_partial = aq.function(functools.partial(bell, 1))
    assert bell_partial(3).to_ir() == expected


def test_classmethod() -> None:
    """Tests aq.function decorator application to a classmethod."""

    class MyClass:
        @classmethod
        def bell(self, q0: int, q1: int):
            h(q0)
            cnot(q0, q1)

    expected = """OPENQASM 3.0;
qubit[4] __qubits__;
h __qubits__[1];
cnot __qubits__[1], __qubits__[3];"""

    a = MyClass()
    assert aq.function(a.bell)(1, 3).to_ir() == expected


def test_with_verbose_logging() -> None:
    """Tests aq.function decorator application with verbose logging enabled."""

    @aq.function
    def nothing():
        pass

    ag_logging.set_verbosity(10)
    nothing()
