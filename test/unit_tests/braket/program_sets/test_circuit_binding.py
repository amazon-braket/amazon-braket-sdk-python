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

from braket.circuits import Circuit
from braket.circuits.observables import X, Y, Z
from braket.circuits.serialization import IRType
from braket.default_simulator.openqasm.parser.openqasm_parser import parse
from braket.parametric import FreeParameter
from braket.program_sets import CircuitBinding
from braket.quantum_information import PauliString


def _source(circuit):
    return circuit.to_ir(IRType.OPENQASM).source


def test_equality(circuit_rx_parametrized):
    input_sets = {"theta": [1.23, 3.21]}
    observable = X(0) @ Z(1) + 3 * Y(0)
    cb = CircuitBinding(circuit_rx_parametrized, input_sets, observable)
    assert cb == CircuitBinding(
        circuit_rx_parametrized, [{"theta": 1.23}, {"theta": 3.21}], observable
    )
    assert cb != CircuitBinding(circuit_rx_parametrized, observables=observable)
    assert cb != CircuitBinding(circuit_rx_parametrized, input_sets)
    assert cb != circuit_rx_parametrized


def test_input_sets_observables_missing():
    with pytest.raises(ValueError):
        CircuitBinding(Circuit().h(0))


def test_result_type(circuit_rx_parametrized):
    with pytest.raises(ValueError):
        CircuitBinding(
            Circuit(circuit_rx_parametrized).expectation(X(0)),
            input_sets={"theta": [1.23, 3.21]},
        )


def test_targetless_sum():
    circuit = Circuit().rx(1, FreeParameter("theta")).cnot(1, 0)
    input_sets = {"theta": [1.35, 1.58]}
    h = X(0) @ Y(1) - 3 * X(1) @ Z(0)
    h_targetless = X() @ Y() - 3 * Z() @ X()
    assert (
        CircuitBinding(circuit, input_sets=input_sets, observables=h).to_ir()
        == CircuitBinding(circuit, input_sets=input_sets, observables=h_targetless).to_ir()
    )


def test_targetless_sum_verbatim_circuit():
    circuit = Circuit().add_verbatim_box(Circuit().rx(1, FreeParameter("theta")).cnot(1, 0))
    input_sets = {"theta": [1.35, 1.58]}
    h = Y(1) @ X(0) - 3 * Z(0) @ X(1)
    h_targetless = Y() @ X() - 3 * X() @ Z()
    assert (
        CircuitBinding(circuit, input_sets=input_sets, observables=h).to_ir()
        == CircuitBinding(circuit, input_sets=input_sets, observables=h_targetless).to_ir()
    )


def test_targetless_observable_in_list():
    circuit = Circuit().rx(1, FreeParameter("theta")).cnot(1, 0)
    input_sets = {"theta": [1.35, 1.58]}
    obs = [X(0) @ Y(1), 3 * Z(0) @ X(1)]
    obs_targetless = [X(0) @ Y(1), 3 * Z() @ X()]
    assert (
        CircuitBinding(circuit, input_sets=input_sets, observables=obs).to_ir()
        == CircuitBinding(circuit, input_sets=input_sets, observables=obs_targetless).to_ir()
    )


def test_targetless_observable_in_list_verbatim_circuit():
    circuit = Circuit().add_verbatim_box(Circuit().rx(1, FreeParameter("theta")).cnot(1, 0))
    input_sets = {"theta": [1.35, 1.58]}
    obs = [Y(1) @ X(0), 3 * Z(0) @ X(1)]
    obs_targetless = [Y() @ X(), 3 * X(1) @ Z(0)]
    assert (
        CircuitBinding(circuit, input_sets=input_sets, observables=obs).to_ir()
        == CircuitBinding(circuit, input_sets=input_sets, observables=obs_targetless).to_ir()
    )


