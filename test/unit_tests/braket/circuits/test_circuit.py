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

from unittest.mock import Mock

import numpy as np
import pytest

import braket.ir.jaqcd as jaqcd
from braket.circuits import (
    AsciiCircuitDiagram,
    Circuit,
    FreeParameter,
    Gate,
    Instruction,
    Moments,
    Observable,
    QubitSet,
    ResultType,
    circuit,
    compiler_directives,
    gates,
    noise,
)


@pytest.fixture
def cnot():
    return Circuit().add_instruction(Instruction(Gate.CNot(), [0, 1]))


@pytest.fixture
def cnot_instr():
    return Instruction(Gate.CNot(), [0, 1])


@pytest.fixture
def h():
    return Circuit().add_instruction(Instruction(Gate.H(), 0))


@pytest.fixture
def h_instr():
    return Instruction(Gate.H(), 0)


@pytest.fixture
def prob():
    return ResultType.Probability([0, 1])


@pytest.fixture
def cnot_prob(cnot_instr, prob):
    return Circuit().add_result_type(prob).add_instruction(cnot_instr)


@pytest.fixture
def bell_pair(prob):
    return (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_result_type(prob)
    )


def test_repr_instructions(h):
    expected = f"Circuit('instructions': {h.instructions})"
    assert repr(h) == expected


def test_repr_result_types(cnot_prob):
    circuit = cnot_prob
    expected = (
        f"Circuit('instructions': {circuit.instructions}"
        + f", 'result_types': {circuit.result_types})"
    )
    assert repr(circuit) == expected


def test_str(h):
    expected = AsciiCircuitDiagram.build_diagram(h)
    assert str(h) == expected


def test_equality():
    circ_1 = Circuit().h(0).probability([0, 1])
    circ_2 = Circuit().h(0).probability([0, 1])
    other_circ = Circuit().h(1)
    non_circ = "non circuit"

    assert circ_1 == circ_2
    assert circ_1 is not circ_2
    assert circ_1 != other_circ
    assert circ_1 != non_circ


def test_call():
    alpha = FreeParameter("alpha")
    theta = FreeParameter("theta")
    circ = Circuit().h(0).rx(angle=theta, target=1).ry(angle=alpha, target=0)
    new_circ = circ(theta=1, alpha=0)
    expected = Circuit().h(0).rx(angle=1, target=1).ry(angle=0, target=0)
    assert new_circ == expected and not new_circ.parameters


def test_call_with_result_type(prob):
    alpha = FreeParameter("alpha")
    theta = FreeParameter("theta")
    circ = Circuit().h(0).rx(angle=theta, target=1).ry(angle=alpha, target=0).add_result_type(prob)
    new_circ = circ(theta=1, alpha=0)
    expected = Circuit().h(0).rx(angle=1, target=1).ry(angle=0, target=0).add_result_type(prob)

    assert new_circ == expected and not new_circ.parameters
    assert new_circ.observables_simultaneously_measurable
    assert new_circ.result_types == [prob]


def test_call_one_param_not_bound():
    alpha = FreeParameter("alpha")
    theta = FreeParameter("theta")
    circ = Circuit().h(0).rx(angle=theta, target=1).ry(angle=alpha, target=0)
    new_circ = circ(theta=1)
    expected_circ = Circuit().h(0).rx(angle=1, target=1).ry(angle=alpha, target=0)
    expected_parameters = set()
    expected_parameters.add(alpha)

    assert new_circ == expected_circ and new_circ.parameters == expected_parameters


def test_call_with_default_parameter_val():
    alpha = FreeParameter("alpha")
    beta = FreeParameter("beta")
    theta = FreeParameter("theta")
    gamma = FreeParameter("gamma")
    circ = (
        Circuit()
        .h(0)
        .rx(angle=theta, target=1)
        .ry(angle=alpha, target=0)
        .ry(angle=beta, target=2)
        .rx(angle=gamma, target=1)
    )
    new_circ = circ(np.pi, theta=1, alpha=0)
    expected = (
        Circuit()
        .h(0)
        .rx(angle=1, target=1)
        .ry(angle=0, target=0)
        .ry(angle=np.pi, target=2)
        .rx(angle=np.pi, target=1)
    )
    assert new_circ == expected and not new_circ.parameters


def test_add_result_type_default(prob):
    circ = Circuit().add_result_type(prob)
    assert circ.observables_simultaneously_measurable
    assert circ.result_types == [prob]


def test_add_result_type_with_mapping(prob):
    expected = [ResultType.Probability([10, 11])]
    circ = Circuit().add_result_type(prob, target_mapping={0: 10, 1: 11})
    assert circ.observables_simultaneously_measurable
    assert circ.result_types == expected


def test_add_result_type_with_target(prob):
    expected = [ResultType.Probability([10, 11])]
    circ = Circuit().add_result_type(prob, target=[10, 11])
    assert circ.observables_simultaneously_measurable
    assert circ.result_types == expected


def test_add_result_type_already_exists():
    expected = [ResultType.StateVector()]
    circ = Circuit(expected).add_result_type(expected[0])
    assert circ.observables_simultaneously_measurable
    assert circ.result_types == expected


def test_add_result_type_observable_conflict_target():
    circ = Circuit().add_result_type(ResultType.Probability([0, 1]))
    circ.add_result_type(ResultType.Expectation(observable=Observable.Y(), target=0))
    assert not circ.observables_simultaneously_measurable
    assert not circ.basis_rotation_instructions


def test_add_result_type_observable_conflict_all():
    circ = Circuit().add_result_type(ResultType.Probability())
    circ.add_result_type(ResultType.Expectation(observable=Observable.Y()))
    assert not circ.observables_simultaneously_measurable
    assert not circ.basis_rotation_instructions


def test_add_result_type_observable_conflict_all_target_then_selected_target():
    circ = Circuit().add_result_type(ResultType.Probability())
    circ.add_result_type(ResultType.Expectation(observable=Observable.Y(), target=[0]))
    assert not circ.observables_simultaneously_measurable
    assert not circ.basis_rotation_instructions


def test_add_result_type_observable_conflict_different_selected_targets_then_all_target():
    circ = Circuit().add_result_type(ResultType.Expectation(observable=Observable.Z(), target=[0]))
    circ.add_result_type(ResultType.Expectation(observable=Observable.Y(), target=[1]))
    circ.add_result_type(ResultType.Expectation(observable=Observable.Y()))
    assert not circ.observables_simultaneously_measurable
    assert not circ.basis_rotation_instructions


def test_add_result_type_observable_conflict_selected_target_then_all_target():
    circ = Circuit().add_result_type(ResultType.Expectation(observable=Observable.Y(), target=[1]))
    circ.add_result_type(ResultType.Probability())
    assert not circ.observables_simultaneously_measurable
    assert not circ.basis_rotation_instructions


def test_add_result_type_observable_no_conflict_all_target():
    expected = [
        ResultType.Probability(),
        ResultType.Expectation(observable=Observable.Z(), target=[0]),
    ]
    circ = Circuit(expected)
    assert circ.observables_simultaneously_measurable
    assert circ.result_types == expected


def test_add_result_type_observable_no_conflict_target_all():
    expected = [
        ResultType.Expectation(observable=Observable.Z(), target=[0]),
        ResultType.Probability(),
    ]
    circ = Circuit(expected)
    assert circ.observables_simultaneously_measurable
    assert circ.result_types == expected


def test_add_result_type_observable_no_conflict_all():
    expected = [
        ResultType.Variance(observable=Observable.Y()),
        ResultType.Expectation(observable=Observable.Y()),
    ]
    circ = Circuit(expected)
    assert circ.observables_simultaneously_measurable
    assert circ.result_types == expected


