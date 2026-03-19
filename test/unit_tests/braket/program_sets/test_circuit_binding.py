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
from braket.parametric import FreeParameter
from braket.program_sets import CircuitBinding
from braket.quantum_information import PauliString


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
