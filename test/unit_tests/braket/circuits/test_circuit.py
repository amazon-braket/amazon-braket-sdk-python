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
    Circuit,
    FreeParameter,
    FreeParameterExpression,
    Gate,
    Instruction,
    Moments,
    Noise,
    Observable,
    QubitSet,
    ResultType,
    UnicodeCircuitDiagram,
    circuit,
    compiler_directives,
    gates,
    noise,
    observables,
)
from braket.circuits.gate_calibrations import GateCalibrations
from braket.circuits.measure import Measure
from braket.circuits.noises import BitFlip
from braket.circuits.parameterizable import Parameterizable
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
)
from braket.circuits.translations import braket_result_to_result_type
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.pulse import DragGaussianWaveform, Frame, GaussianWaveform, Port, PulseSequence


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


@pytest.fixture
def port():
    return Port(port_id="device_port_x0", dt=1e-9, properties={})


@pytest.fixture
def predefined_frame_1(port):
    return Frame(
        frame_id="predefined_frame_1", frequency=2e9, port=port, phase=0, is_predefined=True
    )


@pytest.fixture
def user_defined_frame(port):
    return Frame(
        frame_id="user_defined_frame_0",
        port=port,
        frequency=1e7,
        phase=3.14,
        is_predefined=False,
        properties={"associatedGate": "rz"},
    )


@pytest.fixture
def pulse_sequence(predefined_frame_1):
    return (
        PulseSequence()
        .set_frequency(
            predefined_frame_1,
            6e6,
        )
        .play(
            predefined_frame_1,
            DragGaussianWaveform(length=3e-3, sigma=0.4, beta=0.2, id="drag_gauss_wf"),
        )
    )


@pytest.fixture
def pulse_sequence_2(predefined_frame_1):
    return (
        PulseSequence()
        .shift_phase(
            predefined_frame_1,
            FreeParameter("alpha"),
        )
        .set_phase(
            predefined_frame_1,
            FreeParameter("gamma"),
        )
        .shift_phase(
            predefined_frame_1,
            FreeParameter("beta"),
        )
        .play(
            predefined_frame_1,
            DragGaussianWaveform(length=3e-3, sigma=0.4, beta=0.2, id="drag_gauss_wf"),
        )
    )


@pytest.fixture
def pulse_sequence_3(predefined_frame_1):
    return (
        PulseSequence()
        .shift_phase(
            predefined_frame_1,
            FreeParameter("alpha"),
        )
        .shift_phase(
            predefined_frame_1,
            FreeParameter("beta"),
        )
        .play(
            predefined_frame_1,
            DragGaussianWaveform(length=3e-3, sigma=0.4, beta=0.2, id="drag_gauss_wf"),
        )
    )


@pytest.fixture
def gate_calibrations(pulse_sequence, pulse_sequence_2):
    calibration_key = (Gate.Z(), QubitSet([0, 1]))
    calibration_key_2 = (Gate.Rx(FreeParameter("theta")), QubitSet([0]))
    calibration_key_3 = (
        Gate.MS(FreeParameter("alpha"), FreeParameter("beta"), FreeParameter("gamma")),
        QubitSet([0, 1]),
    )
    return GateCalibrations({
        calibration_key: pulse_sequence,
        calibration_key_2: pulse_sequence,
        calibration_key_3: pulse_sequence_2,
    })


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
    expected = UnicodeCircuitDiagram.build_diagram(h)
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
    expected_parameters = {alpha}
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


def test_add_result_type_observable_no_conflict_all_identity():
    expected = [
        ResultType.Variance(observable=Observable.Y()),
        ResultType.Expectation(observable=Observable.I()),
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


def test_add_result_type_with_target_and_mapping(prob):
    with pytest.raises(TypeError):
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


def test_add_instruction_with_target_and_mapping(h):
    with pytest.raises(TypeError):
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


def test_add_circuit_with_target_and_mapping(h):
    with pytest.raises(TypeError):
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


def test_add_verbatim_box_with_target_and_mapping(h):
    with pytest.raises(TypeError):
        Circuit().add_verbatim_box(h, target=[10], target_mapping={0: 10})


def test_add_verbatim_box_result_types():
    with pytest.raises(ValueError):
        Circuit().h(0).add_verbatim_box(
            Circuit().cnot(0, 1).expectation(observable=Observable.X(), target=0)
        )


def test_measure():
    circ = Circuit().h(0).cnot(0, 1).measure([0])
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Measure(), 0))
    )
    assert circ == expected


def test_measure_int():
    circ = Circuit().h(0).cnot(0, 1).measure(0)
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Measure(), 0))
    )
    assert circ == expected


def test_measure_multiple_targets():
    circ = Circuit().h(0).cnot(0, 1).cnot(1, 2).cnot(2, 3).measure([0, 1, 3])
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.CNot(), [1, 2]))
        .add_instruction(Instruction(Gate.CNot(), [2, 3]))
        .add_instruction(Instruction(Measure(), 0))
        .add_instruction(Instruction(Measure(), 1))
        .add_instruction(Instruction(Measure(), 3))
    )
    assert circ == expected
    assert circ._measure_targets == [0, 1, 3]


def test_measure_with_noise():
    circ = Circuit().x(0).x(1).bit_flip(0, probability=0.1).measure(0)
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.X(), 1))
        .add_instruction(Instruction(BitFlip(probability=0.1), 0))
        .add_instruction(Instruction(Measure(), 0))
    )
    assert circ == expected


def test_measure_verbatim_box():
    circ = Circuit().add_verbatim_box(Circuit().x(0).x(1)).measure(0)
    expected = (
        Circuit()
        .add_instruction(Instruction(compiler_directives.StartVerbatimBox()))
        .add_instruction(Instruction(Gate.X(), 0))
        .add_instruction(Instruction(Gate.X(), 1))
        .add_instruction(Instruction(compiler_directives.EndVerbatimBox()))
        .add_instruction(Instruction(Measure(), 0))
    )
    expected_ir = OpenQasmProgram(
        source="\n".join([
            "OPENQASM 3.0;",
            "bit[1] b;",
            "qubit[2] q;",
            "#pragma braket verbatim",
            "box{",
            "x q[0];",
            "x q[1];",
            "}",
            "b[0] = measure q[0];",
        ]),
        inputs={},
    )
    assert circ == expected
    assert circ.to_ir("OPENQASM") == expected_ir