def test_add_result_type_observable_no_conflict_state_vector_obs_return_value():
    expected = [
        ResultType.StateVector(),
        ResultType.Expectation(observable=Observable.Y()),
    ]
    circ = Circuit(expected)
    assert circ.observables_simultaneously_measurable
    assert circ.result_types == expected


def test_add_result_type_same_observable_wrong_target_order_tensor_product():
    circ = (
        Circuit()
        .add_result_type(
            ResultType.Expectation(observable=Observable.Y() @ Observable.X(), target=[0, 1])
        )
        .add_result_type(
            ResultType.Variance(observable=Observable.Y() @ Observable.X(), target=[1, 0])
        )
    )
    assert not circ.observables_simultaneously_measurable
    assert not circ.basis_rotation_instructions


def test_add_result_type_same_observable_wrong_target_order_hermitian():
    array = np.eye(4)
    circ = (
        Circuit()
        .add_result_type(
            ResultType.Expectation(observable=Observable.Hermitian(matrix=array), target=[0, 1])
        )
        .add_result_type(
            ResultType.Variance(observable=Observable.Hermitian(matrix=array), target=[1, 0])
        )
    )
    assert not circ.observables_simultaneously_measurable
    assert not circ.basis_rotation_instructions


@pytest.mark.xfail(raises=TypeError)
def test_add_result_type_with_target_and_mapping(prob):
    Circuit().add_result_type(prob, target=[10], target_mapping={0: 10})


def test_add_instruction_default(cnot_instr):
    circ = Circuit().add_instruction(cnot_instr)
    assert circ.instructions == [cnot_instr]


def test_add_instruction_with_mapping(cnot_instr):
    expected = [Instruction(Gate.CNot(), [10, 11])]
    circ = Circuit().add_instruction(cnot_instr, target_mapping={0: 10, 1: 11})
    assert circ.instructions == expected


def test_add_instruction_with_target(cnot_instr):
    expected = [Instruction(Gate.CNot(), [10, 11])]
    circ = Circuit().add_instruction(cnot_instr, target=[10, 11])
    assert circ.instructions == expected


def test_add_multiple_single_qubit_instruction(h_instr):
    circ = Circuit().add_instruction(h_instr, target=[0, 1, 2, 3])
    expected = Circuit().h(0).h(1).h(2).h(3)
    assert circ == expected


@pytest.mark.xfail(raises=TypeError)
def test_add_instruction_with_target_and_mapping(h):
    Circuit().add_instruction(h, target=[10], target_mapping={0: 10})


def test_add_circuit_default(bell_pair):
    circ = Circuit().add_circuit(bell_pair)
    assert circ == bell_pair


def test_add_circuit_with_mapping(bell_pair):
    circ = Circuit().add_circuit(bell_pair, target_mapping={0: 10, 1: 11})
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 10))
        .add_instruction(Instruction(Gate.CNot(), [10, 11]))
        .add_result_type(ResultType.Probability([10, 11]))
    )
    assert circ == expected


def test_add_circuit_with_target(bell_pair):
    circ = Circuit().add_circuit(bell_pair, target=[10, 11])
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 10))
        .add_instruction(Instruction(Gate.CNot(), [10, 11]))
        .add_result_type(ResultType.Probability([10, 11]))
    )
    assert circ == expected


def test_add_circuit_with_target_and_non_continuous_qubits():
    widget = Circuit().h(5).h(50).h(100)
    circ = Circuit().add_circuit(widget, target=[1, 3, 5])
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 1))
        .add_instruction(Instruction(Gate.H(), 3))
        .add_instruction(Instruction(Gate.H(), 5))
    )
    assert circ == expected


@pytest.mark.xfail(raises=TypeError)
def test_add_circuit_with_target_and_mapping(h):
    Circuit().add_circuit(h, target=[10], target_mapping={0: 10})


def test_add_verbatim_box():
    circ = Circuit().h(0).add_verbatim_box(Circuit().cnot(0, 1))
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(compiler_directives.StartVerbatimBox()))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(compiler_directives.EndVerbatimBox()))
    )
    assert circ == expected


def test_add_verbatim_box_different_qubits():
    circ = Circuit().h(1).add_verbatim_box(Circuit().h(0)).cnot(3, 4)
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 1))
        .add_instruction(Instruction(compiler_directives.StartVerbatimBox()))
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(compiler_directives.EndVerbatimBox()))
        .add_instruction(Instruction(Gate.CNot(), [3, 4]))
    )
    assert circ == expected


def test_add_verbatim_box_no_preceding():
    circ = Circuit().add_verbatim_box(Circuit().h(0)).cnot(2, 3)
    expected = (
        Circuit()
        .add_instruction(Instruction(compiler_directives.StartVerbatimBox()))
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(compiler_directives.EndVerbatimBox()))
        .add_instruction(Instruction(Gate.CNot(), [2, 3]))
    )
    assert circ == expected


def test_add_verbatim_box_empty():
    circuit = Circuit().add_verbatim_box(Circuit())
    assert circuit == Circuit()
    assert not circuit.qubits_frozen


def test_add_verbatim_box_with_mapping(cnot):
    circ = Circuit().add_verbatim_box(cnot, target_mapping={0: 10, 1: 11})
    expected = (
        Circuit()
        .add_instruction(Instruction(compiler_directives.StartVerbatimBox()))
        .add_instruction(Instruction(Gate.CNot(), [10, 11]))
        .add_instruction(Instruction(compiler_directives.EndVerbatimBox()))
    )
    assert circ == expected


def test_add_verbatim_box_with_target(cnot):
    circ = Circuit().add_verbatim_box(cnot, target=[10, 11])
    expected = (
        Circuit()
        .add_instruction(Instruction(compiler_directives.StartVerbatimBox()))
        .add_instruction(Instruction(Gate.CNot(), [10, 11]))
        .add_instruction(Instruction(compiler_directives.EndVerbatimBox()))
    )
    assert circ == expected


@pytest.mark.xfail(raises=TypeError)
def test_add_verbatim_box_with_target_and_mapping(h):
    Circuit().add_verbatim_box(h, target=[10], target_mapping={0: 10})


@pytest.mark.xfail(raises=ValueError)
def test_add_verbatim_box_result_types():
    Circuit().h(0).add_verbatim_box(
        Circuit().cnot(0, 1).expectation(observable=Observable.X(), target=0)
    )


def test_add_with_instruction_with_default(cnot_instr):
    circ = Circuit().add(cnot_instr)
    assert circ == Circuit().add_instruction(cnot_instr)


def test_add_with_instruction_with_mapping(cnot_instr):
    target_mapping = {0: 10, 1: 11}
    circ = Circuit().add(cnot_instr, target_mapping=target_mapping)
    expected = Circuit().add_instruction(cnot_instr, target_mapping=target_mapping)
    assert circ == expected


def test_add_with_instruction_with_target(cnot_instr):
    target = [10, 11]
    circ = Circuit().add(cnot_instr, target=target)
    expected = Circuit().add_instruction(cnot_instr, target=target)
    assert circ == expected


def test_add_with_circuit_with_default(bell_pair):
    circ = Circuit().add(bell_pair)
    assert circ == Circuit().add_circuit(bell_pair)


def test_add_with_circuit_with_mapping(bell_pair):
    target_mapping = {0: 10, 1: 11}
    circ = Circuit().add(bell_pair, target_mapping=target_mapping)
    expected = Circuit().add_circuit(bell_pair, target_mapping=target_mapping)
    assert circ == expected


