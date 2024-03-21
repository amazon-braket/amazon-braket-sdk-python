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
from braket.circuits import Circuit, Gate, Observable, QubitSet
from braket.circuits.circuit_pulse_sequence import CircuitPulseSequenceBuilder
from braket.circuits.gate_calibrations import GateCalibrations
from braket.device_schema.ionq import IonqDeviceCapabilities
from braket.device_schema.oqc import OqcDeviceCapabilities
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.parametric.free_parameter import FreeParameter
from braket.pulse.frame import Frame
from braket.pulse.port import Port
from braket.pulse.pulse_sequence import PulseSequence
from braket.pulse.waveforms import DragGaussianWaveform

RIGETTI_ARN = "arn:aws:braket:::device/qpu/rigetti/Aspen-M-3"
OQC_ARN = "arn:aws:braket:::device/qpu/oqc/Lucy"
IONQ_ARN = "arn:aws:braket:::device/qpu/ionq/Harmony"

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

MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_2 = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.pulse.pulse_device_action_properties",
        "version": "1",
    },
    "supportedQhpTemplateWaveforms": {},
    "supportedFunctions": {},
    "ports": {
        "channel_14": {
            "portId": "channel_14",
            "direction": "rx",
            "portType": "port_type_1",
            "dt": 5e-10,
            "qubitMappings": [1],
            "centerFrequencies": None,
            "qhpSpecificProperties": None,
        }
    },
    "frames": {
        "r1_measure": {
            "frameId": "r1_measure",
            "portId": "channel_14",
            "frequency": 9624889855.38831,
            "centerFrequency": 9000000000.0,
            "phase": 0.0,
            "associatedGate": None,
            "qubitMappings": [1],
            "qhpSpecificProperties": None,
        }
    },
}


def get_rigetti_pulse_model(capabilities_json):
    device_json = {
        "braketSchemaHeader": {
            "name": "braket.device_schema.rigetti.rigetti_device_capabilities",
            "version": "1",
        },
        "service": {
            "executionWindows": [],
            "shotsRange": [1, 10],
        },
        "provider": {"specs": {}},
        "action": {
            "braket.ir.jaqcd.program": {
                "actionType": "braket.ir.jaqcd.program",
                "version": ["1"],
                "supportedOperations": [],
            }
        },
        "paradigm": {
            "qubitCount": 1,
            "nativeGateSet": [],
            "connectivity": {"fullyConnected": False, "connectivityGraph": {}},
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


def get_oqc_pulse_model(capabilities_json):
    device_json = {
        "braketSchemaHeader": {
            "name": "braket.device_schema.oqc.oqc_device_capabilities",
            "version": "1",
        },
        "service": {
            "executionWindows": [],
            "shotsRange": [1, 10],
        },
        "action": {
            "braket.ir.jaqcd.program": {
                "actionType": "braket.ir.jaqcd.program",
                "version": ["1"],
                "supportedOperations": [],
            }
        },
        "paradigm": {
            "qubitCount": 30,
            "nativeGateSet": [],
            "connectivity": {"fullyConnected": False, "connectivityGraph": {}},
        },
        "deviceParameters": {},
        "pulse": capabilities_json,
    }
    device_obj = OqcDeviceCapabilities.parse_obj(device_json)
    return {
        "deviceName": "Lucy",
        "deviceType": "QPU",
        "providerName": "Oxford",
        "deviceStatus": "OFFLINE",
        "deviceCapabilities": device_obj.json(),
    }


def get_ionq_model():
    device_json = {
        "braketSchemaHeader": {
            "name": "braket.device_schema.ionq.ionq_device_capabilities",
            "version": "1",
        },
        "service": {
            "executionWindows": [],
            "shotsRange": [1, 10],
        },
        "action": {
            "braket.ir.jaqcd.program": {
                "actionType": "braket.ir.jaqcd.program",
                "version": ["1"],
                "supportedOperations": [],
            }
        },
        "paradigm": {
            "qubitCount": 30,
            "nativeGateSet": [],
            "connectivity": {"fullyConnected": True, "connectivityGraph": {}},
        },
        "deviceParameters": {},
    }
    device_obj = IonqDeviceCapabilities.parse_obj(device_json)
    return {
        "deviceName": "IonqDevice",
        "deviceType": "QPU",
        "providerName": "IonQ",
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
        mock_session.get_device.return_value = get_rigetti_pulse_model(
            MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_1
        )
        yield AwsDevice(RIGETTI_ARN, mock_session)


@pytest.fixture
def OQC_device():
    response_data_content = {"gates": {}, "waveforms": {}}
    response_data_stream = io.BytesIO(json.dumps(response_data_content).encode("utf-8"))
    with patch("urllib.request.urlopen") as mock_url_request:
        mock_url_request.return_value.__enter__.return_value = response_data_stream
        mock_session = Mock()
        mock_session.get_device.return_value = get_oqc_pulse_model(
            MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_2
        )
        yield AwsDevice(OQC_ARN, mock_session)


@pytest.fixture
def not_supported_device():
    response_data_content = {"gates": {}, "waveforms": {}}
    response_data_stream = io.BytesIO(json.dumps(response_data_content).encode("utf-8"))
    with patch("urllib.request.urlopen") as mock_url_request:
        mock_url_request.return_value.__enter__.return_value = response_data_stream
        mock_session = Mock()
        mock_session.get_device.return_value = get_ionq_model()
        yield AwsDevice(IONQ_ARN, mock_session)


@pytest.fixture
def port():
    return Port(port_id="device_port_x0", dt=1e-9, properties={})


@pytest.fixture
def frame_1(port):
    return Frame(
        frame_id="frame_1", frequency=2e9, port=port, phase=0, is_predefined=False
    )


@pytest.fixture
def pulse_sequence(frame_1):
    return (
        PulseSequence()
        .set_frequency(
            frame_1,
            6e6,
        )
        .play(
            frame_1,
            DragGaussianWaveform(length=3e-3, sigma=0.4, beta=0.2, id="drag_gauss_wf"),
        )
    )


@pytest.fixture()
def user_defined_gate_calibrations(pulse_sequence):
    calibration_key = (Gate.Z(), QubitSet([1]))
    return GateCalibrations(
        {
            calibration_key: pulse_sequence,
        }
    )


def test_empty_circuit(device):
    assert CircuitPulseSequenceBuilder(device).build_pulse_sequence(Circuit()) == PulseSequence()


def test_no_device():
    with pytest.raises(ValueError, match="Device must be set before building pulse sequences."):
        CircuitPulseSequenceBuilder(None)


def test_not_supported_device(not_supported_device):
    with pytest.raises(ValueError, match=f"Device {not_supported_device.name} is not supported."):
        CircuitPulseSequenceBuilder(not_supported_device)


def test_unbound_circuit(device):
    circuit = Circuit().rz(0, FreeParameter("theta"))
    with pytest.raises(
        ValueError, match="All parameters must be assigned to draw the pulse sequence."
    ):
        circuit.pulse_sequence(device)


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


def test_user_defined_gate_calibrations_extension(device, user_defined_gate_calibrations):
    circ = Circuit().z(1)
    expected = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    bit[1] psb;",
            "    frame frame_1 = newframe(device_port_x0, 2000000000.0, 0);",
            "    waveform drag_gauss_wf = drag_gaussian(3.0ms, 400.0ms, 0.2, 1, false);",
            "    set_frequency(frame_1, 6000000.0);",
            "    play(frame_1, drag_gauss_wf);",
            "    psb[0] = capture_v0(q1_ro_rx_frame);",
            "}",
        ]
    )
    assert (
        circ.pulse_sequence(device, user_defined_gate_calibrations.pulse_sequences).to_ir()
        == expected
    )


def test_with_oxford_device(OQC_device, user_defined_gate_calibrations):
    circ = Circuit().z(1)
    expected = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    bit[1] psb;",
            "    frame frame_1 = newframe(device_port_x0, 2000000000.0, 0);",
            "    waveform drag_gauss_wf = drag_gaussian(3.0ms, 400.0ms, 0.2, 1, false);",
            "    set_frequency(frame_1, 6000000.0);",
            "    play(frame_1, drag_gauss_wf);",
            "    psb[0] = capture_v0(r1_measure);",
            "}",
        ]
    )
    assert (
        circ.pulse_sequence(OQC_device, user_defined_gate_calibrations.pulse_sequences).to_ir()
        == expected
    )


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