def test_measure_in_verbatim_subcircuit():
    message = "cannot measure a subcircuit inside a verbatim box."
    with pytest.raises(ValueError, match=message):
        Circuit().add_verbatim_box(Circuit().x(0).x(1).measure(0))


def test_measure_qubits_out_of_range():
    circ = Circuit().h(0).cnot(0, 1).measure(4)
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Measure(), 4))
    )
    assert circ == expected


def test_measure_empty_circuit():
    circ = Circuit().measure([0, 1, 2])
    expected = (
        Circuit()
        .add_instruction(Instruction(Measure(), 0))
        .add_instruction(Instruction(Measure(), 1))
        .add_instruction(Instruction(Measure(), 2))
    )
    assert circ == expected


def test_measure_target_input():
    message = "Supplied qubit index, 1.1, must be an integer."
    with pytest.raises(TypeError, match=message):
        Circuit().h(0).cnot(0, 1).measure(1.1)

    message = "Supplied qubit index, a, must be an integer."
    with pytest.raises(TypeError, match=message):
        Circuit().h(0).cnot(0, 1).measure(FreeParameter("a"))


def test_measure_with_result_types():
    message = "a circuit cannot contain both measure instructions and result types."
    with pytest.raises(ValueError, match=message):
        Circuit().h(0).sample(observable=Observable.Z(), target=0).measure(0)


def test_result_type_with_measure():
    message = "cannot add a result type to a circuit which already contains a measure instruction."
    with pytest.raises(ValueError, match=message):
        Circuit().h(0).measure(0).sample(observable=Observable.Z(), target=0)


def test_measure_with_multiple_measures():
    circ = Circuit().h(0).cnot(0, 1).h(2).measure([0, 1]).measure(2)
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.H(), 2))
        .add_instruction(Instruction(Measure(), 0))
        .add_instruction(Instruction(Measure(), 1))
        .add_instruction(Instruction(Measure(), 2))
    )
    assert circ == expected


def test_measure_same_qubit_twice():
    # message = "cannot measure the same qubit\\(s\\) Qubit\\(0\\) more than once."
    message = "cannot apply instruction to measured qubits."
    with pytest.raises(ValueError, match=message):
        Circuit().h(0).cnot(0, 1).measure(0).measure(1).measure(0)


def test_measure_same_qubit_twice_with_list():
    # message = "cannot measure the same qubit\\(s\\) Qubit\\(0\\) more than once."
    message = "cannot apply instruction to measured qubits."
    with pytest.raises(ValueError, match=message):
        Circuit().h(0).cnot(0, 1).measure(0).measure([0, 1])


def test_measure_same_qubit_twice_with_one_measure():
    message = "cannot repeat qubit\\(s\\) 0 in the same measurement."
    with pytest.raises(ValueError, match=message):
        Circuit().h(0).cnot(0, 1).measure([0, 0, 0])


def test_measure_gate_after():
    # message = "cannot add a gate or noise operation on a qubit after a measure instruction."
    message = "cannot apply instruction to measured qubits."
    with pytest.raises(ValueError, match=message):
        Circuit().h(0).measure(0).h([0, 1])

    # message = "cannot add a gate or noise operation on a qubit after a measure instruction."
    message = "cannot apply instruction to measured qubits."
    with pytest.raises(ValueError, match=message):
        instr = Instruction(Gate.CNot(), [0, 1])
        Circuit().measure([0, 1]).add_instruction(instr, target_mapping={0: 0, 1: 1})

    # message = "cannot add a gate or noise operation on a qubit after a measure instruction."
    message = "cannot apply instruction to measured qubits."
    with pytest.raises(ValueError, match=message):
        instr = Instruction(Gate.CNot(), [0, 1])
        Circuit().h(0).measure(0).add_instruction(instr, target=[0, 1])


def test_measure_noise_after():
    # message = "cannot add a gate or noise operation on a qubit after a measure instruction."
    message = "cannot apply instruction to measured qubits."
    with pytest.raises(ValueError, match=message):
        Circuit().h(1).h(1).h(2).h(5).h(4).h(3).cnot(1, 2).measure([0, 1, 2, 3, 4]).kraus(
            targets=[0], matrices=[np.array([[1, 0], [0, 1]])]
        )


def test_measure_with_readout_noise():
    circ = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .apply_readout_noise(Noise.BitFlip(probability=0.1), target_qubits=1)
        .measure([0, 1])
    )
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .apply_readout_noise(Noise.BitFlip(probability=0.1), target_qubits=1)
        .add_instruction(Instruction(Measure(), 0))
        .add_instruction(Instruction(Measure(), 1))
    )
    assert circ == expected


def test_measure_gate_after_with_target_mapping():
    # message = "cannot add a gate or noise operation on a qubit after a measure instruction."
    message = "cannot apply instruction to measured qubits."
    instr = Instruction(Gate.CNot(), [0, 1])
    with pytest.raises(ValueError, match=message):
        Circuit().h(0).cnot(0, 1).cnot(1, 2).measure([0, 1]).add_instruction(
            instr, target_mapping={0: 10, 1: 11}
        )


def test_measure_gate_after_with_target():
    # message = "cannot add a gate or noise operation on a qubit after a measure instruction."
    message = "cannot apply instruction to measured qubits."
    instr = Instruction(Gate.CNot(), [0, 1])
    with pytest.raises(ValueError, match=message):
        Circuit().h(0).cnot(0, 1).cnot(1, 2).measure([0, 1]).add_instruction(instr, target=[10, 11])


def test_measure_gate_after_measurement():
    circ = Circuit().h(0).cnot(0, 1).cnot(1, 2).measure(0).h(2)
    expected = (
        Circuit()
        .add_instruction(Instruction(Gate.H(), 0))
        .add_instruction(Instruction(Gate.CNot(), [0, 1]))
        .add_instruction(Instruction(Gate.CNot(), [1, 2]))
        .add_instruction(Instruction(Measure(), 0))
        .add_instruction(Instruction(Gate.H(), 2))
    )
    assert circ == expected