def test_add_with_circuit_with_target(bell_pair):
    target = [10, 11]
    circ = Circuit().add(bell_pair, target=target)
    expected = Circuit().add_circuit(bell_pair, target=target)
    assert circ == expected


def test_adjoint():
    circ = Circuit().s(0).add_verbatim_box(Circuit().rz(0, 0.123)).expectation(Observable.X(), 0)
    expected = Circuit()
    expected.add_verbatim_box(Circuit().rz(0, -0.123))
    expected.si(0)
    expected.expectation(Observable.X(), 0)
    actual = circ.adjoint()
    assert actual == expected
    assert circ == expected.adjoint()
    assert circ == actual.adjoint()


def test_adjoint_subcircuit_free_parameter():
    circ = Circuit().h(0).add_circuit(Circuit().s(0).rz(0, FreeParameter("theta")).adjoint()).x(0)
    expected = Circuit().h(0).rz(0, -FreeParameter("theta")).si(0).x(0)
    assert circ == expected


def test_circuit_copy(h, bell_pair, cnot_instr):
    original = Circuit().add(h).add(bell_pair).add(cnot_instr)
    copy = original.copy()

    assert copy is not original
    assert copy == original


def test_circuit_copy_with_modification(h, bell_pair, cnot_instr):
    original = Circuit().add(h).add(bell_pair)
    copy = original.copy().add(cnot_instr)

    assert copy != original


def test_iadd_operator(cnot_instr, h):
    circ = Circuit()
    circ += h
    circ += cnot_instr
    circ += [h, cnot_instr]

    assert circ == Circuit().add(h).add(cnot_instr).add(h).add(cnot_instr)


def test_add_operator(h, bell_pair):
    addition = h + bell_pair + h + h
    expected = Circuit().add(h).add(bell_pair).add(h).add(h)

    assert addition == expected
    assert addition != (h + h + bell_pair + h)


@pytest.mark.xfail(raises=TypeError)
def test_iadd_with_unknown_type(h):
    h += 100


def test_subroutine_register():
    # register a private method to avoid Sphinx docs picking this up
    @circuit.subroutine(register=True)
    def _foo(target):
        """this docstring will be added to the registered attribute"""
        return Instruction(Gate.H(), target)

    circ = Circuit()._foo(0)
    assert circ == Circuit(Instruction(Gate.H(), 0))
    assert Circuit._foo.__doc__ == _foo.__doc__


def test_subroutine_returns_circuit():
    @circuit.subroutine()
    def foo(target):
        return Circuit().add(Instruction(Gate.H(), 0))

    circ = Circuit().add(foo, 0)
    assert circ == Circuit(Instruction(Gate.H(), 0))


def test_subroutine_returns_instruction():
    @circuit.subroutine()
    def foo(target):
        return Instruction(Gate.H(), 0)

    circ = Circuit().add(foo, 0)
    assert circ == Circuit(Instruction(Gate.H(), 0))


def test_subroutine_returns_iterable():
    @circuit.subroutine()
    def foo(target):
        for qubit in range(1):
            yield Instruction(Gate.H(), qubit)

    circ = Circuit().add(foo, 0)
    assert circ == Circuit(Instruction(Gate.H(), 0))


def test_subroutine_nested():
    @circuit.subroutine()
    def h(target):
        for qubit in target:
            yield Instruction(Gate.H(), qubit)

    @circuit.subroutine()
    def h_nested(target):
        for qubit in target:
            yield h(target)

    circ = Circuit().add(h_nested, [0, 1])
    expected = Circuit([Instruction(Gate.H(), j) for i in range(2) for j in range(2)])
    assert circ == expected


def test_ir_empty_instructions_result_types():
    circ = Circuit()
    assert circ.to_ir() == jaqcd.Program(
        instructions=[], results=[], basis_rotation_instructions=[]
    )


def test_ir_non_empty_instructions_result_types():
    circ = Circuit().h(0).cnot(0, 1).probability([0, 1])
    expected = jaqcd.Program(
        instructions=[jaqcd.H(target=0), jaqcd.CNot(control=0, target=1)],
        results=[jaqcd.Probability(targets=[0, 1])],
        basis_rotation_instructions=[],
    )
    assert circ.to_ir() == expected


def test_ir_non_empty_instructions_result_types_basis_rotation_instructions():
    circ = Circuit().h(0).cnot(0, 1).sample(observable=Observable.X(), target=[0])
    expected = jaqcd.Program(
        instructions=[jaqcd.H(target=0), jaqcd.CNot(control=0, target=1)],
        results=[jaqcd.Sample(observable=["x"], targets=[0])],
        basis_rotation_instructions=[jaqcd.H(target=0)],
    )
    assert circ.to_ir() == expected


def test_as_unitary_empty_instructions_returns_empty_array():
    circ = Circuit()
    circ.as_unitary() == []


@pytest.mark.parametrize(
    "circuit",
    [
        (Circuit().phaseshift(0, 0.15).apply_gate_noise(noise.Noise.BitFlip(probability=0.1))),
        (Circuit().cnot(1, 0).apply_gate_noise(noise.Noise.TwoQubitDepolarizing(probability=0.1))),
        (
            Circuit()
            .x(1)
            .i(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[1])
        ),
        (
            Circuit()
            .x(1)
            .i(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[2])
        ),
        (Circuit().x(1).i(2).apply_gate_noise(noise.Noise.BitFlip(probability=0.1))),
        (Circuit().x(1).apply_gate_noise(noise.Noise.BitFlip(probability=0.1)).i(2)),
        (
            Circuit()
            .y(1)
            .z(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[1])
        ),
        (
            Circuit()
            .y(1)
            .z(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[2])
        ),
        (Circuit().y(1).z(2).apply_gate_noise(noise.Noise.BitFlip(probability=0.1))),
        (Circuit().y(1).apply_gate_noise(noise.Noise.BitFlip(probability=0.1)).z(2)),
        (
            Circuit()
            .cphaseshift(2, 1, 0.15)
            .si(3)
            .apply_gate_noise(
                noise.Noise.TwoQubitDepolarizing(probability=0.1), target_qubits=[1, 2]
            )
        ),
        (
            Circuit()
            .cphaseshift(2, 1, 0.15)
            .apply_gate_noise(noise.Noise.TwoQubitDepolarizing(probability=0.1))
            .si(3)
        ),
    ],
)
@pytest.mark.xfail(raises=TypeError)
def test_as_unitary_noise_raises_error(circuit):
    circuit.as_unitary()


@pytest.mark.xfail(raises=TypeError)
def test_as_unitary_parameterized():
    theta = FreeParameter("theta")
    circ = Circuit().rx(angle=theta, target=0)
    assert np.allclose(circ.as_unitary())


def test_as_unitary_noise_not_apply_returns_expected_unitary(recwarn):
    circuit = (
        Circuit()
        .cphaseshift(2, 1, 0.15)
        .si(3)
        .apply_gate_noise(noise.Noise.TwoQubitDepolarizing(probability=0.1), target_qubits=[1, 3])
    )

    assert len(recwarn) == 1
    assert str(recwarn[0].message).startswith("Noise is not applied to any gate")

    assert np.allclose(
        circuit.as_unitary(),
        np.kron(gates.Si().to_matrix(), np.kron(gates.CPhaseShift(0.15).to_matrix(), np.eye(2))),
    )


