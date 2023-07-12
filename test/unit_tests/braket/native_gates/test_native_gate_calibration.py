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

from braket.circuits import Gate, QubitSet
from braket.native_gates.native_gate_calibration import NativeGateCalibration
from braket.pulse import Frame, Port, PulseSequence


@pytest.fixture
def port():
    return Port("test_port_ff", dt=1e-9)


@pytest.fixture
def frame_id():
    return "test_frame_rf"


@pytest.fixture
def frame(frame_id, port):
    return Frame(frame_id, port, 1e6, is_predefined=True)


@pytest.fixture
def pulse_sequence(frame):
    return (
        PulseSequence()
        .barrier(qubits_or_frames=[frame])
        .delay(qubits_or_frames=[frame], duration=1000)
    )


def test_ngc_creation(pulse_sequence):
    calibration_key = (Gate.H(), QubitSet([0, 1]))
    calibration = NativeGateCalibration({calibration_key: pulse_sequence})

    assert calibration.calibration_data[calibration_key] == pulse_sequence


def test_ngc_copy(pulse_sequence):
    calibration_key = (Gate.H(), QubitSet([0, 1]))
    calibration = NativeGateCalibration({calibration_key: pulse_sequence})

    assert calibration == calibration.copy()


def test_filter_data(pulse_sequence):
    calibration_key = (Gate.Z(), QubitSet([0, 1]))
    calibration_key_2 = (Gate.H(), QubitSet([0, 1]))
    calibration = NativeGateCalibration(
        {calibration_key: pulse_sequence, calibration_key_2: pulse_sequence}
    )
    expected_calibration = NativeGateCalibration({calibration_key: pulse_sequence})

    assert expected_calibration == calibration.filter_data(gates=[Gate.Z()])


def test_get_fidelity(pulse_sequence):
    calibration_key = (Gate.H(), QubitSet([0, 1]))
    calibration = NativeGateCalibration({calibration_key: pulse_sequence})

    assert calibration.get_fidelity(calibration_key) is None


def test_to_defcal(pulse_sequence):
    calibration_key = (Gate.Rx(angle=1), QubitSet([0, 1]))
    calibration = NativeGateCalibration({calibration_key: pulse_sequence})
    expected_defcal = "\n".join(
        [
            "OPENQASM 3.0;",
            "defcal rx(angle 1.0) $0 $1 {",
            "    barrier test_frame_rf;",
            "    delay[1000000000000.0ns] test_frame_rf;",
            "}",
        ]
    )

    assert calibration.to_defcal() == expected_defcal


def test_to_def_cal_with_key(pulse_sequence):
    calibration_key = (Gate.Z(), QubitSet([0, 1]))
    calibration_key_2 = (Gate.H(), QubitSet([0, 1]))
    calibration = NativeGateCalibration(
        {calibration_key: pulse_sequence, calibration_key_2: pulse_sequence}
    )
    expected_defcal = "\n".join(
        [
            "OPENQASM 3.0;",
            "defcal z $0 $1 {",
            "    barrier test_frame_rf;",
            "    delay[1000000000000.0ns] test_frame_rf;",
            "}",
        ]
    )
    assert expected_defcal == calibration.to_defcal(calibration_key)


def test_ngc_length(pulse_sequence):
    calibration_key = (Gate.Z(), QubitSet([0, 1]))
    calibration_key_2 = (Gate.H(), QubitSet([0, 1]))
    calibration = NativeGateCalibration(
        {calibration_key: pulse_sequence, calibration_key_2: pulse_sequence}
    )

    assert len(calibration) == 2


def test_get_pulse_sequence(pulse_sequence):
    calibration_key = (Gate.H(), QubitSet([0, 1]))
    calibration = NativeGateCalibration({calibration_key: pulse_sequence})

    assert calibration.get_pulse_sequence(calibration_key) == pulse_sequence


@pytest.mark.xfail(raises=ValueError)
def test_get_pulse_sequence_bad_key(pulse_sequence):
    calibration_key = (Gate.H, QubitSet([0, 1]))
    calibration = NativeGateCalibration({calibration_key: pulse_sequence})

    calibration.get_pulse_sequence(calibration_key)