def test_pauli_string_in_list():
    circuit = Circuit().rx(1, FreeParameter("theta")).cnot(1, 0)
    input_sets = {"theta": [1.35, 1.58]}
    obs = [X(0) @ Y(1), -1 * Z(0) @ X(1)]
    obs_ps = [X(0) @ Y(1), PauliString("-ZX")]
    assert (
        CircuitBinding(circuit, input_sets=input_sets, observables=obs).to_ir()
        == CircuitBinding(circuit, input_sets=input_sets, observables=obs_ps).to_ir()
    )


def test_string_in_list():
    circuit = Circuit().rx(1, FreeParameter("theta")).cnot(1, 0)
    input_sets = {"theta": [1.35, 1.58]}
    obs = [X(0) @ Y(1), -1 * Z(0) @ X(1)]
    obs_ps = [X(0) @ Y(1), "-ZX"]
    assert (
        CircuitBinding(circuit, input_sets=input_sets, observables=obs).to_ir()
        == CircuitBinding(circuit, input_sets=input_sets, observables=obs_ps).to_ir()
    )


def test_sum_in_observable_list():
    with pytest.raises(TypeError):
        CircuitBinding(Circuit().h(0), observables=[X(0) + Y(0)])


def test_binding_to_input(circuit_rx_parametrized):
    input_sets = {"theta": [1.35, 1.58]}
    observable = [X(0) @ Z(1), Y(0), Z(0)]
    cb1 = CircuitBinding(circuit_rx_parametrized, input_sets, observable)

    cb2 = cb1.bind_observables_to_inputs(inplace=False)
    assert cb1 != cb2
    assert cb1.to_ir() == cb2.to_ir()

    cb1.bind_observables_to_inputs(inplace=True)
    assert cb1 == cb2


def test_binding_to_input_no_inputs(circuit_rx_parametrized):
    observable = [X(0) @ Z(1), Y(0), Z(0)]
    cb1 = CircuitBinding(circuit_rx_parametrized, observables=observable)

    cb2 = cb1.bind_observables_to_inputs(inplace=False)
    assert cb1 != cb2
    assert cb1.to_ir() == cb2.to_ir()

    cb1.bind_observables_to_inputs(inplace=True)
    assert cb1 == cb2


def test_bind_sum_warning(circuit_rx_parametrized):
    observable = 0.5 * X(0) @ Z(1) + 2 * Y(0)
    cb1 = CircuitBinding(circuit_rx_parametrized, observables=observable)
    with pytest.warns(UserWarning):
        cb1.bind_observables_to_inputs()


def test_no_observables_in_binding(circuit_rx_parametrized):
    input_sets = {"theta": [1.35, 1.58]}
    cb1 = CircuitBinding(circuit_rx_parametrized, input_sets=input_sets)
    cb2 = cb1.bind_observables_to_inputs(inplace=False)
    assert cb1 == cb2


def test_binding_without_measure(circuit_rx_parametrized):
    input_sets = {"theta": [1.35, 1.58]}
    cb1 = CircuitBinding(
        circuit_rx_parametrized,
        input_sets=input_sets,
        observables=0.5 * X(0) @ Z(1) + 2 * Y(0),
    )
    cb2 = cb1.bind_observables_to_inputs(inplace=False, add_measure=False)
    cb3 = cb1.bind_observables_to_inputs(inplace=False, add_measure=True)
    assert cb2.circuit != cb3.circuit
    circ = cb2.circuit
    circ.measure(range(2))
    assert circ == cb3.circuit


def test_string_circuit_no_observables(circuit_rx_parametrized):
    src = _source(circuit_rx_parametrized)
    cb = CircuitBinding(src, input_sets={"theta": [1.23, 3.21]})
    program = cb.to_ir()
    assert program.source == src
    assert program.inputs == {"theta": [1.23, 3.21]}
    # With no observables to inject, the source is emitted verbatim and never parsed.
    assert cb._injection_plan is None