def test_to_ir_with_measure():
    circ = Circuit().h(0).cnot(0, 1).cnot(1, 2).measure([0, 2])
    expected_ir = OpenQasmProgram(
        source="\n".join([
            "OPENQASM 3.0;",
            "bit[2] b;",
            "qubit[3] q;",
            "h q[0];",
            "cnot q[0], q[1];",
            "cnot q[1], q[2];",
            "b[0] = measure q[0];",
            "b[1] = measure q[2];",
        ]),
        inputs={},
    )
    assert circ.to_ir("OPENQASM") == expected_ir


def test_from_ir_with_measure():
    ir = OpenQasmProgram(
        source="\n".join([
            "OPENQASM 3.0;",
            "bit[1] b;",
            "qubit[3] q;",
            "h q[0];",
            "cnot q[0], q[1];",
            "cnot q[1], q[2];",
            "b[0] = measure q[0];",
            "b[1] = measure q[2];",
        ]),
        inputs={},
    )
    expected_circ = Circuit().h(0).cnot(0, 1).cnot(1, 2).measure(0).measure(2)
    assert Circuit.from_ir(source=ir.source, inputs=ir.inputs) == expected_circ


def test_from_ir_with_single_measure():
    ir = OpenQasmProgram(
        source="\n".join([
            "OPENQASM 3.0;",
            "bit[2] b;",
            "qubit[2] q;",
            "h q[0];",
            "cnot q[0], q[1];",
            "b = measure q;",
        ]),
        inputs={},
    )
    expected_circ = Circuit().h(0).cnot(0, 1).measure(0).measure(1)
    assert Circuit.from_ir(source=ir.source, inputs=ir.inputs) == expected_circ


def test_from_ir_round_trip_transformation():
    circuit = Circuit().h(0).cnot(0, 1).measure(0).measure(1)
    ir = OpenQasmProgram(
        source="\n".join([
            "OPENQASM 3.0;",
            "bit[2] b;",
            "qubit[2] q;",
            "h q[0];",
            "cnot q[0], q[1];",
            "b = measure q;",
        ]),
        inputs={},
    )

    assert Circuit.from_ir(ir) == Circuit.from_ir(circuit.to_ir("OPENQASM"))
    assert circuit.to_ir("OPENQASM") == Circuit.from_ir(ir).to_ir("OPENQASM")


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


def test_iadd_with_unknown_type(h):
    with pytest.raises(TypeError):
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


@pytest.mark.parametrize(
    "circuit, serialization_properties, expected_ir",
    [
        (
            Circuit()
            .rx(0, 0.15)
            .ry(1, FreeParameterExpression("0.3"))
            .rx(2, 3 * FreeParameterExpression(1)),
            OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[3] b;",
                    "qubit[3] q;",
                    "rx(0.15) q[0];",
                    "ry(0.3) q[1];",
                    "rx(3) q[2];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                    "b[2] = measure q[2];",
                ]),
                inputs={},
            ),
        ),
    ],
)
def test_circuit_to_ir_openqasm(circuit, serialization_properties, expected_ir):
    assert (
        circuit.to_ir(
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
        )
        == expected_ir
    )