@pytest.mark.parametrize(
    "circuit,expected_unitary",
    [
        (Circuit().h(0), gates.H().to_matrix()),
        (Circuit().h(0).add_result_type(ResultType.Probability(target=[0])), gates.H().to_matrix()),
        (Circuit().x(0), gates.X().to_matrix()),
        (Circuit().y(0), gates.Y().to_matrix()),
        (Circuit().z(0), gates.Z().to_matrix()),
        (Circuit().s(0), gates.S().to_matrix()),
        (Circuit().si(0), gates.Si().to_matrix()),
        (Circuit().t(0), gates.T().to_matrix()),
        (Circuit().ti(0), gates.Ti().to_matrix()),
        (Circuit().v(0), gates.V().to_matrix()),
        (Circuit().vi(0), gates.Vi().to_matrix()),
        (Circuit().rx(0, 0.15), gates.Rx(0.15).to_matrix()),
        (Circuit().ry(0, 0.15), gates.Ry(0.15).to_matrix()),
        (Circuit().rz(0, 0.15), gates.Rz(0.15).to_matrix()),
        (Circuit().phaseshift(0, 0.15), gates.PhaseShift(0.15).to_matrix()),
        (Circuit().cnot(1, 0), gates.CNot().to_matrix()),
        (Circuit().cnot(1, 0).add_result_type(ResultType.StateVector()), gates.CNot().to_matrix()),
        (Circuit().swap(1, 0), gates.Swap().to_matrix()),
        (Circuit().swap(0, 1), gates.Swap().to_matrix()),
        (Circuit().iswap(1, 0), gates.ISwap().to_matrix()),
        (Circuit().iswap(0, 1), gates.ISwap().to_matrix()),
        (Circuit().pswap(1, 0, 0.15), gates.PSwap(0.15).to_matrix()),
        (Circuit().pswap(0, 1, 0.15), gates.PSwap(0.15).to_matrix()),
        (Circuit().xy(1, 0, 0.15), gates.XY(0.15).to_matrix()),
        (Circuit().xy(0, 1, 0.15), gates.XY(0.15).to_matrix()),
        (Circuit().cphaseshift(1, 0, 0.15), gates.CPhaseShift(0.15).to_matrix()),
        (Circuit().cphaseshift00(1, 0, 0.15), gates.CPhaseShift00(0.15).to_matrix()),
        (Circuit().cphaseshift01(1, 0, 0.15), gates.CPhaseShift01(0.15).to_matrix()),
        (Circuit().cphaseshift10(1, 0, 0.15), gates.CPhaseShift10(0.15).to_matrix()),
        (Circuit().cy(1, 0), gates.CY().to_matrix()),
        (Circuit().cz(1, 0), gates.CZ().to_matrix()),
        (Circuit().xx(1, 0, 0.15), gates.XX(0.15).to_matrix()),
        (Circuit().yy(1, 0, 0.15), gates.YY(0.15).to_matrix()),
        (Circuit().zz(1, 0, 0.15), gates.ZZ(0.15).to_matrix()),
        (Circuit().ccnot(2, 1, 0), gates.CCNot().to_matrix()),
        (
            Circuit()
            .ccnot(2, 1, 0)
            .add_result_type(ResultType.Expectation(observable=Observable.Y(), target=[1])),
            gates.CCNot().to_matrix(),
        ),
        (Circuit().ccnot(1, 2, 0), gates.CCNot().to_matrix()),
        (Circuit().cswap(2, 1, 0), gates.CSwap().to_matrix()),
        (Circuit().cswap(2, 0, 1), gates.CSwap().to_matrix()),
        (Circuit().h(1), np.kron(gates.H().to_matrix(), np.eye(2))),
        (Circuit().x(1).i(2), np.kron(np.eye(2), np.kron(gates.X().to_matrix(), np.eye(2)))),
        (
            Circuit().y(1).z(2),
            np.kron(gates.Z().to_matrix(), np.kron(gates.Y().to_matrix(), np.eye(2))),
        ),
        (Circuit().rx(1, 0.15), np.kron(gates.Rx(0.15).to_matrix(), np.eye(2))),
        (
            Circuit().ry(1, 0.15).i(2),
            np.kron(np.eye(2), np.kron(gates.Ry(0.15).to_matrix(), np.eye(2))),
        ),
        (
            Circuit().rz(1, 0.15).s(2),
            np.kron(gates.S().to_matrix(), np.kron(gates.Rz(0.15).to_matrix(), np.eye(2))),
        ),
        (Circuit().pswap(2, 1, 0.15), np.kron(gates.PSwap(0.15).to_matrix(), np.eye(2))),
        (Circuit().pswap(1, 2, 0.15), np.kron(gates.PSwap(0.15).to_matrix(), np.eye(2))),
        (
            Circuit().xy(2, 1, 0.15).i(3),
            np.kron(np.eye(2), np.kron(gates.XY(0.15).to_matrix(), np.eye(2))),
        ),
        (
            Circuit().xy(1, 2, 0.15).i(3),
            np.kron(np.eye(2), np.kron(gates.XY(0.15).to_matrix(), np.eye(2))),
        ),
        (
            Circuit().cphaseshift(2, 1, 0.15).si(3),
            np.kron(
                gates.Si().to_matrix(), np.kron(gates.CPhaseShift(0.15).to_matrix(), np.eye(2))
            ),
        ),
        (Circuit().ccnot(3, 2, 1), np.kron(gates.CCNot().to_matrix(), np.eye(2))),
        (Circuit().ccnot(2, 3, 1), np.kron(gates.CCNot().to_matrix(), np.eye(2))),
        (
            Circuit().cswap(3, 2, 1).i(4),
            np.kron(np.eye(2), np.kron(gates.CSwap().to_matrix(), np.eye(2))),
        ),
        (
            Circuit().cswap(3, 1, 2).i(4),
            np.kron(np.eye(2), np.kron(gates.CSwap().to_matrix(), np.eye(2))),
        ),
        (
            Circuit().cswap(3, 2, 1).t(4),
            np.kron(gates.T().to_matrix(), np.kron(gates.CSwap().to_matrix(), np.eye(2))),
        ),
        (
            Circuit().cswap(3, 1, 2).t(4),
            np.kron(gates.T().to_matrix(), np.kron(gates.CSwap().to_matrix(), np.eye(2))),
        ),
        (Circuit().h(0).h(0), gates.I().to_matrix()),
        (Circuit().h(0).x(0), np.dot(gates.X().to_matrix(), gates.H().to_matrix())),
        (Circuit().x(0).h(0), np.dot(gates.H().to_matrix(), gates.X().to_matrix())),
        (
            Circuit().y(0).z(1).cnot(1, 0),
            np.dot(gates.CNot().to_matrix(), np.kron(gates.Z().to_matrix(), gates.Y().to_matrix())),
        ),
        (
            Circuit().z(0).y(1).cnot(1, 0),
            np.dot(gates.CNot().to_matrix(), np.kron(gates.Y().to_matrix(), gates.Z().to_matrix())),
        ),
        (
            Circuit().z(0).y(1).cnot(1, 0).cnot(2, 1),
            np.dot(
                np.dot(
                    np.dot(
                        np.kron(gates.CNot().to_matrix(), np.eye(2)),
                        np.kron(np.eye(2), gates.CNot().to_matrix()),
                    ),
                    np.kron(np.kron(np.eye(2), gates.Y().to_matrix()), np.eye(2)),
                ),
                np.kron(np.eye(4), gates.Z().to_matrix()),
            ),
        ),
        (
            Circuit().z(0).y(1).cnot(1, 0).ccnot(2, 1, 0),
            np.dot(
                np.dot(
                    np.dot(
                        gates.CCNot().to_matrix(),
                        np.kron(np.eye(2), gates.CNot().to_matrix()),
                    ),
                    np.kron(np.kron(np.eye(2), gates.Y().to_matrix()), np.eye(2)),
                ),
                np.kron(np.eye(4), gates.Z().to_matrix()),
            ),
        ),
        (
            Circuit().cnot(0, 1),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(0, 1, 2),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(1, 0, 2),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(0, 2, 1),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(2, 0, 1),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().s(0).v(1).cnot(0, 1).cnot(1, 2),
            np.dot(
                np.dot(
                    np.dot(
                        np.kron(
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                            np.eye(2),
                        ),
                        np.kron(
                            np.eye(2),
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                        ),
                    ),
                    np.kron(np.kron(np.eye(2), gates.V().to_matrix()), np.eye(2)),
                ),
                np.kron(np.eye(4), gates.S().to_matrix()),
            ),
        ),
        (
            Circuit().z(0).y(1).cnot(0, 1).ccnot(0, 1, 2),
            np.dot(
                np.dot(
                    np.dot(
                        np.array(
                            [
                                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                                [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                            ],
                            dtype=complex,
                        ),
                        np.kron(
                            np.eye(2),
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                        ),
                    ),
                    np.kron(np.kron(np.eye(2), gates.Y().to_matrix()), np.eye(2)),
                ),
                np.kron(np.eye(4), gates.Z().to_matrix()),
            ),
        ),
        (
            Circuit().z(0).y(1).cnot(0, 1).ccnot(2, 0, 1),
            np.dot(
                np.dot(
                    np.dot(
                        np.array(
                            [
                                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                            ],
                            dtype=complex,
                        ),
                        np.kron(
                            np.eye(2),
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                        ),
                    ),
                    np.kron(np.kron(np.eye(2), gates.Y().to_matrix()), np.eye(2)),
                ),
                np.kron(np.eye(4), gates.Z().to_matrix()),
            ),
        ),
    ],
)
def test_as_unitary_one_gate_returns_expected_unitary(circuit, expected_unitary):
    assert np.allclose(circuit.as_unitary(), expected_unitary)


def test_to_unitary_empty_instructions_returns_empty_array():
    circ = Circuit()
    circ.to_unitary() == []


@pytest.mark.parametrize(
    "circuit",
    [
        (Circuit().phaseshift(0, 0.15).apply_gate_noise(noise.Noise.BitFlip(probability=0.1))),
        (Circuit().cnot(1, 0).apply_gate_noise(noise.Noise.TwoQubitDepolarizing(probability=0.1))),
        (
            Circuit()
            .x(1)
            .i(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[1])
        ),
        (
            Circuit()
            .x(1)
            .i(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[2])
        ),
        (Circuit().x(1).i(2).apply_gate_noise(noise.Noise.BitFlip(probability=0.1))),
        (Circuit().x(1).apply_gate_noise(noise.Noise.BitFlip(probability=0.1)).i(2)),
        (
            Circuit()
            .y(1)
            .z(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[1])
        ),
        (
            Circuit()
            .y(1)
            .z(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[2])
        ),
        (Circuit().y(1).z(2).apply_gate_noise(noise.Noise.BitFlip(probability=0.1))),
        (Circuit().y(1).apply_gate_noise(noise.Noise.BitFlip(probability=0.1)).z(2)),
        (
            Circuit()
            .cphaseshift(2, 1, 0.15)
            .si(3)
            .apply_gate_noise(
                noise.Noise.TwoQubitDepolarizing(probability=0.1), target_qubits=[1, 2]
            )
        ),
        (
            Circuit()
            .cphaseshift(2, 1, 0.15)
            .apply_gate_noise(noise.Noise.TwoQubitDepolarizing(probability=0.1))
            .si(3)
        ),
    ],
)
@pytest.mark.xfail(raises=TypeError)
def test_to_unitary_noise_raises_error(circuit):
    circuit.to_unitary()


@pytest.mark.xfail(raises=TypeError)
def test_to_unitary_parameterized():
    theta = FreeParameter("theta")
    circ = Circuit().rx(angle=theta, target=0)
    assert np.allclose(circ.to_unitary())


def test_to_unitary_noise_not_apply_returns_expected_unitary(recwarn):
    circuit = (
        Circuit()
        .cphaseshift(1, 2, 0.15)
        .si(3)
        .apply_gate_noise(noise.Noise.TwoQubitDepolarizing(probability=0.1), target_qubits=[1, 3])
    )

    assert len(recwarn) == 1
    assert str(recwarn[0].message).startswith("Noise is not applied to any gate")

    assert np.allclose(
        circuit.to_unitary(),
        np.kron(gates.CPhaseShift(0.15).to_matrix(), gates.Si().to_matrix()),
    )


@pytest.mark.parametrize(
    "circuit,expected_unitary",
    [
        (Circuit().h(0), gates.H().to_matrix()),
        (Circuit().h(0).add_result_type(ResultType.Probability(target=[0])), gates.H().to_matrix()),
        (Circuit().h(1), gates.H().to_matrix()),
        (Circuit().h(2), gates.H().to_matrix()),
        (Circuit().x(0), gates.X().to_matrix()),
        (Circuit().y(0), gates.Y().to_matrix()),
        (Circuit().z(0), gates.Z().to_matrix()),
        (Circuit().s(0), gates.S().to_matrix()),
        (Circuit().si(0), gates.Si().to_matrix()),
        (Circuit().t(0), gates.T().to_matrix()),
        (Circuit().ti(0), gates.Ti().to_matrix()),
        (Circuit().v(0), gates.V().to_matrix()),
        (Circuit().vi(0), gates.Vi().to_matrix()),
        (Circuit().rx(0, 0.15), gates.Rx(0.15).to_matrix()),
        (Circuit().ry(0, 0.15), gates.Ry(0.15).to_matrix()),
        (Circuit().rz(0, 0.15), gates.Rz(0.15).to_matrix()),
        (Circuit().phaseshift(0, 0.15), gates.PhaseShift(0.15).to_matrix()),
        (Circuit().cnot(0, 1), gates.CNot().to_matrix()),
        (Circuit().cnot(0, 1).add_result_type(ResultType.StateVector()), gates.CNot().to_matrix()),
        (Circuit().cnot(2, 4), gates.CNot().to_matrix()),
        (Circuit().swap(0, 1), gates.Swap().to_matrix()),
        (Circuit().swap(1, 0), gates.Swap().to_matrix()),
        (Circuit().iswap(0, 1), gates.ISwap().to_matrix()),
        (Circuit().iswap(1, 0), gates.ISwap().to_matrix()),
        (Circuit().pswap(0, 1, 0.15), gates.PSwap(0.15).to_matrix()),
        (Circuit().pswap(1, 0, 0.15), gates.PSwap(0.15).to_matrix()),
        (Circuit().xy(0, 1, 0.15), gates.XY(0.15).to_matrix()),
        (Circuit().xy(1, 0, 0.15), gates.XY(0.15).to_matrix()),
        (Circuit().cphaseshift(0, 1, 0.15), gates.CPhaseShift(0.15).to_matrix()),
        (Circuit().cphaseshift00(0, 1, 0.15), gates.CPhaseShift00(0.15).to_matrix()),
        (Circuit().cphaseshift01(0, 1, 0.15), gates.CPhaseShift01(0.15).to_matrix()),
        (Circuit().cphaseshift10(0, 1, 0.15), gates.CPhaseShift10(0.15).to_matrix()),
        (Circuit().cy(0, 1), gates.CY().to_matrix()),
        (Circuit().cz(0, 1), gates.CZ().to_matrix()),
        (Circuit().xx(0, 1, 0.15), gates.XX(0.15).to_matrix()),
        (Circuit().yy(0, 1, 0.15), gates.YY(0.15).to_matrix()),
        (Circuit().zz(0, 1, 0.15), gates.ZZ(0.15).to_matrix()),
        (Circuit().ccnot(0, 1, 2), gates.CCNot().to_matrix()),
        (
            Circuit()
            .ccnot(0, 1, 2)
            .add_result_type(ResultType.Expectation(observable=Observable.Y(), target=[1])),
            gates.CCNot().to_matrix(),
        ),
        (Circuit().ccnot(0, 1, 2), gates.CCNot().to_matrix()),
        (Circuit().cswap(0, 1, 2), gates.CSwap().to_matrix()),
        (Circuit().cswap(0, 2, 1), gates.CSwap().to_matrix()),
        (Circuit().h(1), gates.H().to_matrix()),
        (Circuit().x(1).i(2), np.kron(gates.X().to_matrix(), np.eye(2))),
        (Circuit().y(1).z(2), np.kron(gates.Y().to_matrix(), gates.Z().to_matrix())),
        (Circuit().rx(1, 0.15), gates.Rx(0.15).to_matrix()),
        (Circuit().ry(1, 0.15).i(2), np.kron(gates.Ry(0.15).to_matrix(), np.eye(2))),
        (Circuit().rz(1, 0.15).s(2), np.kron(gates.Rz(0.15).to_matrix(), gates.S().to_matrix())),
        (Circuit().pswap(1, 2, 0.15), gates.PSwap(0.15).to_matrix()),
        (Circuit().pswap(2, 1, 0.15), gates.PSwap(0.15).to_matrix()),
        (Circuit().xy(1, 2, 0.15).i(3), np.kron(gates.XY(0.15).to_matrix(), np.eye(2))),
        (Circuit().xy(2, 1, 0.15).i(3), np.kron(gates.XY(0.15).to_matrix(), np.eye(2))),
        (
            Circuit().cphaseshift(1, 2, 0.15).si(3),
            np.kron(gates.CPhaseShift(0.15).to_matrix(), gates.Si().to_matrix()),
        ),
        (Circuit().ccnot(1, 2, 3), gates.CCNot().to_matrix()),
        (Circuit().ccnot(2, 1, 3), gates.CCNot().to_matrix()),
        (Circuit().cswap(1, 2, 3).i(4), np.kron(gates.CSwap().to_matrix(), np.eye(2))),
        (Circuit().cswap(1, 3, 2).i(4), np.kron(gates.CSwap().to_matrix(), np.eye(2))),
        (Circuit().cswap(1, 2, 3).t(4), np.kron(gates.CSwap().to_matrix(), gates.T().to_matrix())),
        (Circuit().cswap(1, 3, 2).t(4), np.kron(gates.CSwap().to_matrix(), gates.T().to_matrix())),
        (Circuit().h(0).h(0), gates.I().to_matrix()),
        (Circuit().h(0).x(0), np.dot(gates.X().to_matrix(), gates.H().to_matrix())),
        (Circuit().x(0).h(0), np.dot(gates.H().to_matrix(), gates.X().to_matrix())),
        (
            Circuit().y(0).z(1).cnot(0, 1),
            np.dot(gates.CNot().to_matrix(), np.kron(gates.Y().to_matrix(), gates.Z().to_matrix())),
        ),
        (
            Circuit().z(0).y(1).cnot(0, 1),
            np.dot(gates.CNot().to_matrix(), np.kron(gates.Z().to_matrix(), gates.Y().to_matrix())),
        ),
        (
            Circuit().y(0).z(1).cnot(0, 1).cnot(1, 2),
            np.dot(
                np.dot(
                    np.kron(np.eye(2), gates.CNot().to_matrix()),
                    np.kron(gates.CNot().to_matrix(), np.eye(2)),
                ),
                np.kron(np.kron(gates.Y().to_matrix(), gates.Z().to_matrix()), np.eye(2)),
            ),
        ),
        (
            Circuit().z(0).y(1).cnot(0, 1).ccnot(0, 1, 2),
            np.dot(
                np.dot(
                    gates.CCNot().to_matrix(),
                    np.kron(gates.CNot().to_matrix(), np.eye(2)),
                ),
                np.kron(np.kron(gates.Z().to_matrix(), gates.Y().to_matrix()), np.eye(2)),
            ),
        ),
        (
            Circuit().cnot(1, 0),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(1, 2, 0),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(2, 1, 0),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(0, 2, 1),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(2, 0, 1),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().s(0).v(1).cnot(0, 1).cnot(2, 1),
            np.dot(
                np.dot(
                    np.dot(
                        np.kron(
                            np.eye(2),
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                        ),
                        np.kron(
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                            np.eye(2),
                        ),
                    ),
                    np.kron(np.kron(np.eye(2), gates.V().to_matrix()), np.eye(2)),
                ),
                np.kron(gates.S().to_matrix(), np.eye(4)),
            ),
        ),
        (
            Circuit().z(0).y(1).cnot(1, 0).ccnot(2, 1, 0),
            np.dot(
                np.dot(
                    np.dot(
                        np.array(
                            [
                                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                                [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                            ],
                            dtype=complex,
                        ),
                        np.kron(
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                            np.eye(2),
                        ),
                    ),
                    np.kron(np.kron(np.eye(2), gates.Y().to_matrix()), np.eye(2)),
                ),
                np.kron(gates.Z().to_matrix(), np.eye(4)),
            ),
        ),
        (
            Circuit().z(0).y(1).cnot(1, 0).ccnot(2, 0, 1),
            np.dot(
                np.dot(
                    np.dot(
                        np.array(
                            [
                                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                            ],
                            dtype=complex,
                        ),
                        np.kron(
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                            np.eye(2),
                        ),
                    ),
                    np.kron(np.kron(np.eye(2), gates.Y().to_matrix()), np.eye(2)),
                ),
                np.kron(gates.Z().to_matrix(), np.eye(4)),
            ),
        ),
    ],
)
def test_to_matrix_one_gate_returns_expected_unitary(circuit, expected_unitary):
    assert np.allclose(circuit.to_unitary(), expected_unitary)


def test_circuit_with_symbol():
    theta = FreeParameter("theta")

    circ = (
        Circuit()
        .ry(angle=theta, target=0)
        .ry(angle=theta, target=1)
        .ry(angle=theta, target=2)
        .ry(angle=theta, target=3)
    )
    expected = (
        Circuit()
        .ry(angle=theta, target=0)
        .ry(angle=theta, target=1)
        .ry(angle=theta, target=2)
        .ry(angle=theta, target=3)
    )
    assert circ == expected


def test_basis_rotation_instructions_all():
    circ = Circuit().h(0).cnot(0, 1).sample(observable=Observable.Y())
    expected = [
        Instruction(Gate.Z(), 0),
        Instruction(Gate.S(), 0),
        Instruction(Gate.H(), 0),
        Instruction(Gate.Z(), 1),
        Instruction(Gate.S(), 1),
        Instruction(Gate.H(), 1),
    ]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_target():
    circ = Circuit().h(0).cnot(0, 1).expectation(observable=Observable.X(), target=0)
    expected = [Instruction(Gate.H(), 0)]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_tensor_product():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .expectation(observable=Observable.X() @ Observable.Y() @ Observable.Y(), target=[0, 1, 2])
    )
    expected = [
        Instruction(Gate.H(), 0),
        Instruction(Gate.Z(), 1),
        Instruction(Gate.S(), 1),
        Instruction(Gate.H(), 1),
        Instruction(Gate.Z(), 2),
        Instruction(Gate.S(), 2),
        Instruction(Gate.H(), 2),
    ]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_tensor_product_shared_factors():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .expectation(observable=Observable.X() @ Observable.Y() @ Observable.Y(), target=[0, 1, 2])
        .expectation(observable=Observable.X() @ Observable.Y(), target=[0, 1])
    )
    expected = [
        Instruction(Gate.H(), 0),
        Instruction(Gate.Z(), 1),
        Instruction(Gate.S(), 1),
        Instruction(Gate.H(), 1),
        Instruction(Gate.Z(), 2),
        Instruction(Gate.S(), 2),
        Instruction(Gate.H(), 2),
    ]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_identity():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .cnot(1, 2)
        .cnot(2, 3)
        .cnot(3, 4)
        .expectation(observable=Observable.X(), target=[0])
        .expectation(observable=Observable.I(), target=[2])
        .expectation(observable=Observable.I() @ Observable.Y(), target=[1, 3])
        .expectation(observable=Observable.I(), target=[0])
        .expectation(observable=Observable.X() @ Observable.I(), target=[1, 3])
        .expectation(observable=Observable.Y(), target=[2])
    )
    expected = [
        Instruction(Gate.H(), 0),
        Instruction(Gate.H(), 1),
        Instruction(Gate.Z(), 2),
        Instruction(Gate.S(), 2),
        Instruction(Gate.H(), 2),
        Instruction(Gate.Z(), 3),
        Instruction(Gate.S(), 3),
        Instruction(Gate.H(), 3),
    ]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_multiple_result_types_different_targets():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .expectation(observable=Observable.X(), target=0)
        .sample(observable=Observable.H(), target=1)
    )
    expected = [Instruction(Gate.H(), 0), Instruction(Gate.Ry(-np.pi / 4), 1)]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_multiple_result_types_same_targets():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .expectation(observable=Observable.H() @ Observable.X(), target=[0, 1])
        .sample(observable=Observable.H() @ Observable.X(), target=[0, 1])
        .variance(observable=Observable.H() @ Observable.X(), target=[0, 1])
    )
    expected = [Instruction(Gate.Ry(-np.pi / 4), 0), Instruction(Gate.H(), 1)]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_multiple_result_types_all_specified_same_targets():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .expectation(observable=Observable.H())
        .sample(observable=Observable.H(), target=[0])
    )
    expected = [Instruction(Gate.Ry(-np.pi / 4), 0), Instruction(Gate.Ry(-np.pi / 4), 1)]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_multiple_result_types_specified_all_same_targets():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .sample(observable=Observable.H(), target=[0])
        .expectation(observable=Observable.H())
    )
    expected = [Instruction(Gate.Ry(-np.pi / 4), 0), Instruction(Gate.Ry(-np.pi / 4), 1)]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_multiple_result_types_same_targets_hermitian():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .sample(observable=Observable.Hermitian(matrix=np.array([[1, 0], [0, -1]])), target=[1])
        .expectation(
            observable=Observable.Hermitian(matrix=np.array([[1, 0], [0, -1]])), target=[1]
        )
    )
    expected = [Instruction(Gate.Unitary(matrix=np.array([[0, 1], [1, 0]])), target=[1])]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_multiple_result_types_different_hermitian_targets():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .sample(observable=Observable.Hermitian(matrix=np.array([[1, 0], [0, -1]])), target=[1])
        .expectation(observable=Observable.Hermitian(matrix=np.array([[0, 1], [1, 0]])), target=[0])
    )
    expected = [
        Instruction(
            Gate.Unitary(
                matrix=1.0 / np.sqrt(2.0) * np.array([[-1.0, 1.0], [1.0, 1.0]], dtype=complex)
            ),
            target=[0],
        ),
        Instruction(Gate.Unitary(matrix=np.array([[0, 1], [1, 0]])), target=[1]),
    ]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_multiple_result_types_tensor_product_hermitian():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .cnot(1, 2)
        .sample(
            observable=Observable.Hermitian(matrix=np.array([[1, 0], [0, -1]])) @ Observable.H(),
            target=[0, 1],
        )
        .variance(
            observable=Observable.Hermitian(matrix=np.array([[1, 0], [0, -1]])) @ Observable.H(),
            target=[0, 1],
        )
        .expectation(observable=Observable.Hermitian(matrix=np.array([[0, 1], [1, 0]])), target=[2])
    )
    expected = [
        Instruction(Gate.Unitary(matrix=np.array([[0, 1], [1, 0]])), target=[0]),
        Instruction(Gate.Ry(-np.pi / 4), 1),
        Instruction(
            Gate.Unitary(
                matrix=1.0 / np.sqrt(2.0) * np.array([[-1.0, 1.0], [1.0, 1.0]], dtype=complex)
            ),
            target=[2],
        ),
    ]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_multiple_result_types_tensor_product_hermitian_qubit_count_2():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .cnot(1, 2)
        .expectation(observable=Observable.I(), target=[1])
        .sample(
            observable=Observable.Hermitian(matrix=np.eye(4)) @ Observable.H(), target=[0, 1, 2]
        )
        .variance(observable=Observable.H(), target=[2])
        .variance(observable=Observable.Hermitian(matrix=np.eye(4)), target=[0, 1])
        .expectation(observable=Observable.I(), target=[0])
    )
    expected = [
        Instruction(Gate.Unitary(matrix=np.eye(4)), target=[0, 1]),
        Instruction(Gate.Ry(-np.pi / 4), 2),
    ]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_multiple_result_types_tensor_product_probability():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .cnot(1, 2)
        .probability([0, 1])
        .sample(observable=Observable.Z() @ Observable.Z() @ Observable.H(), target=[0, 1, 2])
        .variance(observable=Observable.H(), target=[2])
    )
    expected = [
        Instruction(Gate.Ry(-np.pi / 4), 2),
    ]
    assert circ.basis_rotation_instructions == expected


