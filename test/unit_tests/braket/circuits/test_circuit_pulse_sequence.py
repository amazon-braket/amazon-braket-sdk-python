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

import io
import json
from unittest.mock import Mock, patch

import numpy as np
import pytest

from braket.aws import AwsDevice
from braket.circuits import Circuit, Gate, QubitSet
from braket.circuits.circuit_pulse_sequence import CircuitPulseSequenceBuilder
from braket.circuits.gate_calibrations import GateCalibrations
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.pulse.pulse_sequence import PulseSequence
from braket.pulse.waveforms import DragGaussianWaveform

RIGETTI_ARN = "arn:aws:braket:::device/qpu/rigetti/Aspen-M-3"

MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_1 = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.pulse.pulse_device_action_properties",
        "version": "1",
    },
    "supportedQhpTemplateWaveforms": {},
    "supportedFunctions": {},
    "ports": {
        "q0_ff": {
            "portId": "q0_ff",
            "direction": "tx",
            "portType": "ff",
            "dt": 1e-09,
            "qubitMappings": None,
            "centerFrequencies": [375000000.0],
            "qhpSpecificProperties": None,
        },
        "q0_rf": {
            "portId": "q0_rf",
            "direction": "tx",
            "portType": "rf",
            "dt": 1e-09,
            "qubitMappings": None,
            "centerFrequencies": [4875000000.0],
            "qhpSpecificProperties": None,
        },
        "q0_ro_rx": {
            "portId": "q0_ro_rx",
            "direction": "rx",
            "portType": "ro_rx",
            "dt": 5e-10,
            "qubitMappings": None,
            "centerFrequencies": [],
            "qhpSpecificProperties": None,
        },
        "q1_ro_rx": {
            "portId": "q1_ro_rx",
            "direction": "rx",
            "portType": "ro_rx",
            "dt": 5e-10,
            "qubitMappings": None,
            "centerFrequencies": [],
            "qhpSpecificProperties": None,
        },
    },
    "frames": {
        "q0_q1_cphase_frame": {
            "frameId": "q0_q1_cphase_frame",
            "portId": "q0_ff",
            "frequency": 4276236.85736918,
            "centerFrequency": 375000000.0,
            "phase": 1.0,
            "associatedGate": "cphase",
            "qubitMappings": [0, 1],
            "qhpSpecificProperties": None,
        },
        "q0_rf_frame": {
            "frameId": "q0_rf_frame",
            "portId": "q0_rf",
            "frequency": 5041233612.58213,
            "centerFrequency": 4875000000.0,
            "phase": 0.0,
            "associatedGate": None,
            "qubitMappings": [0],
            "qhpSpecificProperties": None,
        },
        "q0_ro_rx_frame": {
            "frameId": "q0_ro_rx_frame",
            "portId": "q0_ro_rx",
            "frequency": 7359200001.83969,
            "centerFrequency": None,
            "phase": 0.0,
            "associatedGate": None,
            "qubitMappings": [0],
            "qhpSpecificProperties": None,
        },
        "q1_ro_rx_frame": {
            "frameId": "q1_ro_rx_frame",
            "portId": "q1_ro_rx",
            "frequency": 7228259838.38781,
            "centerFrequency": None,
            "phase": 0.0,
            "associatedGate": None,
            "qubitMappings": [1],
            "qhpSpecificProperties": None,
        },
    },
    "nativeGateCalibrationsRef": "file://hostname/foo/bar",
}