@pytest.mark.parametrize(
    "circuit, serialization_properties, expected_ir",
    [
        (
            Circuit().rx(0, 0.15).rx(1, 0.3),
            OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "cal {",
                    "    waveform drag_gauss_wf = drag_gaussian"
                    + "(3.0ms, 400.0ms, 0.2, 1, false);",
                    "}",
                    "defcal z $0, $1 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "defcal rx(0.15) $0 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "rx(0.15) q[0];",
                    "rx(0.3) q[1];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().rx(0, 0.15).rx(4, 0.3),
            OpenQASMSerializationProperties(QubitReferenceType.PHYSICAL),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "cal {",
                    "    waveform drag_gauss_wf = drag_gaussian"
                    + "(3.0ms, 400.0ms, 0.2, 1, false);",
                    "}",
                    "defcal z $0, $1 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "defcal rx(0.15) $0 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "rx(0.15) $0;",
                    "rx(0.3) $4;",
                    "b[0] = measure $0;",
                    "b[1] = measure $4;",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit()
            .rx(0, 0.15)
            .add_verbatim_box(Circuit().rx(4, 0.3))
            .expectation(observable=Observable.I()),
            OpenQASMSerializationProperties(QubitReferenceType.PHYSICAL),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "cal {",
                    "    waveform drag_gauss_wf = drag_gaussian"
                    + "(3.0ms, 400.0ms, 0.2, 1, false);",
                    "}",
                    "defcal z $0, $1 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "defcal rx(0.15) $0 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "rx(0.15) $0;",
                    "#pragma braket verbatim",
                    "box{",
                    "rx(0.3) $4;",
                    "}",
                    "#pragma braket result expectation i all",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit()
            .rx(0, 0.15)
            .rx(4, 0.3)
            .bit_flip(3, probability=0.2)
            .expectation(observable=Observable.I(), target=0),
            None,
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "qubit[5] q;",
                    "cal {",
                    "    waveform drag_gauss_wf = drag_gaussian"
                    + "(3.0ms, 400.0ms, 0.2, 1, false);",
                    "}",
                    "defcal z $0, $1 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "defcal rx(0.15) $0 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "rx(0.15) q[0];",
                    "rx(0.3) q[4];",
                    "#pragma braket noise bit_flip(0.2) q[3]",
                    "#pragma braket result expectation i(q[0])",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().rx(0, 0.15).rx(1, FreeParameter("theta")),
            OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "input float theta;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "cal {",
                    "    waveform drag_gauss_wf = drag_gaussian"
                    + "(3.0ms, 400.0ms, 0.2, 1, false);",
                    "}",
                    "defcal z $0, $1 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "defcal rx(0.15) $0 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "rx(0.15) q[0];",
                    "rx(theta) q[1];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit()
            .rx(0, 0.15, control=2, control_state=0)
            .rx(1, 0.3, control=[2, 3])
            .cnot(target=0, control=[2, 3, 4]),
            OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[5] b;",
                    "qubit[5] q;",
                    "cal {",
                    "    waveform drag_gauss_wf = drag_gaussian"
                    + "(3.0ms, 400.0ms, 0.2, 1, false);",
                    "}",
                    "defcal z $0, $1 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "defcal rx(0.15) $0 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "negctrl @ rx(0.15) q[2], q[0];",
                    "ctrl(2) @ rx(0.3) q[2], q[3], q[1];",
                    "ctrl(2) @ cnot q[2], q[3], q[4], q[0];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                    "b[2] = measure q[2];",
                    "b[3] = measure q[3];",
                    "b[4] = measure q[4];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().cnot(0, 1).cnot(target=2, control=3).cnot(target=4, control=[5, 6]),
            OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[7] b;",
                    "qubit[7] q;",
                    "cal {",
                    "    waveform drag_gauss_wf = drag_gaussian"
                    + "(3.0ms, 400.0ms, 0.2, 1, false);",
                    "}",
                    "defcal z $0, $1 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "cnot q[0], q[1];",
                    "cnot q[3], q[2];",
                    "ctrl @ cnot q[5], q[6], q[4];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                    "b[2] = measure q[2];",
                    "b[3] = measure q[3];",
                    "b[4] = measure q[4];",
                    "b[5] = measure q[5];",
                    "b[6] = measure q[6];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0, power=-2.5).h(0, power=0).ms(0, 1, -0.1, -0.2, -0.3),
            OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "cal {",
                    "    waveform drag_gauss_wf = drag_gaussian"
                    + "(3.0ms, 400.0ms, 0.2, 1, false);",
                    "}",
                    "defcal z $0, $1 {",
                    "    set_frequency(predefined_frame_1, 6000000.0);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "defcal ms(-0.1, -0.2, -0.3) $0, $1 {",
                    "    shift_phase(predefined_frame_1, -0.1);",
                    "    set_phase(predefined_frame_1, -0.3);",
                    "    shift_phase(predefined_frame_1, -0.2);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "inv @ pow(2.5) @ h q[0];",
                    "pow(0) @ h q[0];",
                    "ms(-0.1, -0.2, -0.3) q[0], q[1];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        pytest.param(
            Circuit().h(0, power=-2.5).h(0, power=0).rx(0, angle=FreeParameter("theta")),
            OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL),
            OpenQasmProgram(
                source="",
                inputs={},
            ),
            marks=pytest.mark.xfail(
                reason="Parametric calibrations cannot be attached with parametric circuits."
            ),
        ),
    ],
)
def test_circuit_to_ir_openqasm_with_gate_calibrations(
    circuit, serialization_properties, expected_ir, gate_calibrations
):
    copy_of_gate_calibrations = gate_calibrations.copy()
    assert (
        circuit.to_ir(
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
            gate_definitions=gate_calibrations.pulse_sequences,
        )
        == expected_ir
    )
    assert copy_of_gate_calibrations.pulse_sequences == gate_calibrations.pulse_sequences


@pytest.mark.parametrize(
    "circuit, calibration_key, expected_ir",
    [
        (
            Circuit().rx(0, 0.2),
            (Gate.Rx(FreeParameter("alpha")), QubitSet(0)),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "input float beta;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "cal {",
                    "    waveform drag_gauss_wf = drag_gaussian(3.0ms, 400.0ms, 0.2, 1, false);",
                    "}",
                    "defcal rx(0.2) $0 {",
                    "    shift_phase(predefined_frame_1, 0.2);",
                    "    shift_phase(predefined_frame_1, beta);",
                    "    play(predefined_frame_1, drag_gauss_wf);",
                    "}",
                    "rx(0.2) q[0];",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
    ],
)
def test_circuit_with_parametric_defcal(circuit, calibration_key, expected_ir, pulse_sequence_3):
    serialization_properties = OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL)
    gate_calibrations = GateCalibrations({
        calibration_key: pulse_sequence_3,
    })

    assert (
        circuit.to_ir(
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
            gate_definitions=gate_calibrations.pulse_sequences,
        )
        == expected_ir
    )


def test_parametric_circuit_with_fixed_argument_defcal(pulse_sequence):
    circ = Circuit().h(0, power=-2.5).h(0, power=0).rx(0, angle=FreeParameter("theta"))
    serialization_properties = OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL)
    calibration_key = (Gate.Z(), QubitSet([0, 1]))
    calibration_key_2 = (Gate.Rx(0.45), QubitSet([0]))
    gate_calibrations = GateCalibrations({
        calibration_key: pulse_sequence,
        calibration_key_2: pulse_sequence,
    })

    expected_ir = OpenQasmProgram(
        source="\n".join([
            "OPENQASM 3.0;",
            "input float theta;",
            "bit[1] b;",
            "qubit[1] q;",
            "cal {",
            "    waveform drag_gauss_wf = drag_gaussian(3.0ms, 400.0ms, 0.2, 1, false);",
            "}",
            "defcal z $0, $1 {",
            "    set_frequency(predefined_frame_1, 6000000.0);",
            "    play(predefined_frame_1, drag_gauss_wf);",
            "}",
            "defcal rx(0.45) $0 {",
            "    set_frequency(predefined_frame_1, 6000000.0);",
            "    play(predefined_frame_1, drag_gauss_wf);",
            "}",
            "inv @ pow(2.5) @ h q[0];",
            "pow(0) @ h q[0];",
            "rx(theta) q[0];",
            "b[0] = measure q[0];",
        ]),
        inputs={},
    )

    assert (
        circ.to_ir(
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
            gate_definitions=gate_calibrations.pulse_sequences,
        )
        == expected_ir
    )


@pytest.mark.xfail(
    reasons="Calibrations with a partial number of fixed parameters are not supported."
)
def test_circuit_with_partial_calibrations(pulse_sequence_2):
    circuit = Circuit().h(0, power=-2.5).h(0, power=0).ms(0, 1, -0.1, -0.2, -0.3)
    serialization_properties = OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL)
    gate_calibrations = (
        GateCalibrations({
            (Gate.MS(-0.1, FreeParameter("beta"), -0.3), QubitSet([0, 1])): pulse_sequence_2
        }),
    )
    circuit.to_ir(
        ir_type=IRType.OPENQASM,
        serialization_properties=serialization_properties,
        gate_definitions=gate_calibrations.pulse_sequences,
    )


