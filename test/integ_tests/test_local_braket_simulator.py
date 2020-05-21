# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import numpy as np
from braket.circuits import Circuit, Observable
from braket.circuits.result_types import Expectation, Sample, StateVector
from braket.devices import LocalSimulator
from simulator_assert_utils import (
    assert_measurement_counts_most_common,
    assert_measurement_probabilities,
)

DEVICE = LocalSimulator()
SHOTS = 750


def test_bell_pair(bell_state_and_tolerances):
    result = DEVICE.run(bell_state_and_tolerances[0], shots=SHOTS).result()
    assert_measurement_probabilities(result.measurement_probabilities, bell_state_and_tolerances[1])
    assert len(result.measurements) == SHOTS


def test_qubit_ordering(state_110_and_most_common, state_001_and_most_common):
    # |110> should get back value of "110"
    result = DEVICE.run(state_110_and_most_common[0], shots=SHOTS).result()
    assert_measurement_counts_most_common(result.measurement_counts, state_110_and_most_common[1])

    # |001> should get back value of "001"
    result = DEVICE.run(state_001_and_most_common[0], shots=SHOTS).result()
    assert_measurement_counts_most_common(result.measurement_counts, state_001_and_most_common[1])


def test_result_types_no_shots():
    circuit = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .expectation(observable=Observable.H() @ Observable.X(), target=[0, 1])
        .state_vector()
    )
    result = DEVICE.run(circuit).result()
    assert len(result.result_types) == 2
    assert np.allclose(
        result.get_value_by_result_type(
            Expectation(observable=Observable.H() @ Observable.X(), target=[0, 1])
        ),
        1 / np.sqrt(2),
    )
    assert np.allclose(
        result.get_value_by_result_type(StateVector()), np.array([1, 0, 0, 1]) / np.sqrt(2)
    )


def test_result_types_nonzero_shots_expectation():
    circuit_expectation = (
        Circuit()
        .h(0)
        .cnot(0, 1)
        .expectation(observable=Observable.H() @ Observable.X(), target=[0, 1])
    )
    result_expectation = DEVICE.run(circuit_expectation, shots=SHOTS).result()
    assert len(result_expectation.result_types) == 1
    assert (
        0.6
        < result_expectation.get_value_by_result_type(
            Expectation(observable=Observable.H() @ Observable.X(), target=[0, 1])
        )
        < 0.8
    )


def test_result_types_nonzero_shots_sample():
    circuit_sample = (
        Circuit().h(0).cnot(0, 1).sample(observable=Observable.H() @ Observable.X(), target=[0, 1])
    )
    result_sample = DEVICE.run(circuit_sample, shots=SHOTS).result()
    assert len(result_sample.result_types) == 1
    assert (
        len(
            result_sample.get_value_by_result_type(
                Sample(observable=Observable.H() @ Observable.X(), target=[0, 1])
            )
        )
        == SHOTS
    )