def test_string_circuit_matches_circuit_to_ir(circuit_rx_parametrized):
    circuit = Circuit(circuit_rx_parametrized).cnot(0, 1)
    src = _source(circuit)
    observable = [X(0) @ Z(1)]
    cb_circ = CircuitBinding(circuit, {"theta": [1.23]}, observable)
    cb_str = CircuitBinding(src, {"theta": [1.23]}, observable)
    circ_program = cb_circ.to_ir()
    str_program = cb_str.to_ir()
    assert circ_program.inputs == str_program.inputs
    # Same set of statements; declaration ordering may differ between paths.
    assert sorted(circ_program.source.splitlines()) == sorted(str_program.source.splitlines())


def test_string_circuit_targetless_observable(circuit_rx_parametrized):
    circuit = Circuit(circuit_rx_parametrized).cnot(0, 1)
    src = _source(circuit)
    cb_circ = CircuitBinding(circuit, observables=[X() @ Y()])
    cb_str = CircuitBinding(src, observables=[X() @ Y()])
    assert cb_str.to_ir().inputs == cb_circ.to_ir().inputs


def test_string_circuit_sum_observable(circuit_rx_parametrized):
    circuit = Circuit(circuit_rx_parametrized).cnot(0, 1)
    src = _source(circuit)
    h = 0.5 * X(0) @ Z(1) + 2 * Y(0)
    cb_circ = CircuitBinding(circuit, observables=h)
    cb_str = CircuitBinding(src, observables=h)
    assert cb_str.to_ir().inputs == cb_circ.to_ir().inputs


def test_string_circuit_targetless_sum_observable(circuit_rx_parametrized):
    circuit = Circuit(circuit_rx_parametrized).cnot(0, 1)
    src = _source(circuit)
    h_targetless = X() @ Y() - 3 * Z() @ X()
    cb_circ = CircuitBinding(circuit, observables=h_targetless)
    cb_str = CircuitBinding(src, observables=h_targetless)
    assert cb_str.to_ir().inputs == cb_circ.to_ir().inputs


def test_string_circuit_bind_sum_warning(circuit_rx_parametrized):
    src = _source(circuit_rx_parametrized)
    cb = CircuitBinding(src, observables=0.5 * X(0) @ Z(1) + 2 * Y(0))
    with pytest.warns(UserWarning):
        cb.bind_observables_to_inputs()


def test_string_circuit_custom_register_name():
    src = (
        "OPENQASM 3.0;\n"
        "input float theta;\n"
        "bit[2] b;\n"
        "qubit[2] foo;\n"
        "rx(theta) foo[0];\n"
        "cnot foo[0], foo[1];\n"
        "b[0] = measure foo[0];\n"
        "b[1] = measure foo[1];"
    )
    cb = CircuitBinding(src, input_sets={"theta": [0.5]}, observables=[X(0) @ Y(1)])
    serialized = cb.to_ir().source
    assert "rz(_OBSERVABLE_THETA_0) foo[0];" in serialized
    assert "rz(_OBSERVABLE_THETA_1) foo[1];" in serialized
    assert "q[0]" not in serialized
    assert "q[1]" not in serialized


def test_string_circuit_no_measure_or_version_line():
    # Source with no `OPENQASM 3.0;` line and no measurement — exercises the fallback offsets
    # of _plan_injection for declarations_offset and measure_offset.
    src = "qubit[2] q;\nh q[0];\ncnot q[0], q[1];"
    cb = CircuitBinding(src, observables=[X(0) @ Y(1)])
    serialized = cb.to_ir().source
    # Declarations should be prepended (no OPENQASM line to anchor on).
    assert serialized.startswith("input float ")
    # Rotations should land at the end (no measurement to anchor on).
    assert serialized.rstrip().endswith("rz(_OBSERVABLE_OMEGA_1) q[1];")