def test_circuit_user_gate(pulse_sequence_2):
    class Foo(Gate, Parameterizable):
        def __init__(
            self,
            bar,
        ):
            super().__init__(qubit_count=1, ascii_symbols=["Foo"])
            self._parameters = [bar]

        @property
        def parameters(self):
            return self._parameters

        def bind_values(self, **kwargs):
            raise NotImplementedError

        @property
        def _qasm_name(self):
            return "foo"

        def __hash__(self):
            return hash((self.name, self.parameters[0], self.qubit_count))

        @staticmethod
        @circuit.subroutine(register=True)
        def foo(
            target,
            bar,
        ):
            return Instruction(Foo(bar), target=target)

    Gate.register_gate(Foo)

    circ = Circuit().foo(0, -0.2)
    serialization_properties = OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL)
    gate_calibrations = GateCalibrations({
        (Foo(FreeParameter("beta")), QubitSet(0)): pulse_sequence_2(**{
            "alpha": -0.1,
            "gamma": -0.3,
        })
    })

    expected_ir = OpenQasmProgram(
        source="\n".join([
            "OPENQASM 3.0;",
            "bit[1] b;",
            "qubit[1] q;",
            "cal {",
            "    waveform drag_gauss_wf = drag_gaussian(3.0ms, 400.0ms, 0.2, 1, false);",
            "}",
            "defcal foo(-0.2) $0 {",
            "    shift_phase(predefined_frame_1, -0.1);",
            "    set_phase(predefined_frame_1, -0.3);",
            "    shift_phase(predefined_frame_1, -0.2);",
            "    play(predefined_frame_1, drag_gauss_wf);",
            "}",
            "foo(-0.2) q[0];",
            "b[0] = measure q[0];",
        ]),
        inputs={},
    )

    assert (
        circ.to_ir(
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
            gate_definitions=gate_calibrations.pulse_sequences,
        )
        == expected_ir
    )


@pytest.mark.parametrize(
    "expected_circuit, ir",
    [
        (
            Circuit().h(0, control=1, control_state=0).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "negctrl @ h q[1], q[0];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().cnot(target=0, control=1).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "cnot q[1], q[0];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().x(0, control=[1], control_state=[0]).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "negctrl @ x q[1], q[0];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().rx(0, 0.15, control=1, control_state=1).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "ctrl @ rx(0.15) q[1], q[0];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().ry(0, 0.2, control=1, control_state=1).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "ctrl @ ry(0.2) q[1], q[0];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().rz(0, 0.25, control=[1], control_state=[0]).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "negctrl @ rz(0.25) q[1], q[0];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().s(target=0, control=[1], control_state=[0]).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "negctrl @ s q[1], q[0];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().t(target=1, control=[0], control_state=[0]).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "negctrl @ t q[0], q[1];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().cphaseshift(target=0, control=1, angle=0.15).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "cphaseshift(0.15) q[1], q[0];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().ccnot(*[0, 1], target=2).measure(0).measure(1).measure(2),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[3] b;",
                    "qubit[3] q;",
                    "ccnot q[0], q[1], q[2];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                    "b[2] = measure q[2];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).state_vector(),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "qubit[1] q;",
                    "h q[0];",
                    "#pragma braket result state_vector",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).expectation(observables.X(), [0]),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "qubit[1] q;",
                    "h q[0];",
                    "#pragma braket result expectation x(q[0])",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).expectation(observables.H() @ observables.X(), [0, 1]),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "qubit[2] q;",
                    "h q[0];",
                    "#pragma braket result expectation h(q[0]) @ x(q[1])",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).variance(observables.H() @ observables.X(), [0, 1]),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "qubit[2] q;",
                    "h q[0];",
                    "#pragma braket result variance h(q[0]) @ x(q[1])",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).probability(target=[0]),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "qubit[1] q;",
                    "h q[0];",
                    "#pragma braket result probability q[0]",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().bit_flip(0, 0.1).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "#pragma braket noise bit_flip(0.1) q[0]",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().generalized_amplitude_damping(0, 0.1, 0.1).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "#pragma braket noise generalized_amplitude_damping(0.1, 0.1) q[0]",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().phase_flip(0, 0.2).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "#pragma braket noise phase_flip(0.2) q[0]",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().depolarizing(0, 0.5).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "#pragma braket noise depolarizing(0.5) q[0]",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().amplitude_damping(0, 0.8).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "#pragma braket noise amplitude_damping(0.8) q[0]",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().phase_damping(0, 0.1).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "#pragma braket noise phase_damping(0.1) q[0]",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).amplitude(state=["0", "1"]),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "qubit[1] q;",
                    "h q[0];",
                    '#pragma braket result amplitude "0", "1"',
                ]),
                inputs={},
            ),
        ),
        (
            Circuit()
            .rx(0, 0.15, control=2, control_state=0)
            .rx(1, 0.3, control=[2, 3])
            .cnot(target=0, control=[2, 3, 4])
            .measure(0)
            .measure(1)
            .measure(2)
            .measure(3)
            .measure(4),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[5] b;",
                    "qubit[5] q;",
                    "negctrl @ rx(0.15) q[2], q[0];",
                    "ctrl(2) @ rx(0.3) q[2], q[3], q[1];",
                    "ctrl(2) @ cnot q[2], q[3], q[4], q[0];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                    "b[2] = measure q[2];",
                    "b[3] = measure q[3];",
                    "b[4] = measure q[4];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit()
            .cnot(0, 1)
            .cnot(target=2, control=3)
            .cnot(target=4, control=[5, 6])
            .measure(0)
            .measure(1)
            .measure(2)
            .measure(3)
            .measure(4)
            .measure(5)
            .measure(6),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[7] b;",
                    "qubit[7] q;",
                    "cnot q[0], q[1];",
                    "cnot q[3], q[2];",
                    "ctrl @ cnot q[5], q[6], q[4];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                    "b[2] = measure q[2];",
                    "b[3] = measure q[3];",
                    "b[4] = measure q[4];",
                    "b[5] = measure q[5];",
                    "b[6] = measure q[6];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0, power=-2.5).h(0, power=0).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "inv @ pow(2.5) @ h q[0];",
                    "pow(0) @ h q[0];",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().unitary(matrix=np.array([[0, 1], [1, 0]]), targets=[0]).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "#pragma braket unitary([[0, 1.0], [1.0, 0]]) q[0]",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().pauli_channel(0, probX=0.1, probY=0.2, probZ=0.3).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "#pragma braket noise pauli_channel(0.1, 0.2, 0.3) q[0]",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().two_qubit_depolarizing(0, 1, probability=0.1).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "#pragma braket noise two_qubit_depolarizing(0.1) q[0], q[1]",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().two_qubit_dephasing(0, 1, probability=0.1).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "#pragma braket noise two_qubit_dephasing(0.1) q[0], q[1]",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().two_qubit_dephasing(0, 1, probability=0.1).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "#pragma braket noise two_qubit_dephasing(0.1) q[0], q[1]",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).sample(observable=Observable.Z(), target=0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "qubit[1] q;",
                    "h q[0];",
                    "#pragma braket result sample z(q[0])",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).sample(observable=Observable.Z(), target=0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "qubit[1] q;",
                    "h q[0];",
                    "#pragma braket result sample z(q[0])",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).x(1).density_matrix(target=[0, 1]),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "qubit[2] q;",
                    "h q[0];",
                    "x q[1];",
                    "#pragma braket result density_matrix q[0], q[1]",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit()
            .kraus(
                [0],
                matrices=[
                    np.array([[0.9486833j, 0], [0, 0.9486833j]]),
                    np.array([[0, 0.31622777], [0.31622777, 0]]),
                ],
            )
            .measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "#pragma braket noise "
                    "kraus([[0.9486833im, 0], [0, 0.9486833im]], [[0, 0.31622777], "
                    "[0.31622777, 0]]) q[0]",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().rx(0, FreeParameter("theta")).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "input float theta;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "rx(theta) q[0];",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().rx(0, np.pi).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "rx(π) q[0];",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().rx(0, 2 * np.pi).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "rx(τ) q[0];",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().gphase(0.15).x(0).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "gphase(0.15);",
                    "x q[0];",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
    ],
)
def test_from_ir(expected_circuit, ir):
    assert Circuit.from_ir(source=ir.source, inputs=ir.inputs) == expected_circuit
    assert Circuit.from_ir(source=ir) == expected_circuit


