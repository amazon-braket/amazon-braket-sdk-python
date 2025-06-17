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
from braket.circuits.gate_calibrations import GateCalibrations
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


def test_gc_creation(pulse_sequence):
    calibration_key = (Gate.H(), QubitSet([0, 1]))
    calibration = GateCalibrations({calibration_key: pulse_sequence})

    assert calibration.pulse_sequences[calibration_key] == pulse_sequence


def test_gc_copy(pulse_sequence):
    calibration_key = (Gate.H(), QubitSet([0, 1]))
    calibration = GateCalibrations({calibration_key: pulse_sequence})

    assert calibration == calibration.copy()


def test_filter(pulse_sequence):
    calibration_key = (Gate.Z(), QubitSet([0]))
    calibration_key_2 = (Gate.H(), QubitSet([1]))
    calibration_key_3 = (Gate.CZ(), QubitSet([0, 1]))
    calibration = GateCalibrations({
        calibration_key: pulse_sequence,
        calibration_key_2: pulse_sequence,
        calibration_key_3: pulse_sequence,
    })
    expected_calibration_1 = GateCalibrations({calibration_key: pulse_sequence})
    expected_calibration_2 = GateCalibrations({
        calibration_key: pulse_sequence,
        calibration_key_3: pulse_sequence,
    })
    expected_calibration_3 = GateCalibrations({calibration_key_2: pulse_sequence})
    expected_calibration_4 = GateCalibrations({})
    expected_calibration_5 = calibration
    expected_calibration_6 = GateCalibrations({calibration_key_3: pulse_sequence})
    assert expected_calibration_1 == calibration.filter(gates=[Gate.Z()])
    assert expected_calibration_2 == calibration.filter(qubits=QubitSet(0))
    assert expected_calibration_3 == calibration.filter(gates=[Gate.H()], qubits=QubitSet(1))
    assert expected_calibration_4 == calibration.filter(gates=[Gate.Z()], qubits=QubitSet(1))
    assert expected_calibration_5 == calibration.filter(qubits=[QubitSet(0), QubitSet(1)])
    assert expected_calibration_6 == calibration.filter(qubits=QubitSet([0, 1]))


def test_to_ir(pulse_sequence):
    calibration_key = (Gate.Rx(angle=1), QubitSet([0, 1]))
    calibration = GateCalibrations({calibration_key: pulse_sequence})
    expected_ir = "\n".join([
        "OPENQASM 3.0;",
        "defcal rx(1.0) $0, $1 {",
        "    barrier test_frame_rf;",
        "    delay[1000s] test_frame_rf;",
        "}",
    ])

    assert calibration.to_ir() == expected_ir


@pytest.mark.xfail(raises=ValueError)
def test_to_ir_with_bad_key(pulse_sequence):
    calibration_key = (Gate.Z(), QubitSet([0, 1]))
    calibration_key_2 = (Gate.H(), QubitSet([0, 1]))
    calibration = GateCalibrations({
        calibration_key: pulse_sequence,
        calibration_key_2: pulse_sequence,
    })
    expected_ir = "\n".join([
        "OPENQASM 3.0;",
        "defcal z $0, $1 {",
        "    barrier test_frame_rf;",
        "    delay[1000s] test_frame_rf;",
        "}",
    ])
    assert expected_ir == calibration.to_ir((Gate.Z(), QubitSet([1, 2])))


def test_to_ir_with_key(pulse_sequence):
    calibration_key = (Gate.Z(), QubitSet([0, 1]))
    calibration_key_2 = (Gate.H(), QubitSet([0, 1]))
    calibration = GateCalibrations({
        calibration_key: pulse_sequence,
        calibration_key_2: pulse_sequence,
    })
    expected_ir = "\n".join([
        "OPENQASM 3.0;",
        "defcal z $0, $1 {",
        "    barrier test_frame_rf;",
        "    delay[1000s] test_frame_rf;",
        "}",
    ])
    assert expected_ir == calibration.to_ir(calibration_key)


def test_gate_calibrations_length(pulse_sequence):
    calibration_key = (Gate.Z(), QubitSet([0, 1]))
    calibration_key_2 = (Gate.H(), QubitSet([0, 1]))
    calibration = GateCalibrations({
        calibration_key: pulse_sequence,
        calibration_key_2: pulse_sequence,
    })

    assert len(calibration) == 2


@pytest.mark.parametrize(
    "bad_input",
    [
        ({(Gate.Rx(1), "string"): PulseSequence()}),
        ({(Gate.Rx(1), QubitSet(0)): 4}),
        ({("string_a", "string_b"): PulseSequence()}),
    ],
)
@pytest.mark.xfail(raises=TypeError)
def test_bad_pulse_sequence(bad_input):
    GateCalibrations(bad_input)