def test_basis_rotation_instructions_call_twice():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .expectation(observable=Observable.H() @ Observable.X(), target=[0, 1])
        .sample(observable=Observable.H() @ Observable.X(), target=[0, 1])
        .variance(observable=Observable.H() @ Observable.X(), target=[0, 1])
    )
    expected = [Instruction(Gate.Ry(-np.pi / 4), 0), Instruction(Gate.H(), 1)]
    assert circ.basis_rotation_instructions == expected
    assert circ.basis_rotation_instructions == expected


def test_depth_getter(h):
    assert h.depth is h._moments.depth


@pytest.mark.xfail(raises=AttributeError)
def test_depth_setter(h):
    h.depth = 1


def test_instructions_getter(h):
    assert h.instructions == list(h._moments.values())


@pytest.mark.xfail(raises=AttributeError)
def test_instructions_setter(h, h_instr):
    h.instructions = [h_instr]


def test_moments_getter(h):
    assert h.moments is h._moments


@pytest.mark.xfail(raises=AttributeError)
def test_moments_setter(h):
    h.moments = Moments()


def test_qubit_count_getter(h):
    assert h.qubit_count is h._moments.qubit_count


@pytest.mark.xfail(raises=AttributeError)
def test_qubit_count_setter(h):
    h.qubit_count = 1