def get_pulse_model(capabilities_json):
    device_json = {
        "braketSchemaHeader": {
            "name": "braket.device_schema.rigetti.rigetti_device_capabilities",
            "version": "1",
        },
        "service": {
            "executionWindows": [
                {
                    "executionDay": "Everyday",
                    "windowStartHour": "11:00",
                    "windowEndHour": "12:00",
                }
            ],
            "shotsRange": [1, 10],
        },
        "provider": {
            "specs": {
                "1Q": {
                    "0": {
                        "fActiveReset": 0.9715,
                        "fRO": 0.951,
                        "f1QRB": 0.997339217568556,
                        "f1QRB_std_err": 0.00006690422818326937,
                        "f1Q_simultaneous_RB": 0.9949723201166536,
                        "f1Q_simultaneous_RB_std_err": 0.00021695233492231294,
                        "T1": 0.000010019627401991471,
                        "T2": 0.000018156447816365015,
                    }
                },
                "2Q": {
                    "0-1": {
                        "fCZ": 0.9586440436264603,
                        "fCZ_std_err": 0.007025921432645824,
                        "fCPHASE": 0.9287330972713645,
                        "fCPHASE_std_err": 0.009709406809550082,
                        "fXY": 0.9755179214520402,
                        "fXY_std_err": 0.0060234488782598536,
                    },
                },
            }
        },
        "action": {
            "braket.ir.jaqcd.program": {
                "actionType": "braket.ir.jaqcd.program",
                "version": ["1"],
                "supportedOperations": ["H"],
            }
        },
        "paradigm": {
            "qubitCount": 30,
            "nativeGateSet": ["ccnot", "cy"],
            "connectivity": {"fullyConnected": False, "connectivityGraph": {"1": ["2", "3"]}},
        },
        "deviceParameters": {},
        "pulse": capabilities_json,
    }
    device_obj = RigettiDeviceCapabilities.parse_obj(device_json)
    return {
        "deviceName": "Aspen-M-3",
        "deviceType": "QPU",
        "providerName": "Rigetti",
        "deviceStatus": "OFFLINE",
        "deviceCapabilities": device_obj.json(),
    }


