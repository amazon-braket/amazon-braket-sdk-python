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

import json
from decimal import Decimal
from unittest.mock import Mock

import pytest

from braket.ahs.analog_hamiltonian_simulation import (
    AnalogHamiltonianSimulation,
    AtomArrangement,
    DiscretizationError,
    DrivingField,
    ShiftingField,
    SiteType,
)
from braket.ahs.field import Field
from braket.ahs.pattern import Pattern
from braket.ahs.time_series import TimeSeries
from braket.ir.ahs.program_v1 import Program


@pytest.fixture
def register():
    return (
        AtomArrangement()
        .add((0.0, 0.0))
        .add((0.0, 3.0e-6))
        .add((0.0, 6.0e-6))
        .add((3.0e-6, 0.0))
        .add((3.0e-6, 3.0e-6))
        .add((3.0e-6, 3.0e-6), SiteType.VACANT)
        .add((3.0e-6, 6.0e-6), SiteType.VACANT)
    )


@pytest.fixture
def driving_field():
    return DrivingField(
        TimeSeries().put(0.0, 0.0).put(3.0e-7, 2.51327e7).put(2.7e-6, 2.51327e7).put(3.0e-6, 0.0),
        TimeSeries().put(0.0, 0).put(3.0e-6, 0),
        TimeSeries()
        .put(0.0, -1.25664e8)
        .put(3.0e-7, -1.25664e8)
        .put(2.7e-6, 1.25664e8)
        .put(3.0e-6, 1.25664e8),
    )


@pytest.fixture
def shifting_field():
    return ShiftingField(
        Field(
            TimeSeries().put(0.0, -1.25664e8).put(3.0e-6, 1.25664e8),
            Pattern([0.5, 1.0, 0.5, 0.5, 0.5, 0.5]),
        )
    )


def test_create():
    mock0 = Mock()
    mock1 = Mock()
    ahs = AnalogHamiltonianSimulation(register=mock0, hamiltonian=mock1)
    assert mock0 == ahs.register
    assert mock1 == ahs.hamiltonian


def test_to_ir(register, driving_field, shifting_field):
    hamiltonian = driving_field + shifting_field
    ahs = AnalogHamiltonianSimulation(register=register, hamiltonian=hamiltonian)
    problem = ahs.to_ir()
    assert Program.parse_raw(problem.json()) == problem
    assert problem == Program.parse_raw_schema(problem.json())


def test_to_ir_empty():
    hamiltonian = Mock()
    hamiltonian.terms = []
    ahs = AnalogHamiltonianSimulation(register=AtomArrangement(), hamiltonian=hamiltonian)
    problem = ahs.to_ir()
    assert Program.parse_raw(problem.json()) == problem
    assert problem == Program.parse_raw_schema(problem.json())


@pytest.mark.xfail(raises=TypeError)
def test_to_ir_invalid_hamiltonian(register):
    hamiltonian = Mock()
    hamiltonian.terms = [Mock()]
    ahs = AnalogHamiltonianSimulation(register=register, hamiltonian=hamiltonian)
    ahs.to_ir()


@pytest.mark.xfail(raises=DiscretizationError)
def test_invalid_action():
    action = Mock()
    action.actionType = "not-a-valid-AHS-action"
    device = Mock()
    device.properties.action = {"braket.ir.ahs.program": action}

    AnalogHamiltonianSimulation(register=Mock(), hamiltonian=Mock()).discretize(device)


@pytest.mark.xfail(raises=DiscretizationError)
def test_invalid_action_name():
    action = Mock()
    action.actionType = "braket.ir.ahs.program"
    device = Mock()
    device.properties.action = {"not-a-valid-AHS-action": action}

    AnalogHamiltonianSimulation(register=Mock(), hamiltonian=Mock()).discretize(device)


def test_discretize(register, driving_field, shifting_field):
    hamiltonian = driving_field + shifting_field
    ahs = AnalogHamiltonianSimulation(register=register, hamiltonian=hamiltonian)

    action = Mock()
    action.actionType = "braket.ir.ahs.program"

    device = Mock()
    device.properties.action = {"braket.ir.ahs.program": action}

    device.properties.paradigm.lattice.geometry.positionResolution = Decimal("1E-7")

    device.properties.paradigm.rydberg.rydbergGlobal.timeResolution = Decimal("1E-9")
    device.properties.paradigm.rydberg.rydbergGlobal.rabiFrequencyResolution = Decimal("400")
    device.properties.paradigm.rydberg.rydbergGlobal.detuningResolution = Decimal("0.2")
    device.properties.paradigm.rydberg.rydbergGlobal.phaseResolution = Decimal("5E-7")

    device.properties.paradigm.rydberg.rydbergLocal.timeResolution = Decimal("1E-9")
    device.properties.paradigm.rydberg.rydbergLocal.commonDetuningResolution = Decimal("2000.0")
    device.properties.paradigm.rydberg.rydbergLocal.localDetuningResolution = Decimal("0.01")

    discretized_ahs = ahs.discretize(device)
    discretized_ir = discretized_ahs.to_ir()
    discretized_json = json.loads(discretized_ir.json())
    assert discretized_json["setup"]["atomArray"] == {
        "filling": [1, 1, 1, 1, 1, 0, 0],
        "sites": [
            [0.0, 0.0],
            [0.0, 3e-06],
            [0.0, 6e-06],
            [3e-06, 0.0],
            [3e-06, 3e-06],
            [3e-06, 3e-06],
            [3e-06, 6e-06],
        ],
    }
    assert discretized_json["hamiltonian"]["drivingFields"][0]["amplitude"] == {
        "pattern": "uniform",
        "sequence": {"times": [0.0, 3e-07, 2.7e-06, 3e-06], "values": [0, 25132800, 25132800, 0]},
    }
    assert discretized_json["hamiltonian"]["drivingFields"][0]["phase"] == {
        "pattern": "uniform",
        "sequence": {"times": [0.0, 3e-06], "values": [0.0, 0.0]},
    }
    assert discretized_json["hamiltonian"]["drivingFields"][0]["detuning"] == {
        "pattern": "uniform",
        "sequence": {
            "times": [0.0, 3e-07, 2.7e-06, 3e-06],
            "values": [-125664000.0, -125664000.0, 125664000.0, 125664000.0],
        },
    }
    assert discretized_json["hamiltonian"]["shiftingFields"][0]["magnitude"] == {
        "pattern": [0.5, 1.0, 0.5, 0.5, 0.5, 0.5],
        "sequence": {"times": [0.0, 3e-06], "values": [-125664000.0, 125664000.0]},
    }