@pytest.mark.parametrize(
    "circuit,expected_qubit_count",
    [
        (Circuit().h(0).h(1).h(2), 3),
        (
            Circuit()
            .h(0)
            .expectation(observable=Observable.H() @ Observable.X(), target=[0, 1])
            .sample(observable=Observable.H() @ Observable.X(), target=[0, 1]),
            2,
        ),
        (
            Circuit().h(0).probability([1, 2]).state_vector(),
            1,
        ),
        (
            Circuit()
            .h(0)
            .variance(observable=Observable.H(), target=1)
            .state_vector()
            .amplitude(["01"]),
            2,
        ),
    ],
)
def test_qubit_count(circuit, expected_qubit_count):
    assert circuit.qubit_count == expected_qubit_count


@pytest.mark.parametrize(
    "circuit,expected_qubits",
    [
        (Circuit().h(0).h(1).h(2), QubitSet([0, 1, 2])),
        (
            Circuit()
            .h(0)
            .expectation(observable=Observable.H() @ Observable.X(), target=[0, 1])
            .sample(observable=Observable.H() @ Observable.X(), target=[0, 1]),
            QubitSet([0, 1]),
        ),
        (
            Circuit().h(0).probability([1, 2]).state_vector(),
            QubitSet([0]),
        ),
        (
            Circuit()
            .h(0)
            .variance(observable=Observable.H(), target=1)
            .state_vector()
            .amplitude(["01"]),
            QubitSet([0, 1]),
        ),
    ],
)
def test_circuit_qubits(circuit, expected_qubits):
    assert circuit.qubits == expected_qubits