@pytest.fixture
def device():
    response_data_content = {
        "gates": {
            "0_1": {
                "cphaseshift": [
                    {
                        "name": "cphaseshift",
                        "qubits": ["0", "1"],
                        "arguments": ["theta"],
                        "calibrations": [
                            {
                                "name": "play",
                                "arguments": [
                                    {
                                        "name": "waveform",
                                        "value": "q0_q1_cphase_sqrtCPHASE",
                                        "type": "waveform",
                                    },
                                    {
                                        "name": "frame",
                                        "value": "q0_q1_cphase_frame",
                                        "type": "frame",
                                    },
                                ],
                            },
                            {
                                "name": "shift_phase",
                                "arguments": [
                                    {
                                        "name": "frame",
                                        "value": "q0_rf_frame",
                                        "type": "frame",
                                        "optional": False,
                                    },
                                    {
                                        "name": "phase",
                                        "value": "-1.0*theta",
                                        "type": "expr",
                                        "optional": False,
                                    },
                                ],
                            },
                        ],
                    }
                ],
            },
            "0": {
                "rx": [
                    {
                        "name": "rx",
                        "qubits": ["0"],
                        "arguments": ["1.5707963267948966"],
                        "calibrations": [
                            {
                                "name": "barrier",
                                "arguments": [
                                    {
                                        "name": "qubit",
                                        "value": "0",
                                        "type": "string",
                                        "optional": False,
                                    }
                                ],
                            },
                            {
                                "name": "shift_frequency",
                                "arguments": [
                                    {
                                        "name": "frame",
                                        "value": "q0_rf_frame",
                                        "type": "frame",
                                        "optional": False,
                                    },
                                    {
                                        "name": "frequency",
                                        "value": -321047.14178613486,
                                        "type": "float",
                                        "optional": False,
                                    },
                                ],
                            },
                            {
                                "name": "play",
                                "arguments": [
                                    {
                                        "name": "frame",
                                        "value": "q0_rf_frame",
                                        "type": "frame",
                                        "optional": False,
                                    },
                                    {
                                        "name": "waveform",
                                        "value": "wf_drag_gaussian_1",
                                        "type": "waveform",
                                        "optional": False,
                                    },
                                ],
                            },
                            {
                                "name": "shift_frequency",
                                "arguments": [
                                    {
                                        "name": "frame",
                                        "value": "q0_rf_frame",
                                        "type": "frame",
                                        "optional": False,
                                    },
                                    {
                                        "name": "frequency",
                                        "value": 321047.14178613486,
                                        "type": "float",
                                        "optional": False,
                                    },
                                ],
                            },
                            {
                                "name": "barrier",
                                "arguments": [
                                    {
                                        "name": "qubit",
                                        "value": "0",
                                        "type": "string",
                                        "optional": False,
                                    }
                                ],
                            },
                        ],
                    },
                ],
                "rz": [
                    {
                        "name": "rz",
                        "qubits": ["0"],
                        "arguments": ["theta"],
                        "calibrations": [
                            {
                                "name": "shift_phase",
                                "arguments": [
                                    {
                                        "name": "frame",
                                        "value": "q0_rf_frame",
                                        "type": "frame",
                                        "optional": False,
                                    },
                                    {
                                        "name": "phase",
                                        "value": "-1.0*theta",
                                        "type": "expr",
                                        "optional": False,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        },
        "waveforms": {
            "wf_drag_gaussian_1": {
                "waveformId": "wf_drag_gaussian_1",
                "name": "drag_gaussian",
                "arguments": [
                    {"name": "length", "value": 6.000000000000001e-8, "type": "float"},
                    {"name": "sigma", "value": 6.369913502160144e-9, "type": "float"},
                    {"name": "amplitude", "value": -0.4549282253548838, "type": "float"},
                    {"name": "beta", "value": 7.494904522022295e-10, "type": "float"},
                ],
            },
            "q0_q1_cphase_sqrtCPHASE": {
                "waveformId": "q0_q1_cphase_sqrtCPHASE",
                "amplitudes": [
                    [0.0, 0.0],
                    [0.0, 0.0],
                    [0.0, 0.0],
                    [0.0, 0.0],
                ],
            },
        },
    }

    response_data_stream = io.BytesIO(json.dumps(response_data_content).encode("utf-8"))
    with patch("urllib.request.urlopen") as mock_url_request:
        mock_url_request.return_value.__enter__.return_value = response_data_stream
        mock_session = Mock()
        mock_session.get_device.return_value = get_pulse_model(
            MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_1
        )
        yield AwsDevice(RIGETTI_ARN, mock_session)


@pytest.fixture
def pulse_sequence(predefined_frame_1):
    return (
        PulseSequence()
        .set_frequency(
            predefined_frame_1,
            6e6,
        )
        .play(
            predefined_frame_1,
            DragGaussianWaveform(length=3e-3, sigma=0.4, beta=0.2, id="drag_gauss_wf"),
        )
    )


@pytest.fixture()
def user_defined_gate_calibrations():
    calibration_key = (Gate.Z(), QubitSet([0, 1]))
    return GateCalibrations(
        {
            calibration_key: pulse_sequence,
        }
    )


def test_empty_circuit(device):
    assert CircuitPulseSequenceBuilder(device).build_pulse_sequence(Circuit()) == PulseSequence()


def test_no_device():
    with pytest.raises(AssertionError, match="Device must be set before building pulse sequences."):
        CircuitPulseSequenceBuilder(None)


def test_non_parametric_defcal(device):
    circ = Circuit().rx(0, np.pi / 2)
    expected = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    bit[1] psb;",
            "    waveform wf_drag_gaussian_1 = drag_gaussian(60.0ns, 6.36991350216ns, "
            "7.494904522022295e-10, -0.4549282253548838, false);",
            "    barrier $0;",
            "    shift_frequency(q0_rf_frame, -321047.14178613486);",
            "    play(q0_rf_frame, wf_drag_gaussian_1);",
            "    shift_frequency(q0_rf_frame, 321047.14178613486);",
            "    barrier $0;",
            "    psb[0] = capture_v0(q0_ro_rx_frame);",
            "}",
        ]
    )
    assert circ.pulse_sequence(device).to_ir() == expected


def test_parametric_defcal(device):
    circ = Circuit().cphaseshift(0, 1, 0.1)
    expected = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    bit[2] psb;",
            "    waveform q0_q1_cphase_sqrtCPHASE = {0.0, 0.0, 0.0, 0.0};",
            "    play(q0_q1_cphase_frame, q0_q1_cphase_sqrtCPHASE);",
            "    shift_phase(q0_rf_frame, -0.1);",
            "    psb[0] = capture_v0(q0_ro_rx_frame);",
            "    psb[1] = capture_v0(q1_ro_rx_frame);",
            "}",
        ]
    )

    assert circ.pulse_sequence(device).to_ir() == expected
