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

"""AutoQASM tests exercising the main API: building programs and correctly
generating OpenQASM, and in turn verifying the OpenQASM by running against
the local simulator.
"""

import pytest

import braket.experimental.autoqasm as aq
from braket.default_simulator import StateVectorSimulator
from braket.devices.local_simulator import LocalSimulator
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.instructions import cnot, h, measure, rx, x
from braket.tasks.local_quantum_task import LocalQuantumTask


def _test_on_local_sim(program: aq.Program, inputs=None) -> None:
    device = LocalSimulator(backend=StateVectorSimulator())
    task = device.run(program, shots=10, inputs=inputs or {})
    assert isinstance(task, LocalQuantumTask)
    assert isinstance(task.result().measurements, dict)


def test_empty_function(empty_program) -> None:
    """Test that a function with no instructions generates an empty program."""
    expected = """OPENQASM 3.0;"""
    assert empty_program.to_ir() == expected


def test_sim_empty(empty_program) -> None:
    """Test an empty subroutine on the local simulator."""
    _test_on_local_sim(empty_program)


def test_sim_bell_state(bell_state_program) -> None:
    _test_on_local_sim(bell_state_program)


def test_multiple_calls(empty_subroutine, bell_state_subroutine) -> None:
    """Tests multiple calls to a single aq.main to ensure that each resulting
    Program object has the expected contents.
    """

    def count_function_calls(program: aq.Program, func_name: str) -> int:
        return program.to_ir().count(f"{func_name}();")

    def empty_program_wrapper():
        empty_subroutine()

    def bell_state_program_wrapper():
        bell_state_subroutine()

    first_program = aq.main(empty_program_wrapper)
    assert 1 == count_function_calls(first_program, "empty_function")
    assert 0 == count_function_calls(first_program, "bell_state")
    second_program = aq.main(empty_program_wrapper)
    third_program = aq.main(bell_state_program_wrapper)
    assert 1 == count_function_calls(first_program, "empty_function"), "reverify first program"
    assert 0 == count_function_calls(first_program, "bell_state"), "reverify first program"
    assert 1 == count_function_calls(second_program, "empty_function")
    assert 0 == count_function_calls(second_program, "bell_state")
    assert 0 == count_function_calls(third_program, "empty_function")
    assert 1 == count_function_calls(third_program, "bell_state")


def test_subroutines(empty_subroutine, bell_state_subroutine, physical_bell_subroutine):
    """Tests calling several subroutines consecutively."""

    @aq.main
    def call_subroutines() -> None:
        empty_subroutine()
        bell_state_subroutine()
        physical_bell_subroutine()

    expected = """OPENQASM 3.0;
def empty_function() {
}
def bell_state() {
    h __qubits__[0];
    cnot __qubits__[0], __qubits__[1];
}
def physical_bell() {
    h $0;
    cnot $0, $5;
}
qubit[2] __qubits__;
empty_function();
bell_state();
physical_bell();"""

    assert call_subroutines.to_ir() == expected

    _test_on_local_sim(call_subroutines)


@aq.subroutine
def do_h(q: int):
    h(q)


@aq.subroutine
def recursive_h(q: int):
    do_h(q)
    if q > 0:
        recursive_h(q - 1)


@pytest.fixture
def recursive_h_wrapper():
    q = 5

    @aq.main(num_qubits=q + 1)
    def recursive_h_wrapper():
        recursive_h(q)

    return recursive_h_wrapper


def test_recursive_h_wrapper(recursive_h_wrapper):
    expected = """OPENQASM 3.0;
def do_h(int[32] q) {
    h __qubits__[q];
}
def recursive_h(int[32] q) {
    do_h(q);
    bool __bool_0__;
    __bool_0__ = q > 0;
    if (__bool_0__) {
        recursive_h(q - 1);
    }
}
qubit[6] __qubits__;
recursive_h(5);"""
    assert recursive_h_wrapper.to_ir() == expected


def test_sim_recursive_h_wrapper(recursive_h_wrapper):
    _test_on_local_sim(recursive_h_wrapper)