def test_qubits_getter(h):
    assert h.qubits == h._moments.qubits
    assert h.qubits is not h._moments.qubits


@pytest.mark.xfail(raises=AttributeError)
def test_qubits_setter(h):
    h.qubits = QubitSet(1)


def test_diagram(h):
    expected = "foo bar diagram"
    mock_diagram = Mock()
    mock_diagram.build_diagram.return_value = expected

    assert h.diagram(mock_diagram) == expected
    mock_diagram.build_diagram.assert_called_with(h)


def test_add_parameterized_check_true():
    theta = FreeParameter("theta")
    circ = (
        Circuit()
        .ry(angle=theta, target=0)
        .ry(angle=theta, target=1)
        .ry(angle=theta, target=2)
        .ry(angle=theta, target=3)
    )
    expected = set()
    expected.add(theta)

    assert circ.parameters == expected


def test_add_parameterized_instr_parameterized_circ_check_true():
    theta = FreeParameter("theta")
    alpha = FreeParameter("alpha")
    alpha2 = FreeParameter("alpha")
    circ = Circuit().ry(angle=theta, target=0).ry(angle=alpha2, target=1).ry(angle=theta, target=2)
    circ.add_instruction(Instruction(Gate.Ry(alpha), 3))
    expected = set()
    expected.add(theta)
    expected.add(alpha)

    assert circ.parameters == expected