def test_from_ir_inputs_updated():
    circuit = Circuit().rx(0, 0.2).ry(0, 0.1).measure(0)
    openqasm = OpenQasmProgram(
        source="\n".join([
            "OPENQASM 3.0;",
            "input float theta;",
            "input float phi;",
            "bit[1] b;",
            "qubit[1] q;",
            "rx(theta) q[0];",
            "ry(phi) q[0];",
            "b[0] = measure q[0];",
        ]),
        inputs={"theta": 0.2, "phi": 0.3},
    )
    assert Circuit.from_ir(source=openqasm, inputs={"phi": 0.1}) == circuit


@pytest.mark.parametrize(
    "expected_circuit, ir",
    [
        (
            Circuit().h(0).cnot(0, 1).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "gate my_gate a,b {",
                    "h a;",
                    "cnot a,b;",
                    "}",
                    "my_gate q[0], q[1];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).h(1).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "def my_sub(qubit q) {",
                    "h q;",
                    "}",
                    "h q[0];",
                    "my_sub(q[1]);",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).h(1).cnot(0, 1).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "for uint i in [0:1] {",
                    "h q[i];",
                    "}",
                    "cnot q[0], q[1];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().h(0).h(1).cnot(0, 1).measure(0).measure(1),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[2] b;",
                    "qubit[2] q;",
                    "for uint i in [0:1] {",
                    "h q[i];",
                    "}",
                    "cnot q[0], q[1];",
                    "b[0] = measure q[0];",
                    "b[1] = measure q[1];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().x(0).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "bit c = 0;",
                    "if (c ==0){",
                    "x q[0];",
                    "}",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
        (
            Circuit().rx(0, FreeParameter("theta")).rx(0, 2 * FreeParameter("theta")).measure(0),
            OpenQasmProgram(
                source="\n".join([
                    "OPENQASM 3.0;",
                    "input float theta;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "rx(theta) q[0];",
                    "rx(2*theta) q[0];",
                    "b[0] = measure q[0];",
                ]),
                inputs={},
            ),
        ),
    ],
)
def test_from_ir_advanced_openqasm(expected_circuit, ir):
    circuit_from_ir = Circuit.from_ir(source=ir.source, inputs=ir.inputs)

    assert circuit_from_ir == expected_circuit


def test_braket_result_to_result_type_raises_type_error():
    with pytest.raises(TypeError, match="Result type str is not supported"):
        braket_result_to_result_type("type error test")


@pytest.mark.parametrize(
    "ir_type, serialization_properties, expected_exception, expected_message",
    [
        (
            "invalid-ir-type",
            OpenQASMSerializationProperties(QubitReferenceType.VIRTUAL),
            ValueError,
            "Supplied ir_type invalid-ir-type is not supported.",
        ),
        (
            IRType.OPENQASM,
            OpenQASMSerializationProperties("invalid-qubit-reference-type"),
            ValueError,
            "Invalid qubit_reference_type invalid-qubit-reference-type supplied.",
        ),
        (
            IRType.OPENQASM,
            "invalid-serialization-properties",
            ValueError,
            "serialization_properties must be of type OpenQASMSerializationProperties "
            "for IRType.OPENQASM.",
        ),
    ],
)
def test_circuit_to_ir_invalid_inputs(
    ir_type, serialization_properties, expected_exception, expected_message
):
    circuit = Circuit().h(0).cnot(0, 1)
    with pytest.raises(expected_exception) as exc:
        circuit.to_ir(ir_type, serialization_properties=serialization_properties)
    assert exc.value.args[0] == expected_message


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
def test_to_unitary_noise_raises_error(circuit):
    with pytest.raises(TypeError):
        circuit.to_unitary()


def test_to_unitary_parameterized():
    theta = FreeParameter("theta")
    circ = Circuit().rx(angle=theta, target=0)
    with pytest.raises(TypeError):
        np.allclose(circ.to_unitary())


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


def test_to_unitary_with_compiler_directives_returns_expected_unitary():
    circuit = Circuit().add_verbatim_box(Circuit().cphaseshift(1, 2, 0.15).si(3))
    assert np.allclose(
        circuit.to_unitary(),
        np.kron(gates.CPhaseShift(0.15).to_matrix(), gates.Si().to_matrix()),
    )


def test_to_unitary_with_global_phase():
    circuit = Circuit().x(0)
    circuit_unitary = np.array([[0, 1], [1, 0]])
    assert np.allclose(circuit.to_unitary(), circuit_unitary)
    circuit = circuit.gphase(np.pi / 2)
    assert np.allclose(circuit.to_unitary(), 1j * circuit_unitary)


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
        (Circuit().u(0, 0.15, 0.16, 0.17), gates.U(0.15, 0.16, 0.17).to_matrix()),
        (Circuit().gphase(0.15), gates.GPhase(0.15).to_matrix()),
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
        (Circuit().prx(0, 1, 0.15), gates.PRx(1, 0.15).to_matrix()),
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
            Circuit().x(0, control=1),
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
            Circuit().x(1, control=0, power=0.5),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 0.5 + 0.5j, 0.5 - 0.5j],
                    [0.0, 0.0, 0.5 - 0.5j, 0.5 + 0.5j],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().x(1, control=0, power=2),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
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


