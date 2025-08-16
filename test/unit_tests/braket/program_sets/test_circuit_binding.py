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
from braket.program_sets import CircuitBinding


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
            Circuit(circuit_rx_parametrized).expectation(X(0)), input_sets={"theta": [1.23, 3.21]}
        )


def test_sum_in_observable_list():
    with pytest.raises(TypeError):
        CircuitBinding(Circuit().h(0), observables=[X(0) + Y(0)])
