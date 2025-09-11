# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import re
from braket.circuits import Circuit, Observable
from braket.circuits.observables import X, Y, Z, H, I
from braket.device_schema.result_type import ResultType
from braket.emulation.passes.circuit_passes.result_type_validator import ResultTypeValidator


@pytest.fixture
def supported_result_types():
    names = ["Sample", "Expectation", "Variance", "Probability"]
    observables = ["x", "y", "z", "h", "i"]
    return [ResultType(name=name, observables=observables) for name in names]


@pytest.fixture
def connectivity_graph():
    # Create a simple connectivity graph for a 2-qubit device
    return {"0": ["1"], "1": ["0"]}


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit(),
        Circuit().h(0).cnot(0, 1).probability(),
        Circuit().h(0).cnot(0, 1).expectation(observable=Z(), target=0),
        Circuit().h(0).cnot(0, 1).sample(observable=X(), target=0),
        Circuit().h(0).cnot(0, 1).variance(observable=Z(), target=0),
        Circuit().h(0).cnot(0, 1).expectation(observable=Z(), target=0).probability(),
        Circuit().h(0).cnot(0, 1).sample(observable=Y(), target=1).probability(target=[0]),
        Circuit().h(0).cnot(0, 1).variance(observable=H(), target=0),
        Circuit().h(0).cnot(0, 1).expectation(observable=I(), target=0),
    ],
)
def test_valid_circuits(supported_result_types, connectivity_graph, circuit):
    """
    ResultTypeValidator should not raise any errors when validating these circuits.
    """
    ResultTypeValidator(supported_result_types, connectivity_graph).validate(circuit)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit().h(0).cnot(0, 1).state_vector(),
        Circuit().h(0).cnot(0, 1).probability().state_vector(),
        Circuit().h(0).cnot(0, 1).expectation(observable=Z(), target=0).state_vector(),
        Circuit().h(0).cnot(0, 1).density_matrix(),
        Circuit().h(0).cnot(0, 1).amplitude(state=["00", "11"]),
    ],
)
def test_invalid_circuits(supported_result_types, connectivity_graph, circuit):
    """
    ResultTypeValidator should raise errors when validating these circuits.
    """
    with pytest.raises(ValueError):
        ResultTypeValidator(supported_result_types, connectivity_graph).validate(circuit)


def test_invalid_instantiation():
    with pytest.raises(ValueError, match="Supported result types must be provided."):
        ResultTypeValidator([], {"0": ["1"]})

    with pytest.raises(ValueError, match="Connectivity graph must be provided."):
        ResultTypeValidator(["Expectation"], None)


def test_invalid_qubit_target():
    """
    Test that ResultTypeValidator raises an error when a result type targets a qubit
    that is not in the device's connectivity graph.
    """
    # Create a connectivity graph for a 1-qubit device
    connectivity_graph = {"0": []}

    # Create a circuit with a result type targeting qubit 1, which is not in the device
    circuit = Circuit().h(0).expectation(observable=Z(), target=1)

    # The validator should raise an error because qubit 1 is not in the device
    with pytest.raises(
        ValueError,
        match="Qubit 1 in result type Expectation is not a valid qubit for this device. The set of valid qubits can be found in the connectivity graph of the device.",
    ):
        ResultTypeValidator(
            [ResultType(name="Expectation", observables=["x", "y", "z", "h", "i"])],
            connectivity_graph,
        ).validate(circuit)


def test_observables(supported_result_types, connectivity_graph):
    circuit = Circuit().h(0).cnot(0, 1).sample(Observable.Z(0) @ Observable.Z(1))
    observable_name = circuit.result_types[0].observable.name.lower()
    error_messasge = re.escape(
        f"Observable {observable_name} is not supported for result type Sample on this device. "
        f"Supported observables are: ['x', 'y', 'z', 'h', 'i']."
    )
    with pytest.raises(
        ValueError,
        match=error_messasge,
    ):
        ResultTypeValidator(supported_result_types, connectivity_graph).validate(circuit)
