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

import numpy as np
import pytest

from braket.ahs.analog_hamiltonian_simulation import (
    AnalogHamiltonianSimulation,
    AtomArrangement,
    DiscretizationError,
    DrivingField,
    LocalDetuning,
    SiteType,
)
from braket.ahs.atom_arrangement import AtomArrangementItem
from braket.ahs.field import Field
from braket.ahs.pattern import Pattern
from braket.ir.ahs.program_v1 import Program
from braket.timings.time_series import TimeSeries


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
def local_detuning():
    return LocalDetuning(
        Field(
            TimeSeries().put(0.0, -1.25664e8).put(3.0e-6, 1.25664e8),
            Pattern([0.5, 1.0, 0.5, 0.5, 0.5, 0.5]),
        )
    )


@pytest.fixture
def ir():
    return Program.parse_raw_schema(
        """
{
  "braketSchemaHeader": {
    "name": "braket.ir.ahs.program",
    "version": "1"
  },
  "setup": {
    "ahs_register": {
      "sites": [
        [
          "0.0",
          "0.0"
        ],
        [
          "0.0",
          "0.000003"
        ],
        [
          "0.0",
          "0.000006"
        ],
        [
          "0.000003",
          "0.0"
        ],
        [
          "0.000003",
          "0.000003"
        ],
        [
          "0.000003",
          "0.000003"
        ],
        [
          "0.000003",
          "0.000006"
        ]
      ],
      "filling": [
        1,
        1,
        1,
        1,
        1,
        0,
        0
      ]
    }
  },
  "hamiltonian": {
    "drivingFields": [
      {
        "amplitude": {
          "time_series": {
            "values": [
              "0.0",
              "25132700.0",
              "25132700.0",
              "0.0"
            ],
            "times": [
              "0.0",
              "3E-7",
              "0.0000027",
              "0.000003"
            ]
          },
          "pattern": "uniform"
        },
        "phase": {
          "time_series": {
            "values": [
              "0",
              "0"
            ],
            "times": [
              "0.0",
              "0.000003"
            ]
          },
          "pattern": "uniform"
        },
        "detuning": {
          "time_series": {
            "values": [
              "-125664000.0",
              "-125664000.0",
              "125664000.0",
              "125664000.0"
            ],
            "times": [
              "0.0",
              "3E-7",
              "0.0000027",
              "0.000003"
            ]
          },
          "pattern": "uniform"
        }
      }
    ],
    "localDetuning": [
      {
        "magnitude": {
          "time_series": {
            "values": [
              "-125664000.0",
              "125664000.0"
            ],
            "times": [
              "0.0",
              "0.000003"
            ]
          },
          "pattern": [
            "0.5",
            "1.0",
            "0.5",
            "0.5",
            "0.5",
            "0.5"
          ]
        }
      }
    ]
  }
}
"""
    )


def test_create():
    mock0 = Mock()
    mock1 = Mock()
    ahs = AnalogHamiltonianSimulation(register=mock0, hamiltonian=mock1)
    assert mock0 == ahs.register
    assert mock1 == ahs.hamiltonian


def test_to_ir(register, driving_field, local_detuning):
    hamiltonian = driving_field + local_detuning
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


def test_from_ir(ir):
    problem = AnalogHamiltonianSimulation.from_ir(ir).to_ir()
    assert problem == ir
    assert problem == Program.parse_raw_schema(problem.json())


def test_from_ir_empty():
    empty_ir = Program.parse_raw_schema(
        """
{
  "braketSchemaHeader": {
    "name": "braket.ir.ahs.program",
    "version": "1"
  },
  "setup": {
    "ahs_register": {
      "sites": [],
      "filling": []
    }
  },
  "hamiltonian": {
    "drivingFields": [],
    "localDetuning": []
  }
}
"""
    )
    problem = AnalogHamiltonianSimulation.from_ir(empty_ir).to_ir()
    assert problem == empty_ir
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


def test_discretize(register, driving_field, local_detuning):
    hamiltonian = driving_field + local_detuning
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

    discretized_ahs = ahs.discretize(device)
    discretized_ir = discretized_ahs.to_ir()
    discretized_json = json.loads(discretized_ir.json())
    assert discretized_json["setup"]["ahs_register"] == {
        "filling": [1, 1, 1, 1, 1, 0, 0],
        "sites": [
            ["0E-7", "0E-7"],
            ["0E-7", "0.0000030"],
            ["0E-7", "0.0000060"],
            ["0.0000030", "0E-7"],
            ["0.0000030", "0.0000030"],
            ["0.0000030", "0.0000030"],
            ["0.0000030", "0.0000060"],
        ],
    }
    assert discretized_json["hamiltonian"]["drivingFields"][0]["amplitude"] == {
        "pattern": "uniform",
        "time_series": {
            "times": ["0E-9", "3.00E-7", "0.000002700", "0.000003000"],
            "values": ["0", "25132800", "25132800", "0"],
        },
    }
    assert discretized_json["hamiltonian"]["drivingFields"][0]["phase"] == {
        "pattern": "uniform",
        "time_series": {"times": ["0E-9", "0.000003000"], "values": ["0E-7", "0E-7"]},
    }
    assert discretized_json["hamiltonian"]["drivingFields"][0]["detuning"] == {
        "pattern": "uniform",
        "time_series": {
            "times": ["0E-9", "3.00E-7", "0.000002700", "0.000003000"],
            "values": ["-125664000.0", "-125664000.0", "125664000.0", "125664000.0"],
        },
    }
    local_detuning = discretized_json["hamiltonian"]["localDetuning"][0]["magnitude"]
    assert local_detuning == {
        "pattern": ["0.5", "1", "0.5", "0.5", "0.5", "0.5"],
        "time_series": {
            "times": ["0E-9", "0.000003000"],
            "values": ["-125664000", "125664000"],
        },
    }


def test_converting_numpy_array_sites_to_ir(driving_field):
    hamiltonian = driving_field

    sites = np.array([
        [0.0, 0.0],
        [0.0, 1.0e-6],
        [1e-6, 2.0e-6],
    ])
    register = AtomArrangement()
    for site in sites:
        register.add(site)

    ahs = AnalogHamiltonianSimulation(register=register, hamiltonian=hamiltonian)
    sites_in_ir = ahs.to_ir().setup.ahs_register.sites
    expected_sites_in_ir = [
        [Decimal("0.0"), Decimal("0.0")],
        [Decimal("0.0"), Decimal("1e-6")],
        [Decimal("1e-6"), Decimal("2e-6")],
    ]

    assert sites_in_ir == expected_sites_in_ir


@pytest.mark.xfail(raises=ValueError)
def test_site_validation_wrong_length():
    register = AtomArrangement()
    register.add(np.array([0.0, 1e-6, -1e-6]))


@pytest.mark.xfail(raises=TypeError)
def test_site_validation_non_number():
    register = AtomArrangement()
    register.add([
        "not-a-number",
        [
            "also-not-a-number",
        ],
    ])


@pytest.mark.xfail(raises=TypeError)
def test_site_validation_not_a_tuple():
    AtomArrangementItem(None, SiteType.FILLED)


@pytest.mark.xfail(raises=ValueError)
def test_site_validation_invalid_site_type():
    register = AtomArrangement()
    register.add([0.0, 0.0], "not-a-valid-site-type")
