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

import pytest

from braket.ahs.driving_field import DrivingField
from braket.ahs.field import Field
from braket.ahs.hamiltonian import Hamiltonian
from braket.timings.time_series import TimeSeries


@pytest.fixture
def default_driving_field():
    return DrivingField(Mock(spec=Field), Mock(spec=Field), Mock(spec=Field))


def test_create():
    mock0 = Mock(spec=Field)
    mock1 = Mock(spec=Field)
    mock2 = Mock(spec=Field)
    field = DrivingField(amplitude=mock0, phase=mock1, detuning=mock2)
    assert mock0 == field.amplitude
    assert mock1 == field.phase
    assert mock2 == field.detuning


def test_create_non_field():
    mock0 = Mock(spec=TimeSeries)
    mock1 = Mock(spec=TimeSeries)
    mock2 = Mock(spec=TimeSeries)
    field = DrivingField(amplitude=mock0, phase=mock1, detuning=mock2)
    assert mock0 == field.amplitude.time_series
    assert mock1 == field.phase.time_series
    assert mock2 == field.detuning.time_series


def test_add_hamiltonian(default_driving_field):
    expected = [default_driving_field, Mock(), Mock(), Mock()]
    result = expected[0] + Hamiltonian([expected[1], expected[2], expected[3]])
    assert result.terms == expected


def test_add_to_hamiltonian(default_driving_field):
    expected = [Mock(), Mock(), Mock(), default_driving_field]
    result = Hamiltonian([expected[0], expected[1], expected[2]]) + expected[3]
    assert result.terms == expected


def test_add_to_other():
    field0 = DrivingField(Mock(spec=Field), Mock(spec=Field), Mock(spec=Field))
    field1 = DrivingField(Mock(spec=Field), Mock(spec=Field), Mock(spec=Field))
    result = field0 + field1
    assert type(result) is Hamiltonian
    assert result.terms == [field0, field1]


def test_add_to_self(default_driving_field):
    result = default_driving_field + default_driving_field
    assert type(result) is Hamiltonian
    assert result.terms == [default_driving_field, default_driving_field]


def test_iadd_to_other(default_driving_field):
    expected = [Mock(), Mock(), Mock(), default_driving_field]
    other = Hamiltonian([expected[0], expected[1], expected[2]])
    other += expected[3]
    assert other.terms == expected


def test_discretize():
    amplitude_mock = Mock(spec=Field)
    amplitude_mock.discretize.return_value = Mock(spec=Field)
    phase_mock = Mock(spec=Field)
    phase_mock.discretize.return_value = Mock(spec=Field)
    detuning_mock = Mock(spec=Field)
    detuning_mock.discretize.return_value = Mock(spec=Field)
    mock_properties = Mock()
    field = DrivingField(amplitude=amplitude_mock, phase=phase_mock, detuning=detuning_mock)
    discretized_field = field.discretize(mock_properties)
    amplitude_mock.discretize.assert_called_with(
        time_resolution=mock_properties.rydberg.rydbergGlobal.timeResolution,
        value_resolution=mock_properties.rydberg.rydbergGlobal.rabiFrequencyResolution,
    )
    phase_mock.discretize.assert_called_with(
        time_resolution=mock_properties.rydberg.rydbergGlobal.timeResolution,
        value_resolution=mock_properties.rydberg.rydbergGlobal.phaseResolution,
    )
    detuning_mock.discretize.assert_called_with(
        time_resolution=mock_properties.rydberg.rydbergGlobal.timeResolution,
        value_resolution=mock_properties.rydberg.rydbergGlobal.detuningResolution,
    )
    assert field is not discretized_field
    assert discretized_field.amplitude == amplitude_mock.discretize.return_value
    assert discretized_field.phase == phase_mock.discretize.return_value
    assert discretized_field.detuning == detuning_mock.discretize.return_value


@pytest.mark.xfail(raises=ValueError)
def test_iadd_to_itself(default_driving_field):
    default_driving_field += Hamiltonian(Mock())
