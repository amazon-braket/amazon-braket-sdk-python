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
from braket.experimental.autoqasm.instructions import cnot, h, measure, rx, x


def test_convert_invalid_main_object() -> None:
    """Tests the aq.main decorator on something that is not a function."""

    with pytest.raises(ValueError):

        @aq.main
        class MyClass:
            pass


def test_convert_invalid_subroutine_object() -> None:
    """Tests the aq.subroutine decorator on something that is not a function."""

    @aq.subroutine
    class MyClass:
        pass

    with pytest.raises(ValueError):

        @aq.main
        def main():
            MyClass()


def test_autograph_disabled() -> None:
    """Tests the aq.main decorator with autograph disabled by control status,
    and verifies that the function is not converted."""

    with ControlStatusCtx(Status.DISABLED):
        with pytest.raises(RuntimeError):

            @aq.main
            def my_program():
                h(0)
                if measure(0):
                    x(0)


def test_partial_function() -> None:
    """Tests aq.main decorator application to a partial function."""

    def bell(q0: int, q1: int):
        h(q0)
        cnot(q0, q1)

    expected_partial = """OPENQASM 3.0;
input int[32] q1;
qubit[2] __qubits__;
h __qubits__[1];
cnot __qubits__[1], __qubits__[q1];"""

    expected_no_arg_partial = """OPENQASM 3.0;
qubit[2] __qubits__;
h __qubits__[1];
cnot __qubits__[1], __qubits__[3];"""

    bell_partial = aq.main(num_qubits=2)(functools.partial(bell, 1))
    assert bell_partial.to_ir() == expected_partial

    bell_noarg_partial = aq.main(num_qubits=2)(functools.partial(bell, 1, 3))
    assert bell_noarg_partial.to_ir() == expected_no_arg_partial


def test_classmethod() -> None:
    """Tests aq.main decorator application to a classmethod."""

    # todo: see if this functionality should work
    pytest.xfail("cls must be handled")
    # we could try to catch `cls` parameters and use qualname to extrapolate
    # class info, but it's a best-effort approach

    class MyClass:
        @classmethod
        def bell(cls, q0: int, q1: int):
            h(q0)
            cnot(q0, q1)

        @classmethod
        @aq.main(num_qubits=2)
        def bell_decorated(cls, q0: int, q1: int):
            cls.bell(q0, q1)

    expected = """OPENQASM 3.0;
input int[32] q0;
input int[32] q1;
qubit[2] __qubits__;
h __qubits__[q0];
cnot __qubits__[q0], __qubits__[q1];"""

    assert aq.main(num_qubits=2)(MyClass.bell).to_ir() == expected
    assert MyClass.bell_decorated.to_ir() == expected

    a = MyClass()
    assert aq.main(num_qubits=2)(a.bell).to_ir() == expected
    assert a.bell_decorated.to_ir() == expected


def test_method() -> None:
    """Tests aq.main decorator application to a classmethod."""

    # todo: see if this functionality should work
    pytest.xfail("can't access `self` at function definition time")

    class MyClass:
        def __init__(self):
            self.class_param = 2

        def rx(self, q0: int):
            rx(target=q0, angle=self.class_param)

        @aq.main(num_qubits=1)
        def rx_decorated(self, q0: int):
            self.rx(q0)

    expected = """OPENQASM 3.0;
input int[32] q0;
qubit[1] __qubits__;
rx __qubits__[q0];"""

    assert aq.main(num_qubits=2)(MyClass.rx).to_ir() == expected
    assert MyClass.rx_decorated.to_ir() == expected

    a = MyClass()
    assert aq.main(num_qubits=2)(a.rx).to_ir() == expected
    assert a.rx_decorated.to_ir() == expected


def test_with_verbose_logging() -> None:
    """Tests aq.main decorator application with verbose logging enabled."""

    @aq.main
    def nothing():
        pass

    ag_logging.set_verbosity(10)