def test_add_non_parameterized_instr_parameterized_check_true():
    theta = FreeParameter("theta")
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=theta, target=2)
    circ.add_instruction(Instruction(Gate.Ry(0.1), 3))
    expected = set()
    expected.add(theta)

    assert circ.parameters == expected


def test_add_circ_parameterized_check_true():
    theta = FreeParameter("theta")
    circ = Circuit().ry(angle=1, target=0).add_circuit(Circuit().ry(angle=theta, target=0))

    expected = set()
    expected.add(theta)

    assert circ.parameters == expected


def test_add_circ_not_parameterized_check_true():
    theta = FreeParameter("theta")
    circ = Circuit().ry(angle=theta, target=0).add_circuit(Circuit().ry(angle=0.1, target=0))

    expected = set()
    expected.add(theta)

    assert circ.parameters == expected


@pytest.mark.parametrize(
    "input_circ",
    [
        (Circuit().ry(angle=1, target=0).ry(angle=2, target=1)),
        (Circuit().ry(angle=1, target=0).add_circuit(Circuit().ry(angle=2, target=0))),
    ],
)
def test_parameterized_check_false(input_circ):
    circ = input_circ
    expected = 0

    assert len(circ.parameters) == expected


def test_parameters():
    theta = FreeParameter("theta")
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=theta, target=2)
    expected = set()
    expected.add(theta)

    assert circ.parameters == expected


def test_no_parameters():
    circ = Circuit().ry(angle=0.12, target=0).ry(angle=0.25, target=1).ry(angle=0.6, target=2)
    expected = set()

    assert circ.parameters == expected


def test_make_bound_circuit_strict():
    theta = FreeParameter("theta")
    input_val = np.pi
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=theta, target=2)
    circ_new = circ.make_bound_circuit({"theta": input_val}, strict=True)
    expected = (
        Circuit().ry(angle=np.pi, target=0).ry(angle=np.pi, target=1).ry(angle=np.pi, target=2)
    )

    assert circ_new == expected


def test_make_bound_circuit_strict_false():
    input_val = np.pi
    theta = FreeParameter("theta")
    param_superset = {"theta": input_val, "alpha": input_val, "beta": input_val}
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=theta, target=2)
    circ_new = circ.make_bound_circuit(param_superset)
    expected = (
        Circuit().ry(angle=np.pi, target=0).ry(angle=np.pi, target=1).ry(angle=np.pi, target=2)
    )

    assert circ_new == expected


def test_make_bound_circuit_multiple():
    theta = FreeParameter("theta")
    alpha = FreeParameter("alpha")
    input_val = np.pi
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=alpha, target=2)
    circ_new = circ.make_bound_circuit({"theta": input_val, "alpha": input_val})
    expected = (
        Circuit().ry(angle=np.pi, target=0).ry(angle=np.pi, target=1).ry(angle=np.pi, target=2)
    )

    assert circ_new == expected


def test_make_bound_circuit_partial_bind():
    theta = FreeParameter("theta")
    alpha = FreeParameter("alpha")
    input_val = np.pi
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=alpha, target=2)
    circ_new = circ.make_bound_circuit({"theta": input_val})
    expected_circ = (
        Circuit().ry(angle=np.pi, target=0).ry(angle=np.pi, target=1).ry(angle=alpha, target=2)
    )
    expected_parameters = set()
    expected_parameters.add(alpha)

    assert circ_new == expected_circ and circ_new.parameters == expected_parameters


@pytest.mark.xfail(raises=ValueError)
def test_make_bound_circuit_non_existent_param():
    theta = FreeParameter("theta")
    input_val = np.pi
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=theta, target=2)
    circ.make_bound_circuit({"alpha": input_val}, strict=True)


@pytest.mark.xfail(raises=ValueError)
def test_make_bound_circuit_bad_value():
    theta = FreeParameter("theta")
    input_val = "invalid"
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=theta, target=2)
    circ.make_bound_circuit({"theta": input_val})


def test_circuit_with_expr():
    theta = FreeParameter("theta")
    alpha = FreeParameter("alpha")
    circ = (
        Circuit()
        .ry(angle=theta * 2 + theta, target=0)
        .rx(angle=(alpha + theta + 2 * alpha * theta), target=2)
        .rz(angle=theta, target=1)
    )
    circ.add_instruction(Instruction(Gate.Ry(alpha), 3))

    new_circ = circ(theta=1, alpha=np.pi)
    expected = (
        Circuit()
        .ry(angle=3, target=0)
        .rx(angle=(3 * np.pi + 1), target=2)
        .rz(angle=1, target=1)
        .ry(angle=np.pi, target=3)
    )

    assert new_circ == expected


def test_circuit_with_expr_not_fully_bound():
    theta = FreeParameter("theta")
    alpha = FreeParameter("alpha")
    circ = (
        Circuit()
        .ry(angle=theta * 2 + theta, target=0)
        .rx(angle=(alpha + theta + 2 * alpha * theta), target=2)
        .rz(angle=theta, target=1)
    )
    circ.add_instruction(Instruction(Gate.Ry(alpha), 3))

    new_circ = circ(theta=1)
    expected = (
        Circuit()
        .ry(angle=3, target=0)
        .rx(angle=(3 * alpha + 1), target=2)
        .rz(angle=1, target=1)
        .ry(angle=alpha, target=3)
    )
    assert new_circ == expected