def test_string_circuit_single_line_source():
    # A newline-free program must inject the same statements as its multi-line equivalent.
    multiline = (
        "OPENQASM 3.0;\n"
        "input float theta;\n"
        "bit[2] b;\n"
        "qubit[2] q;\n"
        "rx(theta) q[0];\n"
        "cnot q[0], q[1];\n"
        "b[0] = measure q[0];\n"
        "b[1] = measure q[1];"
    )
    single_line = multiline.replace("\n", " ")
    observable = [X(0) @ Z(1)]
    ml_program = CircuitBinding(multiline, {"theta": [0.5]}, observable).to_ir()
    sl_program = CircuitBinding(single_line, {"theta": [0.5]}, observable).to_ir()
    assert sl_program.inputs == ml_program.inputs
    # The injected statements match; only the original (un-split) lines differ in packing.
    injected = "input float _OBSERVABLE"
    assert sl_program.source.count(injected) == ml_program.source.count(injected)
    # Both forms parse back into the same circuit.
    assert Circuit.from_ir(sl_program.source) == Circuit.from_ir(ml_program.source)


def test_string_circuit_single_line_reparses():
    # The injected single-line result must be valid OpenQASM that round-trips through from_ir.
    src = "OPENQASM 3.0; bit[1] b; qubit[1] q; rx(0.5) q[0]; b[0] = measure q[0];"
    serialized = CircuitBinding(src, observables=[X(0)]).to_ir().source
    assert "input float _OBSERVABLE_THETA_0;" in serialized
    assert "rz(_OBSERVABLE_THETA_0) q[0];" in serialized
    # Rotations are injected before the measurement.
    assert serialized.index("rz(_OBSERVABLE_THETA_0)") < serialized.index("measure q[0]")
    Circuit.from_ir(serialized)


def test_string_circuit_midcircuit_measurement():
    # With a mid-circuit measurement, rotations must anchor before the *terminal* measurement
    # block, not the first measurement — otherwise the basis change lands ahead of a readout it
    # is not meant to affect and no-ops for the terminal readout.
    src = (
        "OPENQASM 3.0;\n"
        "bit[2] b;\n"
        "qubit[2] q;\n"
        "h q[0];\n"
        "b[0] = measure q[0];\n"  # mid-circuit measurement
        "if (b[0]) x q[1];\n"
        "b[1] = measure q[1];"  # terminal measurement
    )
    serialized = CircuitBinding(src, observables=[X(0) @ Z(1)]).to_ir().source
    # Rotations sit after the mid-circuit measurement + branch, before the terminal measurement.
    assert (
        serialized.index("b[0] = measure")
        < serialized.index("if (b[0])")
        < serialized.index("rz(_OBSERVABLE_THETA_0)")
        < serialized.index("b[1] = measure")
    )
    # The result is still valid OpenQASM.
    parse(serialized)


def test_string_circuit_measurement_then_gate_is_not_terminal():
    # A lone measurement followed by a gate is not a terminal-measurement block; rotations
    # append at the end (fallback), leaving the earlier measurement untouched.
    src = "OPENQASM 3.0;\nqubit[1] q;\nh q[0];\nb[0] = measure q[0];\nx q[0];"
    serialized = CircuitBinding(src, observables=[X(0)]).to_ir().source
    assert serialized.index("x q[0];") < serialized.index("rz(_OBSERVABLE_THETA_0)")
    assert serialized.rstrip().endswith("rz(_OBSERVABLE_OMEGA_0) q[0];")


def test_string_circuit_no_instructions():
    # An instruction-free (header-only) program has no statements; injected declarations and
    # rotations append after the header, and the result stays valid OpenQASM.
    serialized = CircuitBinding("OPENQASM 3.0;", observables=[X(0)]).to_ir().source
    assert serialized.startswith("OPENQASM 3.0;")
    assert "input float _OBSERVABLE_THETA_0;" in serialized
    assert "rz(_OBSERVABLE_THETA_0) $0;" in serialized
    parse(serialized)