def test_recursive_h():
    n = 4

    @aq.main(num_qubits=6)
    def main():
        recursive_h(n)

    expected = """OPENQASM 3.0;
def do_h(int[32] q) {
    h __qubits__[q];
}
def recursive_h(int[32] q) {
    do_h(q);
    bool __bool_0__;
    __bool_0__ = q > 0;
    if (__bool_0__) {
        recursive_h(q - 1);
    }
}
qubit[6] __qubits__;
recursive_h(4);"""

    assert main.to_ir() == expected


@aq.subroutine
def bell_state_arbitrary_qubits(q0: aq.Qubit, q1: aq.Qubit) -> None:
    h(q0)
    cnot(q0, q1)


@pytest.fixture
def double_bell_state():
    @aq.main
    def double_bell_state() -> None:
        bell_state_arbitrary_qubits(0, 1)
        bell_state_arbitrary_qubits(2, 3)

    return double_bell_state


def test_double_bell_state(double_bell_state) -> None:
    expected = """OPENQASM 3.0;
def bell_state_arbitrary_qubits(qubit q0, qubit q1) {
    h q0;
    cnot q0, q1;
}
qubit[4] __qubits__;
bell_state_arbitrary_qubits(__qubits__[0], __qubits__[1]);
bell_state_arbitrary_qubits(__qubits__[2], __qubits__[3]);"""
    assert double_bell_state.to_ir() == expected


def test_sim_double_bell(double_bell_state) -> None:
    _test_on_local_sim(double_bell_state)


@pytest.fixture
def bell_measurement_undeclared():
    @aq.main
    def bell_measurement_undeclared() -> None:
        """A function that generates and measures a two-qubit Bell state."""
        h(0)
        cnot(0, 1)
        c = measure([0, 1])  # noqa: F841

    return bell_measurement_undeclared


def test_bell_measurement_undeclared(bell_measurement_undeclared) -> None:
    expected = """OPENQASM 3.0;
bit[2] c;
qubit[2] __qubits__;
h __qubits__[0];
cnot __qubits__[0], __qubits__[1];
bit[2] __bit_0__ = "00";
__bit_0__[0] = measure __qubits__[0];
__bit_0__[1] = measure __qubits__[1];
c = __bit_0__;"""
    assert bell_measurement_undeclared.to_ir() == expected


def test_sim_bell_measurement_undeclared(bell_measurement_undeclared) -> None:
    _test_on_local_sim(bell_measurement_undeclared)


@pytest.fixture
def bell_measurement_declared():
    @aq.main
    def bell_measurement_declared() -> None:
        """A function that generates and measures a two-qubit Bell state."""
        c = aq.BitVar(0, size=2)
        h(0)
        cnot(0, 1)
        c = measure([0, 1])  # noqa: F841

    return bell_measurement_declared


def test_bell_measurement_declared(bell_measurement_declared) -> None:
    expected = """OPENQASM 3.0;
qubit[2] __qubits__;
bit[2] c = "00";
h __qubits__[0];
cnot __qubits__[0], __qubits__[1];
bit[2] __bit_1__ = "00";
__bit_1__[0] = measure __qubits__[0];
__bit_1__[1] = measure __qubits__[1];
c = __bit_1__;"""
    assert bell_measurement_declared.to_ir() == expected


def test_sim_bell_measurement_declared(bell_measurement_declared) -> None:
    _test_on_local_sim(bell_measurement_declared)


@pytest.fixture
def bell_partial_measurement():
    @aq.main
    def bell_partial_measurement() -> None:
        """A function that generates and measures a two-qubit Bell state."""
        h(0)
        cnot(0, 1)
        c = measure(1)  # noqa: F841

    return bell_partial_measurement


def test_bell_partial_measurement(bell_partial_measurement) -> None:
    expected = """OPENQASM 3.0;
bit c;
qubit[2] __qubits__;
h __qubits__[0];
cnot __qubits__[0], __qubits__[1];
bit __bit_0__;
__bit_0__ = measure __qubits__[1];
c = __bit_0__;"""
    assert bell_partial_measurement.to_ir() == expected