def test_depth_setter(h):
    with pytest.raises(AttributeError):
        h.depth = 1


def test_instructions_getter(h):
    assert h.instructions == list(h._moments.values())


def test_instructions_setter(h, h_instr):
    with pytest.raises(AttributeError):
        h.instructions = [h_instr]


def test_moments_getter(h):
    assert h.moments is h._moments


def test_moments_setter(h):
    with pytest.raises(AttributeError):
        h.moments = Moments()


def test_qubit_count_getter(h):
    assert h.qubit_count is h._moments.qubit_count


def test_qubit_count_setter(h):
    with pytest.raises(AttributeError):
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


def test_qubits_setter(h):
    with pytest.raises(AttributeError):
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
    expected = {theta}
    assert circ.parameters == expected


def test_add_parameterized_instr_parameterized_circ_check_true():
    theta = FreeParameter("theta")
    alpha = FreeParameter("alpha")
    alpha2 = FreeParameter("alpha")
    circ = Circuit().ry(angle=theta, target=0).ry(angle=alpha2, target=1).ry(angle=theta, target=2)
    circ.add_instruction(Instruction(Gate.Ry(alpha), 3))
    expected = {theta, alpha}
    assert circ.parameters == expected


def test_add_non_parameterized_instr_parameterized_check_true():
    theta = FreeParameter("theta")
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=theta, target=2)
    circ.add_instruction(Instruction(Gate.Ry(0.1), 3))
    expected = {theta}
    assert circ.parameters == expected


def test_add_circ_parameterized_check_true():
    theta = FreeParameter("theta")
    circ = Circuit().ry(angle=1, target=0).add_circuit(Circuit().ry(angle=theta, target=0))

    expected = {theta}
    assert circ.parameters == expected


def test_add_circ_not_parameterized_check_true():
    theta = FreeParameter("theta")
    circ = Circuit().ry(angle=theta, target=0).add_circuit(Circuit().ry(angle=0.1, target=0))

    expected = {theta}
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
    expected = {theta}
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
    expected_parameters = {alpha}
    assert circ_new == expected_circ and circ_new.parameters == expected_parameters


def test_make_bound_circuit_non_existent_param():
    theta = FreeParameter("theta")
    input_val = np.pi
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=theta, target=2)
    with pytest.raises(ValueError):
        circ.make_bound_circuit({"alpha": input_val}, strict=True)


def test_make_bound_circuit_bad_value():
    theta = FreeParameter("theta")
    input_val = "invalid"
    circ = Circuit().ry(angle=theta, target=0).ry(angle=theta, target=1).ry(angle=theta, target=2)
    with pytest.raises(TypeError):
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


def test_pulse_circuit_to_openqasm(predefined_frame_1, user_defined_frame):
    pulse_sequence_1 = (
        PulseSequence()
        .set_frequency(predefined_frame_1, 3e9)
        .play(predefined_frame_1, GaussianWaveform(length=1e-3, sigma=0.7, id="gauss_wf"))
        .play(
            predefined_frame_1,
            DragGaussianWaveform(length=3e-3, sigma=0.4, beta=0.2, id="drag_gauss_wf"),
        )
    )

    pulse_sequence_2 = (
        PulseSequence()
        .set_frequency(predefined_frame_1, 3e9)
        .play(user_defined_frame, GaussianWaveform(length=1e-3, sigma=0.7, id="gauss_wf"))
        .play(
            predefined_frame_1,
            DragGaussianWaveform(length=3e-3, sigma=0.4, beta=0.2, id="drag_gauss_wf_2"),
        )
    )

    circuit = (
        Circuit().h(0).pulse_gate(0, pulse_sequence_1).x(1).pulse_gate(1, pulse_sequence_2).h(1)
    )

    pulse_sequence_2.play(
        user_defined_frame, GaussianWaveform(length=1e-3, sigma=0.7, id="gauss_wf_ignore")
    )

    assert circuit.to_ir(
        ir_type=IRType.OPENQASM,
        serialization_properties=OpenQASMSerializationProperties(
            qubit_reference_type=QubitReferenceType.PHYSICAL
        ),
    ).source == "\n".join([
        "OPENQASM 3.0;",
        "bit[2] b;",
        "cal {",
        "    frame user_defined_frame_0 = newframe(device_port_x0, 10000000.0, 3.14);",
        "    waveform gauss_wf = gaussian(1.0ms, 700.0ms, 1, false);",
        "    waveform drag_gauss_wf = drag_gaussian(3.0ms, 400.0ms, 0.2, 1, false);",
        "    waveform drag_gauss_wf_2 = drag_gaussian(3.0ms, 400.0ms, 0.2, 1, false);",
        "}",
        "h $0;",
        "cal {",
        "    set_frequency(predefined_frame_1, 3000000000.0);",
        "    play(predefined_frame_1, gauss_wf);",
        "    play(predefined_frame_1, drag_gauss_wf);",
        "}",
        "x $1;",
        "cal {",
        "    set_frequency(predefined_frame_1, 3000000000.0);",
        "    play(user_defined_frame_0, gauss_wf);",
        "    play(predefined_frame_1, drag_gauss_wf_2);",
        "}",
        "h $1;",
        "b[0] = measure $0;",
        "b[1] = measure $1;",
    ])