def test_string_circuit_broadcast_gate():
    # A register-broadcast gate (`h q;`) should still yield Euler rotations on every qubit,
    # driven by the declared register size rather than explicit `q[i]` references.
    src = "OPENQASM 3.0;\nqubit[2] q;\nh q;"
    serialized = CircuitBinding(src, observables=[X(0) @ Y(1)]).to_ir().source
    assert "rz(_OBSERVABLE_THETA_0) q[0];" in serialized
    assert "rz(_OBSERVABLE_THETA_1) q[1];" in serialized


def test_string_circuit_single_unindexed_qubit():
    # `qubit q;` (no size) declares a single qubit at index 0.
    src = "OPENQASM 3.0;\nqubit q;\nh q;"
    serialized = CircuitBinding(src, observables=[X(0)]).to_ir().source
    assert "rz(_OBSERVABLE_THETA_0) q[0];" in serialized
    assert "q[1]" not in serialized


def test_circuit_binding_dunders(circuit_rx_parametrized):
    # Exercises the input_sets/observables properties and __len__/__repr__.
    input_sets = {"theta": [1.23, 3.21, 0.5]}
    observable = [X(0), Y(0)]
    cb = CircuitBinding(circuit_rx_parametrized, input_sets, observable)
    assert cb.input_sets.as_dict() == input_sets
    assert list(cb.observables) == observable
    assert len(cb) == 6
    assert len(CircuitBinding(circuit_rx_parametrized, input_sets)) == 3
    assert len(CircuitBinding(circuit_rx_parametrized, observables=observable)) == 2
    assert "CircuitBinding(circuit=" in repr(cb)


def test_string_circuit_physical_qubits(circuit_rx_parametrized):
    verbatim = Circuit().add_verbatim_box(Circuit().rx(1, FreeParameter("theta")).cnot(1, 0))
    src = _source(verbatim)
    cb = CircuitBinding(src, input_sets={"theta": [0.5]}, observables=[X(0) @ Y(1)])
    serialized = cb.to_ir().source
    # Inserted Euler rotations target physical qubits, not virtual q[i].
    assert "rz(_OBSERVABLE_THETA_0) $0;" in serialized
    assert "rz(_OBSERVABLE_THETA_1) $1;" in serialized
    assert "q[" not in serialized.replace("bit[", "")


def test_string_circuit_bind_observables_to_inputs(circuit_rx_parametrized):
    src = _source(circuit_rx_parametrized)
    observable = [X(0) @ Z(1), Y(0), Z(0)]
    cb1 = CircuitBinding(src, input_sets={"theta": [1.35, 1.58]}, observables=observable)

    cb2 = cb1.bind_observables_to_inputs(inplace=False)
    assert cb1 != cb2
    assert cb1.to_ir() == cb2.to_ir()

    cb1.bind_observables_to_inputs(inplace=True)
    assert cb1 == cb2
    # Observables are now folded into the source, so no injection plan remains.
    assert cb1._injection_plan is None


def test_string_circuit_bind_no_observables(circuit_rx_parametrized):
    src = _source(circuit_rx_parametrized)
    cb1 = CircuitBinding(src, input_sets={"theta": [1.35, 1.58]})
    cb2 = cb1.bind_observables_to_inputs(inplace=False)
    assert cb1 == cb2


def test_string_circuit_equality():
    src = "OPENQASM 3.0;\ninput float theta;\nbit[1] b;\nqubit[1] q;\nrx(theta) q[0];"
    input_sets = {"theta": [1.23, 3.21]}
    observable = [X(0)]
    cb = CircuitBinding(src, input_sets, observable)
    assert cb == CircuitBinding(src, input_sets, observable)
    assert cb != CircuitBinding(src, observables=observable)
    assert cb != CircuitBinding(src, input_sets)