def test_bell_measurement_invalid_declared_type() -> None:
    """Test measurement with result stored in a variable with invalid type."""
    expected_error_message = "Variables in assignment statements must have the same type"
    with pytest.raises(errors.InvalidAssignmentStatement) as exc_info:

        @aq.main
        def bell_measurement_invalid_declared_type() -> None:
            """A function that generates and measures a two-qubit Bell state. But stores
            result in a variable with invalid type.
            """
            c = aq.IntVar(0)
            h(0)
            cnot(0, 1)
            c = measure(1)  # noqa: F841

    assert expected_error_message in str(exc_info.value)


def test_bell_measurement_invalid_declared_size() -> None:
    """Test measurement with result stored in a variable with invalid size."""
    expected_error_message = "Variables in assignment statements must have the same size"
    with pytest.raises(errors.InvalidAssignmentStatement) as exc_info:

        @aq.main
        def bell_measurement_invalid_declared_size() -> None:
            """A function that generates and measures a two-qubit Bell state. But stores
            result in a variable with invalid size.
            """
            c = aq.BitVar([0, 0], size=2)
            h(0)
            cnot(0, 1)
            c = measure(1)  # noqa: F841

    assert expected_error_message in str(exc_info.value)


@pytest.fixture
def measure_physical_qubits():
    @aq.main
    def measure_physical_qubits() -> None:
        """A program that measures physical qubits."""
        a = measure("$0")  # noqa: F841
        b = measure("$1")  # noqa: F841
        c = measure(["$0", "$1"])  # noqa: F841

    return measure_physical_qubits


def test_measure_physical_qubits(measure_physical_qubits) -> None:
    expected = """OPENQASM 3.0;
bit a;
bit b;
bit[2] c;
bit __bit_0__;
__bit_0__ = measure $0;
a = __bit_0__;
bit __bit_1__;
__bit_1__ = measure $1;
b = __bit_1__;
bit[2] __bit_2__ = "00";
__bit_2__[0] = measure $0;
__bit_2__[1] = measure $1;
c = __bit_2__;"""
    assert measure_physical_qubits.to_ir() == expected


@pytest.fixture
def ghz_qasm_for_loop():
    @aq.main(num_qubits=5)
    def ghz_qasm_for_loop() -> None:
        """A function that generates a GHZ state using a QASM for loop."""
        n_qubits = 5
        h(0)
        for i in aq.range(n_qubits - 1):
            cnot(i, i + 1)

    return ghz_qasm_for_loop


def test_ghz_qasm_for_loop(ghz_qasm_for_loop) -> None:
    expected = """OPENQASM 3.0;
qubit[5] __qubits__;
h __qubits__[0];
for int i in [0:4 - 1] {
    cnot __qubits__[i], __qubits__[i + 1];
}"""
    assert ghz_qasm_for_loop.to_ir() == expected


def test_sim_ghz_qasm_for_loop(ghz_qasm_for_loop) -> None:
    _test_on_local_sim(ghz_qasm_for_loop)


@pytest.fixture
def ghz_py_for_loop():
    @aq.main
    def ghz_py_for_loop() -> None:
        """A function that generates a GHZ state using a Python for loop."""
        n_qubits = 5
        h(0)
        for i in range(n_qubits - 1):
            cnot(i, i + 1)

    return ghz_py_for_loop


def test_ghz_py_for_loop(ghz_py_for_loop) -> None:
    expected = """OPENQASM 3.0;
qubit[5] __qubits__;
h __qubits__[0];
cnot __qubits__[0], __qubits__[1];
cnot __qubits__[1], __qubits__[2];
cnot __qubits__[2], __qubits__[3];
cnot __qubits__[3], __qubits__[4];"""
    assert ghz_py_for_loop.to_ir() == expected


def test_sim_ghz_py_for_loop(ghz_py_for_loop) -> None:
    _test_on_local_sim(ghz_py_for_loop)


@aq.subroutine
def qasm_simple_condition(do_cnot: bool) -> bool:
    """A function that contains a QASM conditional statement.

    Args:
        do_cnot (bool): Determines whether to insert a cnot operation.

    Returns:
        bool: Whether a cnot operation was performed.
    """
    h(0)
    if do_cnot:
        cnot(0, 1)
    return do_cnot


@pytest.fixture
def build_qasm_simple_condition_wrapper():
    def build_qasm_simple_condition_wrapper(do_cnot: bool):
        @aq.main
        def qasm_simple_condition_wrapper():
            qasm_simple_condition(do_cnot)

        return qasm_simple_condition_wrapper

    return build_qasm_simple_condition_wrapper


