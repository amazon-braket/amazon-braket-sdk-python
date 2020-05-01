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

import pytest
from braket.circuits import Circuit
from braket.circuits.circuit_helpers import validate_circuit_and_shots


@pytest.mark.xfail(raises=ValueError)
def test_validate_circuit_and_shots_0_no_results():
    validate_circuit_and_shots(Circuit().h(0), 0)


def test_validate_circuit_and_shots_100_no_results():
    assert validate_circuit_and_shots(Circuit().h(0), 100) is None


def test_validate_circuit_and_shots_0_results():
    assert validate_circuit_and_shots(Circuit().h(0).state_vector(), 0) is None


def test_validate_circuit_and_shots_100_results():
    assert validate_circuit_and_shots(Circuit().h(0).probability(), 100) is None


@pytest.mark.xfail(raises=ValueError)
def test_validate_circuit_and_shots_100_result_state_vector():
    validate_circuit_and_shots(Circuit().h(0).state_vector(), 100)


@pytest.mark.xfail(raises=ValueError)
def test_validate_circuit_and_shots_100_result_amplitude():
    validate_circuit_and_shots(Circuit().h(0).amplitude(state=["0"]), 100)