def test_pulse_circuit_conflicting_wf(predefined_frame_1, user_defined_frame):
    pulse_sequence_1 = (
        PulseSequence()
        .set_frequency(predefined_frame_1, 3e9)
        .play(predefined_frame_1, GaussianWaveform(length=1e-3, sigma=0.7, id="gauss_wf"))
    )

    pulse_sequence_2 = (
        PulseSequence()
        .set_frequency(predefined_frame_1, 3e9)
        .play(user_defined_frame, GaussianWaveform(length=1e-3, sigma=0.3, id="gauss_wf"))
    )

    circuit = (
        Circuit().h(0).pulse_gate(0, pulse_sequence_1).x(1).pulse_gate(1, pulse_sequence_2).h(1)
    )

    with pytest.raises(ValueError):
        circuit.to_ir(
            ir_type=IRType.OPENQASM,
            serialization_properties=OpenQASMSerializationProperties(
                qubit_reference_type=QubitReferenceType.PHYSICAL
            ),
        )


def test_pulse_circuit_conflicting_frame(user_defined_frame):
    user_defined_frame_x = Frame(
        user_defined_frame.id,
        Port("wrong_port", 1e-9),
        user_defined_frame.frequency,
        user_defined_frame.phase,
    )
    pulse_sequence_user_defined_frame_x = (
        PulseSequence()
        .set_frequency(user_defined_frame_x, 3e9)
        .play(user_defined_frame_x, GaussianWaveform(length=1e-3, sigma=0.7, id="gauss_wf"))
    )

    pulse_sequence_user_defined_frame = (
        PulseSequence()
        .set_frequency(user_defined_frame, 3e9)
        .play(user_defined_frame, GaussianWaveform(length=1e-3, sigma=0.7, id="gauss_wf"))
    )

    circuit = (
        Circuit()
        .h(0)
        .pulse_gate(0, pulse_sequence_user_defined_frame)
        .x(1)
        .pulse_gate(1, pulse_sequence_user_defined_frame_x)
        .h(1)
    )

    with pytest.raises(ValueError):
        circuit.to_ir(
            ir_type=IRType.OPENQASM,
            serialization_properties=OpenQASMSerializationProperties(
                qubit_reference_type=QubitReferenceType.PHYSICAL
            ),
        )


def test_parametrized_pulse_circuit(user_defined_frame):
    frequency_parameter = FreeParameter("frequency")
    length = FreeParameter("length")
    theta = FreeParameter("theta")
    pulse_sequence = (
        PulseSequence()
        .set_frequency(user_defined_frame, frequency_parameter)
        .play(user_defined_frame, GaussianWaveform(length=length, sigma=0.7, id="gauss_wf"))
    )

    circuit = (
        Circuit().rx(angle=theta, target=0).pulse_gate(pulse_sequence=pulse_sequence, targets=1)
    )

    assert circuit.parameters == {frequency_parameter, length, theta}

    bound_half = circuit(theta=0.5, length=1e-5)
    assert bound_half.to_ir(
        ir_type=IRType.OPENQASM,
        serialization_properties=OpenQASMSerializationProperties(
            qubit_reference_type=QubitReferenceType.PHYSICAL
        ),
    ).source == "\n".join([
        "OPENQASM 3.0;",
        "input float frequency;",
        "bit[2] b;",
        "cal {",
        "    frame user_defined_frame_0 = newframe(device_port_x0, 10000000.0, 3.14);",
        "    waveform gauss_wf = gaussian(10.0us, 700.0ms, 1, false);",
        "}",
        "rx(0.5) $0;",
        "cal {",
        "    set_frequency(user_defined_frame_0, frequency);",
        "    play(user_defined_frame_0, gauss_wf);",
        "}",
        "b[0] = measure $0;",
        "b[1] = measure $1;",
    ])

    bound = bound_half(frequency=1e7)

    assert bound.to_ir(
        ir_type=IRType.OPENQASM,
        serialization_properties=OpenQASMSerializationProperties(
            qubit_reference_type=QubitReferenceType.PHYSICAL
        ),
    ).source == "\n".join([
        "OPENQASM 3.0;",
        "bit[2] b;",
        "cal {",
        "    frame user_defined_frame_0 = newframe(device_port_x0, 10000000.0, 3.14);",
        "    waveform gauss_wf = gaussian(10.0us, 700.0ms, 1, false);",
        "}",
        "rx(0.5) $0;",
        "cal {",
        "    set_frequency(user_defined_frame_0, 10000000.0);",
        "    play(user_defined_frame_0, gauss_wf);",
        "}",
        "b[0] = measure $0;",
        "b[1] = measure $1;",
    ])


def test_free_param_float_mix():
    Circuit().ms(0, 1, 0.1, FreeParameter("theta"))


def test_circuit_with_global_phase():
    circuit = Circuit().gphase(0.15).x(0)
    assert circuit.global_phase == 0.15

    assert circuit.to_ir(
        ir_type=IRType.OPENQASM,
        serialization_properties=OpenQASMSerializationProperties(
            qubit_reference_type=QubitReferenceType.PHYSICAL
        ),
    ).source == "\n".join([
        "OPENQASM 3.0;",
        "bit[1] b;",
        "gphase(0.15);",
        "x $0;",
        "b[0] = measure $0;",
    ])


def test_from_ir_round_trip_transformation_with_targeted_measurements():
    circuit = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .add_instruction(Instruction(Measure(index=2), 1))
        .add_instruction(Instruction(Measure(index=1), 2))
        .add_instruction(Instruction(Measure(index=0), 0))
    )
    ir = OpenQasmProgram(
        source="\n".join([
            "OPENQASM 3.0;",
            "bit[3] b;",
            "qubit[3] q;",
            "h q[0];",
            "cnot q[0], q[1];",
            "b[2] = measure q[1];",
            "b[1] = measure q[2];",
            "b[0] = measure q[0];",
        ]),
        inputs={},
    )

    assert Circuit.from_ir(ir) == Circuit.from_ir(circuit.to_ir("OPENQASM"))
    assert circuit.to_ir("OPENQASM") == Circuit.from_ir(ir).to_ir("OPENQASM")