@pytest.mark.parametrize("do_cnot", (True, False))
def test_qasm_simple_condition(do_cnot: bool, build_qasm_simple_condition_wrapper) -> None:
    expected = """OPENQASM 3.0;
def qasm_simple_condition(bool do_cnot) -> bool {
    h __qubits__[0];
    if (do_cnot) {
        cnot __qubits__[0], __qubits__[1];
    }
    return do_cnot;
}
qubit[2] __qubits__;
bool __bool_0__;
"""
    expected += f"__bool_0__ = qasm_simple_condition({'true' if do_cnot else 'false'});"
    assert build_qasm_simple_condition_wrapper(do_cnot).to_ir() == expected


@pytest.mark.parametrize("do_cnot", [True, False])
def test_sim_qasm_simple_condition(do_cnot: bool, build_qasm_simple_condition_wrapper) -> None:
    _test_on_local_sim(build_qasm_simple_condition_wrapper(do_cnot))


@pytest.fixture
def qasm_inline_var_condition():
    @aq.main
    def qasm_inline_var_condition() -> aq.BitVar:
        """A function that contains a QASM conditional statement with an inline var condition.

        Returns:
            aq.BitVar: Measurement result.
        """
        h(0)
        if aq.BitVar(1):
            cnot(0, 1)
        x(0) if aq.IntVar(1) else x(1)
        return measure(1)

    return qasm_inline_var_condition


def test_qasm_inline_var_condition(qasm_inline_var_condition) -> None:
    """Tests the QASM contents of qasm_inline_var_condition."""
    expected = """OPENQASM 3.0;
bit __bit_0__ = 1;
int[32] __int_1__ = 1;
qubit[2] __qubits__;
h __qubits__[0];
if (__bit_0__) {
    cnot __qubits__[0], __qubits__[1];
}
if (__int_1__) {
    x __qubits__[0];
} else {
    x __qubits__[1];
}
bit __bit_2__;
__bit_2__ = measure __qubits__[1];"""
    assert qasm_inline_var_condition.to_ir() == expected


def test_sim_qasm_inline_var_condition(qasm_inline_var_condition) -> None:
    """Tests the function qasm_inline_var_condition on the local simulator."""
    _test_on_local_sim(qasm_inline_var_condition)


@pytest.fixture
def ground_state_measurements():
    @aq.main
    def ground_state_measurements() -> aq.BitVar:
        """Measure a few ground state qubits."""
        return measure([5, 2, 1])

    return ground_state_measurements


def test_measurement_qubit_discovery(ground_state_measurements) -> None:
    """Test that qubits measured by integer are automatically discovered for the purpose
    of qubit declaration.
    """
    assert "qubit[6] __qubits__;" in ground_state_measurements.to_ir()


def test_simple_measurement(ground_state_measurements) -> None:
    """Test that a program with only measurements is generated correctly."""
    expected = """OPENQASM 3.0;
qubit[6] __qubits__;
bit[3] __bit_0__ = "000";
__bit_0__[0] = measure __qubits__[5];
__bit_0__[1] = measure __qubits__[2];
__bit_0__[2] = measure __qubits__[1];"""
    assert ground_state_measurements.to_ir() == expected


def test_sim_simple_measurement(ground_state_measurements) -> None:
    _test_on_local_sim(ground_state_measurements)


def test_simple_measurement_return() -> None:
    """Test that a program with only measurements is generated correctly, when
    the measurement results are returned from a subroutine.
    """

    @aq.subroutine
    def ground_state_measurements_subroutine() -> aq.BitVar:
        """Measure a few ground state qubits."""
        return measure([5, 2, 1])

    @aq.main
    def ground_state_measurements_wrapper() -> None:
        ground_state_measurements_subroutine()

    expected = """OPENQASM 3.0;
def ground_state_measurements_subroutine() -> bit[3] {
    bit[3] __bit_0__ = "000";
    __bit_0__[0] = measure __qubits__[5];
    __bit_0__[1] = measure __qubits__[2];
    __bit_0__[2] = measure __qubits__[1];
    return __bit_0__;
}
qubit[6] __qubits__;
bit[3] __bit_1__ = "000";
__bit_1__ = ground_state_measurements_subroutine();"""
    assert ground_state_measurements_wrapper.to_ir() == expected