def test_pulse_gate(device):
    pulse_sequence = PulseSequence().set_frequency(device.frames["q0_rf_frame"], 1e6)
    circ = Circuit().pulse_gate(0, pulse_sequence)
    expected = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    bit[1] psb;",
            "    set_frequency(q0_rf_frame, 1000000.0);",
            "    psb[0] = capture_v0(q0_ro_rx_frame);",
            "}",
        ]
    )

    assert circ.pulse_sequence(device).to_ir() == expected


def test_missing_calibration(device):
    circuit = Circuit().rz(1, 0.1)
    with pytest.raises(
        ValueError, match="No pulse sequence for Rz was provided in the gate calibration set."
    ):
        circuit.pulse_sequence(device)


def test_expectation_value_result_type_on_one_qubit(device):
    circ = Circuit().cphaseshift(0, 1, 0.1).expectation(observable=Observable.X(), target=[1])
    expected = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    bit[2] psb;",
            "    waveform q0_q1_cphase_sqrtCPHASE = {0.0, 0.0, 0.0, 0.0};",
            "    play(q0_q1_cphase_frame, q0_q1_cphase_sqrtCPHASE);",
            "    shift_phase(q0_rf_frame, -0.1);",
            "    rx(pi/2) $1;",  # FIXME: this need the right basis rotation
            "    psb[0] = capture_v0(q0_ro_rx_frame);",
            "    psb[1] = capture_v0(q1_ro_rx_frame);",
            "}",
        ]
    )
    with pytest.raises(
        NotImplementedError, match="_to_pulse_sequence has not been implemented yet."
    ):
        assert circ.pulse_sequence(device).to_ir() == expected


def test_expectation_value_result_type_on_all_qubits(device):
    circ = Circuit().cphaseshift(0, 1, 0.1).expectation(observable=Observable.X())
    expected = "\n".join(
        [
            "OPENQASM 3.0;",
            "cal {",
            "    bit[2] psb;",
            "    waveform q0_q1_cphase_sqrtCPHASE = {0.0, 0.0, 0.0, 0.0};",
            "    play(q0_q1_cphase_frame, q0_q1_cphase_sqrtCPHASE);",
            "    shift_phase(q0_rf_frame, -0.1);",
            "    rx(pi/2) $0;",  # FIXME: this need the right basis rotation
            "    rx(pi/2) $1;",  # FIXME: this need the right basis rotation
            "    psb[0] = capture_v0(q0_ro_rx_frame);",
            "    psb[1] = capture_v0(q1_ro_rx_frame);",
            "}",
        ]
    )
    with pytest.raises(
        NotImplementedError, match="_to_pulse_sequence has not been implemented yet."
    ):
        assert circ.pulse_sequence(device).to_ir() == expected


def test_no_target_result_type(device):
    circ = Circuit().rx(0, np.pi / 2).state_vector()
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
    with pytest.warns(
        UserWarning,
        match=r"StateVector\(\) does not have have a pulse representation and it is ignored.",
    ):
        assert circ.pulse_sequence(device).to_ir() == expected
