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

from braket.circuits import Circuit, Observable, observables
from braket.circuits.circuit_helpers import validate_circuit_and_shots


def test_validate_circuit_and_shots_no_instructions():
    with pytest.raises(ValueError, match="Circuit must have instructions to run on a device"):
        validate_circuit_and_shots(Circuit(), 100)


def test_validate_circuit_and_shots_only_gphase():
    with pytest.raises(
        ValueError, match="Circuit must have at least one non-GPhase gate to run on a device"
    ):
        validate_circuit_and_shots(Circuit().gphase(0.15), 100)


def test_validate_circuit_and_shots_ctrl_gphase():
    assert validate_circuit_and_shots(Circuit().gphase(0.15, control=[0]), 100) is None


def test_validate_circuit_and_shots_0_no_instructions():
    with pytest.raises(ValueError, match="Circuit must have instructions to run on a device"):
        validate_circuit_and_shots(Circuit(), 0)


def test_validate_circuit_and_shots_0_no_results():
    with pytest.raises(ValueError, match="No result types specified for circuit and shots=0."):
        validate_circuit_and_shots(Circuit().h(0), 0)


def test_validate_circuit_and_shots_100_no_results():
    assert validate_circuit_and_shots(Circuit().h(0), 100) is None


def test_validate_circuit_and_shots_0_results():
    assert validate_circuit_and_shots(Circuit().h(0).state_vector(), 0) is None


def test_validate_circuit_and_shots_100_results():
    assert validate_circuit_and_shots(Circuit().h(0).probability(), 100) is None


def test_validate_circuit_and_shots_100_results_mixed_result():
    assert (
        validate_circuit_and_shots(
            Circuit().h(0).expectation(observable=Observable.Z(), target=0), 100
        )
        is None
    )


def test_validate_circuit_and_shots_100_result_state_vector():
    with pytest.raises(
        ValueError, match="StateVector or Amplitude cannot be specified when shots>0"
    ):
        validate_circuit_and_shots(Circuit().h(0).state_vector(), 100)


def test_validate_circuit_and_shots_100_result_amplitude():
    with pytest.raises(
        ValueError, match="StateVector or Amplitude cannot be specified when shots>0"
    ):
        validate_circuit_and_shots(Circuit().h(0).amplitude(state=["0"]), 100)


def test_validate_circuit_and_shots_0_noncommuting():
    validate_circuit_and_shots(
        Circuit()
        .h(0)
        .expectation(observables.X() @ observables.Y(), [0, 1])
        .expectation(observables.Y() @ observables.X(), [0, 1]),
        0,
    )


def test_validate_circuit_and_shots_100_noncommuting():
    with pytest.raises(ValueError, match="Observables cannot be sampled simultaneously"):
        validate_circuit_and_shots(
            Circuit()
            .h(0)
            .expectation(observables.X() @ observables.Y(), [0, 1])
            .expectation(observables.Y() @ observables.X(), [0, 1]),
            100,
        )


def test_probability_limit():
    circ = Circuit()
    for i in range(50):
        circ.h(i)
    circ.probability()

    too_many_qubits = "Probability target must be less than or equal to 40 qubits."
    with pytest.raises(ValueError, match=too_many_qubits):
        validate_circuit_and_shots(circ, 100)