@pytest.fixture
def qasm_measurement_condition():
    @aq.main
    def qasm_measurement_condition() -> aq.BitVar:
        """A function that contains a mid-circuit measurement conditional.

        Returns:
            BitVar: The result of measuring qubit 1.
        """
        h(0)
        if measure(0):
            cnot(0, 1)
        return measure(1)

    return qasm_measurement_condition


def test_qasm_measurement_condition(qasm_measurement_condition) -> None:
    expected = """OPENQASM 3.0;
qubit[2] __qubits__;
h __qubits__[0];
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
if (__bit_0__) {
    cnot __qubits__[0], __qubits__[1];
}
bit __bit_1__;
__bit_1__ = measure __qubits__[1];"""
    assert qasm_measurement_condition.to_ir() == expected


def test_sim_measurement_condition(qasm_measurement_condition) -> None:
    _test_on_local_sim(qasm_measurement_condition)


def test_virtual_int_qubit_decl(bell_state_program) -> None:
    """Tests for ex. h(0) -> qubit[1] __qubits__"""
    qasm = bell_state_program.to_ir()
    assert "\nqubit[2] __qubits__;" in qasm


def test_py_int_qubit_decl(ghz_py_for_loop) -> None:
    """Tests for ex. i = 1; h(i) -> qubit[1] __qubits__"""
    qasm = ghz_py_for_loop.to_ir()
    assert "\nqubit[5] __qubits__;" in qasm


def test_physical_qubit_decl(physical_bell_subroutine) -> None:
    """Tests e.g. h("$0"). Note that physical qubits aren't declared."""

    @aq.main
    def main():
        physical_bell_subroutine()

    assert "__qubits__" not in main.to_ir()


def test_invalid_physical_qubit_fails() -> None:
    """Tests invalid physical qubit formatting."""
    with pytest.raises(ValueError):

        @aq.main
        def broken() -> None:
            """Uses invalid string for qubit index"""
            cnot("$0l", "$O1")


def test_invalid_qubit_label_fails() -> None:
    """Tests random string fails for qubit label."""
    with pytest.raises(ValueError):

        @aq.main
        def broken() -> None:
            """Uses invalid string for qubit index"""
            h("nope")


def test_float_qubit_index_fails() -> None:
    """Tests floats fails for qubit label."""
    with pytest.raises(TypeError):

        @aq.main
        def broken() -> None:
            """Uses float for qubit index"""
            i = 1
            h(i / 2)


def test_bool_qubit_index_fails() -> None:
    """Tests that an error is raised for boolean qubit type."""
    with pytest.raises(ValueError):

        @aq.main
        def broken() -> None:
            """Uses invalid type for qubit index"""
            h(True)


def test_invalid_qubit_type_fails() -> None:
    """Tests that an error is raised for other unusual qubit types."""
    with pytest.raises(ValueError):

        @aq.main
        def broken() -> None:
            """Uses invalid type for qubit index"""
            h(h)


def test_bit_array_name() -> None:
    """Tests that auto declared bits are given a reasonable name."""

    @aq.subroutine
    def my_program() -> aq.BitVar:
        """Program which requires generating a bit"""
        h(0)
        return measure(0)

    @aq.main
    def my_program_wrapper() -> None:
        my_program()

    expected = """
    bit __bit_0__;
    __bit_0__ = measure __qubits__[0];
    return __bit_0__;"""
    assert expected in my_program_wrapper.to_ir()


@pytest.fixture
def reset():
    @aq.main
    def reset() -> None:
        """Reset qubit 0."""
        if measure(0):
            x(0)
        if measure(0):
            x(0)
        if measure(0):
            x(0)

    return reset


def test_bit_array_name_multi(reset) -> None:
    """Tests that auto declared bits are given a reasonable name."""
    expected = """OPENQASM 3.0;
qubit[1] __qubits__;
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
if (__bit_0__) {
    x __qubits__[0];
}
bit __bit_1__;
__bit_1__ = measure __qubits__[0];
if (__bit_1__) {
    x __qubits__[0];
}
bit __bit_2__;
__bit_2__ = measure __qubits__[0];
if (__bit_2__) {
    x __qubits__[0];
}"""
    assert reset.to_ir() == expected


