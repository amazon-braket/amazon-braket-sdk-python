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

from braket.ahs.hamiltonian import Hamiltonian
from braket.ahs.local_detuning import LocalDetuning
from braket.timings.time_series import StitchBoundaryCondition


@pytest.fixture
def default_local_detuning():
    return LocalDetuning(Mock())


def test_create():
    mock0 = Mock()
    field = LocalDetuning(magnitude=mock0)
    assert mock0 == field.magnitude


def test_add_hamiltonian(default_local_detuning):
    expected = [default_local_detuning, Mock(), Mock(), Mock()]
    result = expected[0] + Hamiltonian([expected[1], expected[2], expected[3]])
    assert result.terms == expected


def test_add_to_hamiltonian(default_local_detuning):
    expected = [Mock(), Mock(), Mock(), default_local_detuning]
    result = Hamiltonian([expected[0], expected[1], expected[2]]) + expected[3]
    assert result.terms == expected


def test_add_to_other():
    field0 = LocalDetuning(Mock())
    field1 = LocalDetuning(Mock())
    result = field0 + field1
    assert type(result) is Hamiltonian
    assert result.terms == [field0, field1]


def test_add_to_self(default_local_detuning):
    result = default_local_detuning + default_local_detuning
    assert type(result) is Hamiltonian
    assert result.terms == [default_local_detuning, default_local_detuning]


def test_iadd_to_other(default_local_detuning):
    expected = [Mock(), Mock(), Mock(), default_local_detuning]
    other = Hamiltonian([expected[0], expected[1], expected[2]])
    other += expected[3]
    assert other.terms == expected


def test_from_lists():
    times = [0, 0.1, 0.2, 0.3]
    glob_amplitude = [0.5, 0.8, 0.9, 1.0]
    pattern = [0.3, 0.7, 0.6, -0.5, 0, 1.6]

    sh_field = LocalDetuning.from_lists(times, glob_amplitude, pattern)
    assert sh_field.magnitude.time_series.values() == glob_amplitude
    assert sh_field.magnitude.pattern.series == pattern

    assert sh_field.magnitude.time_series.times() == times


@pytest.mark.xfail(raises=ValueError)
def test_from_lists_not_eq_length():
    times = [0, 0.1, 0.2]
    glob_amplitude = [0.5, 0.8, 0.9, 1.0]
    pattern = [0.3, 0.7, 0.6, -0.5, 0, 1.6]

    LocalDetuning.from_lists(times, glob_amplitude, pattern)


def test_stitch():
    times_1 = [0, 0.1, 0.2, 0.3]
    glob_amplitude_1 = [0.5, 0.8, 0.9, 1.0]
    pattern_1 = [0.3, 0.7, 0.6, -0.5, 0, 1.6]

    times_2 = [0, 0.1, 0.2, 0.3]
    glob_amplitude_2 = [0.5, 0.8, 0.9, 1.0]
    pattern_2 = pattern_1

    sh_field_1 = LocalDetuning.from_lists(times_1, glob_amplitude_1, pattern_1)
    sh_field_2 = LocalDetuning.from_lists(times_2, glob_amplitude_2, pattern_2)

    new_sh_field = sh_field_1.stitch(sh_field_2, boundary=StitchBoundaryCondition.LEFT)

    expected_times = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    expected_amplitude = glob_amplitude_1 + glob_amplitude_2[1:]
    assert new_sh_field.magnitude.time_series.times() == expected_times
    assert new_sh_field.magnitude.time_series.values() == expected_amplitude
    assert new_sh_field.magnitude.pattern == sh_field_1.magnitude.pattern


@pytest.mark.xfail(raises=ValueError)
def test_stitch_not_eq_pattern():
    times_1 = [0, 0.1, 0.2, 0.3]
    glob_amplitude_1 = [0.5, 0.8, 0.9, 1.0]
    pattern_1 = [0.3, 0.7, 0.6, -0.5, 0, 1.6]

    times_2 = [0.4, 0.5, 0.6, 0.7]
    glob_amplitude_2 = [0.5, 0.8, 0.9, 1.0]
    pattern_2 = [-0.3, 0.7, 0.6, -0.5, 0, 1.6]

    sh_field_1 = LocalDetuning.from_lists(times_1, glob_amplitude_1, pattern_1)
    sh_field_2 = LocalDetuning.from_lists(times_2, glob_amplitude_2, pattern_2)

    sh_field_1.stitch(sh_field_2)


def test_discretize():
    magnitude_mock = Mock()
    mock_properties = Mock()
    field = LocalDetuning(magnitude=magnitude_mock)
    discretized_field = field.discretize(mock_properties)
    magnitude_mock.discretize.assert_called_with(
        time_resolution=mock_properties.rydberg.rydbergLocal.timeResolution,
    )
    assert field is not discretized_field
    assert discretized_field.magnitude == magnitude_mock.discretize.return_value


@pytest.mark.xfail(raises=ValueError)
def test_iadd_to_itself(default_local_detuning):
    default_local_detuning += Hamiltonian(Mock())
