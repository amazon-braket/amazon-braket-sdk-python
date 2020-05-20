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

DEVICE = LocalSimulator()
SHOTS = 750


def test_bell_pair():
    bell = Circuit().h(0).cnot(0, 1)
    result = DEVICE.run(bell, shots=SHOTS).result()

    assert 0.40 < result.measurement_probabilities["00"] < 0.60
    assert 0.40 < result.measurement_probabilities["11"] < 0.60
    assert len(result.measurements) == SHOTS


def test_qubit_ordering():
    # |110> should get back value of "110"
    state_110 = Circuit().x(0).x(1).i(2)
    result = DEVICE.run(state_110, shots=SHOTS).result()
    assert result.measurement_counts.most_common(1)[0][0] == "110"

    # |001> should get back value of "001"
    state_001 = Circuit().i(0).i(1).x(2)
    result = DEVICE.run(state_001, shots=SHOTS).result()
    assert result.measurement_counts.most_common(1)[0][0] == "001"


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


def test_result_types_nonzero_shots():
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