def test_program_simple_expr() -> None:
    """Test that a program with simple expressions for the qubit index raises
    an error if the user doesn't specify the number of qubits.
    """
    with pytest.raises(errors.UnknownQubitCountError):

        @aq.main
        def simple_range() -> None:
            "Uses aq.range iterator for qubit index."
            for i in aq.range(5):
                h(i)


def test_program_with_expr() -> None:
    """Test that a program with expressions for the qubit index raises
    an error if the user doesn't specify the number of qubits.
    """
    with pytest.raises(errors.UnknownQubitCountError):

        @aq.main
        def qubit_expr() -> None:
            "Uses aq.range iterator for qubit index."
            for i in aq.range(5):
                h(i + 3)


def test_multi_for_loop() -> None:
    """Test that a program with multiple differing for loops is generated
    correctly.
    """
    expected = """OPENQASM 3.0;
qubit[6] __qubits__;
for int i in [0:3 - 1] {
    cnot __qubits__[i], __qubits__[i + 1];
}
for int i in [0:5 - 1] {
    h __qubits__[i];
}"""

    @aq.main(num_qubits=6)
    def prog():
        for i in aq.range(3):
            cnot(i, i + 1)

        for i in aq.range(5):
            h(i)

    assert prog.to_ir() == expected


@aq.subroutine
def bell(q0: aq.Qubit, q1: aq.Qubit) -> None:
    h(q0)
    cnot(q0, q1)


@pytest.fixture
def bell_in_for_loop():
    @aq.main
    def bell_in_for_loop() -> None:
        for i in aq.range(3):
            bell(0, 1)

    return bell_in_for_loop


def test_subroutines_in_for_loop(bell_in_for_loop) -> None:
    """Test calling a parameterized subroutine from inside a for loop."""
    expected = """OPENQASM 3.0;
def bell(qubit q0, qubit q1) {
    h q0;
    cnot q0, q1;
}
qubit[2] __qubits__;
for int i in [0:3 - 1] {
    bell(__qubits__[0], __qubits__[1]);
}"""

    assert bell_in_for_loop.to_ir() == expected


@pytest.fixture
def classical_variables_types():
    @aq.main
    def classical_variables_types() -> None:
        a = aq.BitVar(0)
        a = aq.BitVar(1)  # noqa: F841

        i = aq.IntVar(1)
        a_array = aq.BitVar(size=2)
        a_array[0] = aq.BitVar(0)
        a_array[i] = aq.BitVar(1)

        b = aq.IntVar(10)
        b = aq.IntVar(15)  # noqa: F841

        c = aq.FloatVar(1.2)
        c = aq.FloatVar(3.4)  # noqa: F841

    return classical_variables_types


def test_classical_variables_types(classical_variables_types):
    expected = """OPENQASM 3.0;
bit a = 0;
a = 1;
int[32] i = 1;
bit[2] a_array = "00";
a_array[0] = 0;
a_array[i] = 1;
int[32] b = 10;
b = 15;
float[64] c = 1.2;
c = 3.4;"""
    assert classical_variables_types.to_ir() == expected


def test_sim_classical_variables_types(classical_variables_types):
    _test_on_local_sim(classical_variables_types)


def test_classical_variables_assignment():
    @aq.main
    def prog() -> None:
        a = aq.IntVar(1)  # undeclared target, undeclared value
        a = aq.IntVar(2)  # declared target, undeclared value
        b = a  # undeclared target, declared value # noqa: F841
        a = b  # declared target, declared value # noqa: F841

    expected = """OPENQASM 3.0;
int[32] b;
int[32] a = 1;
a = 2;
b = a;
a = b;"""
    assert prog.to_ir() == expected


def test_assignment_measurement_results():
    @aq.main
    def prog() -> None:
        a = measure(0)
        b = a  # noqa: F841

    expected = """OPENQASM 3.0;
bit a;
bit b;
qubit[1] __qubits__;
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
a = __bit_0__;
b = a;"""
    assert prog.to_ir() == expected


def test_nested_function():
    n = 5

    @aq.main
    def make_ghz() -> None:
        def ghz(n: int):
            if n == 1:
                h(0)
            else:
                ghz(n - 1)
                cnot(0, n - 1)

        ghz(n)

    expected = """OPENQASM 3.0;
qubit[5] __qubits__;
h __qubits__[0];
cnot __qubits__[0], __qubits__[1];
cnot __qubits__[0], __qubits__[2];
cnot __qubits__[0], __qubits__[3];
cnot __qubits__[0], __qubits__[4];"""

    assert make_ghz.to_ir() == expected


def test_double_decorated_function():
    @aq.main
    @aq.main
    def empty_program() -> None:
        pass

    expected = """OPENQASM 3.0;"""
    assert empty_program.to_ir() == expected


def test_main_return():
    with pytest.warns(UserWarning, match="Return value from top level function is ignored"):

        @aq.main
        def main() -> int:
            return 1


def test_main_no_return():
    @aq.subroutine
    def tester(x: int) -> int:
        return measure(x)

    @aq.main(num_qubits=3)
    def main():
        x = 3
        tester(x)


def test_subroutine_args():
    """Test that subroutines will fail if supplied args."""
    with pytest.raises(TypeError, match="got an unexpected keyword argument"):

        @aq.subroutine(num_qubits=5)
        def bell(q0: int, q1: int) -> None:
            h(q0)
            cnot(q0, q1)


def test_direct_subroutine_call_w_args():
    """Shouldn't be able to call a subroutine directly."""

    @aq.subroutine
    def bell(q0: int, q1: int) -> None:
        h(q0)
        cnot(q0, q1)

    with pytest.raises(errors.AutoQasmTypeError):
        bell()


def test_direct_subroutine_call_no_args():
    """Shouldn't be able to call a subroutine directly."""

    @aq.subroutine
    def bell() -> None:
        h(0)
        cnot(0, 1)

    with pytest.raises(errors.AutoQasmTypeError):
        bell()


@pytest.mark.xfail(reason="(#809) will fix by adding a checker to the transpiler")
def test_main_from_main():
    """Can't call main from main!"""

    @aq.main(num_qubits=2)
    def bell(q0: int, q1: int) -> None:
        h(q0)
        cnot(q0, q1)

    with pytest.raises(errors.AutoQasmTypeError):

        @aq.main
        def main():
            bell(0, 1)


def test_empty_decorator_parentheses():
    @aq.subroutine()
    def nothing():
        pass

    @aq.main()
    def main():
        nothing()

    expected = """OPENQASM 3.0;
def nothing() {
}
nothing();"""

    assert main.to_ir() == expected


def test_input_types():
    @aq.main
    def multiple_input_types(x: int, y: bool, z: float, u):
        if x and y:
            rx(target=0, angle=u + z)

    @aq.main()
    def multiple_input_types_parens(x: int, y: bool, z: float, u):
        if x and y:
            rx(target=0, angle=u + z)

    @aq.main(num_qubits=1)
    def multiple_input_types_params(x: int, y: bool, z: float, u):
        if x and y:
            rx(target=0, angle=u + z)

    expected_ir = """OPENQASM 3.0;
input int[32] x;
input bool y;
input float[64] z;
input float[64] u;
qubit[1] __qubits__;
bool __bool_0__;
__bool_0__ = x && y;
if (__bool_0__) {
    rx(u + z) __qubits__[0];
}"""
    assert (
        multiple_input_types.to_ir()
        == multiple_input_types_parens.to_ir()
        == multiple_input_types_params.to_ir()
        == expected_ir
    )


def test_input_qubit_indices():
    @aq.main(num_qubits=8)
    def circ(q: int, r: int):
        h(2 * q + r)

    expected_ir = """OPENQASM 3.0;
input int[32] q;
input int[32] r;
qubit[8] __qubits__;
h __qubits__[2*q + r];"""
    assert circ.to_ir() == expected_ir


def test_input_qubit_indices_needs_num_qubits():
    with pytest.raises(errors.UnknownQubitCountError):

        @aq.main
        def circ(q: int, r: int):
            h(2 * q + r)
