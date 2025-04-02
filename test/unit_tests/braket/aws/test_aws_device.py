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
import os
import textwrap
from datetime import datetime
from unittest.mock import Mock, PropertyMock, patch
from urllib.error import URLError

import networkx as nx
import pytest
from botocore.exceptions import ClientError
from common_test_utils import (
    DM1_ARN,
    DWAVE_ARN,
    IONQ_ARN,
    OQC_ARN,
    RIGETTI_ARN,
    RIGETTI_REGION,
    SV1_ARN,
    TN1_ARN,
    run_and_assert,
    run_batch_and_assert,
)
from jsonschema import validate

from braket.aws import AwsDevice, AwsDeviceType, AwsQuantumTask
from braket.aws.queue_information import QueueDepthInfo, QueueType
from braket.circuits import Circuit, FreeParameter, Gate, Noise, QubitSet
from braket.circuits.gate_calibrations import GateCalibrations
from braket.circuits.noise_model import GateCriteria, NoiseModel
from braket.device_schema.device_execution_window import DeviceExecutionWindow
from braket.device_schema.dwave import DwaveDeviceCapabilities
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.device_schema.simulators import GateModelSimulatorDeviceCapabilities
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.pulse import DragGaussianWaveform, Frame, Port, PulseSequence

MOCK_GATE_MODEL_QPU_CAPABILITIES_JSON_1 = {
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
}

MOCK_GATE_MODEL_QPU_CAPABILITIES_1 = RigettiDeviceCapabilities.parse_obj(
    MOCK_GATE_MODEL_QPU_CAPABILITIES_JSON_1
)

MOCK_gate_calibrations_JSON = {
    "gates": {
        "0": {
            "cphaseshift": [
                {
                    "name": "cphaseshift",
                    "qubits": ["0", "1"],
                    "arguments": ["-1.5707963267948966"],
                    "calibrations": [
                        {
                            "name": "barrier",
                            "arguments": [{"name": "qubit", "value": "0", "type": "string"}],
                        },
                        {
                            "name": "play",
                            "arguments": [
                                {"name": "frame", "value": "q0_q1_cphase_frame", "type": "frame"},
                                {
                                    "name": "waveform",
                                    "value": "wf_drag_gaussian_0",
                                    "type": "waveform",
                                },
                            ],
                        },
                        {
                            "name": "barrier",
                            "arguments": [
                                {"name": "frame", "value": "q0_q1_cphase_frame", "type": "frame"}
                            ],
                        },
                        {
                            "name": "barrier",
                            "arguments": None,
                        },
                        {
                            "name": "delay",
                            "arguments": [
                                {"name": "duration", "value": 3e-07, "type": "float"},
                                {"name": "qubit", "value": "0", "type": "string"},
                                {"name": "qubit", "value": "1", "type": "string"},
                            ],
                        },
                        {
                            "name": "delay",
                            "arguments": [
                                {"name": "frame", "value": "q0_q1_cphase_frame", "type": "frame"},
                                {"name": "duration", "value": 3e-07, "type": "float"},
                            ],
                        },
                        {
                            "name": "shift_phase",
                            "arguments": [
                                {"name": "frame", "value": "q0_q1_cphase_frame", "type": "frame"},
                                {"name": "phase", "value": 3e-07, "type": "float"},
                            ],
                        },
                        {
                            "name": "shift_frequency",
                            "arguments": [
                                {"name": "frequency", "value": "theta", "type": "expr"},
                                {"name": "frame", "value": "q0_q1_cphase_frame", "type": "frame"},
                                {"name": "extra", "value": "q0_q1_cphase_frame", "type": "string"},
                            ],
                        },
                    ],
                }
            ],
            "rx": [
                {
                    "gateName": "rx",
                    "gateId": "rz_1",
                    "qubits": "0",
                    "arguments": ["theta"],
                    "calibrations": [
                        {"name": "barrier", "arguments": None},
                    ],
                }
            ],
        },
        "0_1": {
            "cz": [
                {
                    "gateName": "cz",
                    "gateId": "cz_0_1",
                    "qubits": ["1", "0"],
                    "arguments": [],
                    "calibrations": [
                        {"name": "barrier", "arguments": None},
                    ],
                }
            ],
            "rx_12": [],
        },
    },
    "waveforms": {
        "q0_q1_cz_CZ": {
            "waveformId": "q0_q1_cz_CZ",
            "amplitudes": [[0.0, 0.0], [0.0, 0.0]],
        },
        "wf_drag_gaussian_0": {
            "waveformId": "wf_drag_gaussian_0",
            "name": "drag_gaussian",
            "arguments": [
                {"name": "length", "value": 6.000000000000001e-8, "type": "float"},
                {"name": "sigma", "value": 6.369913502160144e-9, "type": "float"},
                {"name": "amplitude", "value": -0.4549282253548838, "type": "float"},
                {"name": "beta", "value": 7.494904522022295e-10, "type": "float"},
            ],
        },
        "wf_gaussian_0": {
            "waveformId": "wf_gaussian_0",
            "name": "gaussian",
            "arguments": [
                {"name": "length", "value": 6.000000000000001e-8, "type": "float"},
                {"name": "sigma", "value": 6.369913502160144e-9, "type": "float"},
                {"name": "amplitude", "value": -0.4549282253548838, "type": "float"},
            ],
        },
        "wf_constant": {
            "waveformId": "wf_constant",
            "name": "constant",
            "arguments": [
                {"name": "length", "value": 2, "type": "float"},
                {"name": "iq", "value": 0.23, "type": "complex"},
            ],
        },
    },
}


def test_mock_rigetti_schema_1():
    validate(MOCK_GATE_MODEL_QPU_CAPABILITIES_JSON_1, RigettiDeviceCapabilities.schema())


MOCK_GATE_MODEL_QPU_1 = {
    "deviceName": "Ankaa-2",
    "deviceType": "QPU",
    "providerName": "Rigetti",
    "deviceStatus": "OFFLINE",
    "deviceCapabilities": MOCK_GATE_MODEL_QPU_CAPABILITIES_1.json(),
    "deviceQueueInfo": [
        {"queue": "QUANTUM_TASKS_QUEUE", "queueSize": "19", "queuePriority": "Normal"},
        {"queue": "QUANTUM_TASKS_QUEUE", "queueSize": "3", "queuePriority": "Priority"},
        {"queue": "JOBS_QUEUE", "queueSize": "0 (3 prioritized job(s) running)"},
    ],
}

MOCK_GATE_MODEL_QPU_CAPABILITIES_JSON_2 = {
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
        "connectivity": {"fullyConnected": True, "connectivityGraph": {}},
    },
    "deviceParameters": {},
}

MOCK_GATE_MODEL_QPU_CAPABILITIES_2 = RigettiDeviceCapabilities.parse_obj(
    MOCK_GATE_MODEL_QPU_CAPABILITIES_JSON_2
)


def test_mock_rigetti_schema_2():
    validate(MOCK_GATE_MODEL_QPU_CAPABILITIES_JSON_2, RigettiDeviceCapabilities.schema())


MOCK_GATE_MODEL_QPU_2 = {
    "deviceName": "Blah",
    "deviceType": "QPU",
    "providerName": "blahhhh",
    "deviceStatus": "OFFLINE",
    "deviceCapabilities": MOCK_GATE_MODEL_QPU_CAPABILITIES_2.json(),
}

MOCK_GATE_MODEL_QPU_3 = {
    "deviceName": "Lucy",
    "deviceType": "QPU",
    "providerName": "OQC",
    "deviceStatus": "OFFLINE",
    "deviceCapabilities": MOCK_GATE_MODEL_QPU_CAPABILITIES_1.json(),
}

MOCK_DWAVE_QPU_CAPABILITIES_JSON = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.dwave.dwave_device_capabilities",
        "version": "1",
    },
    "provider": {
        "annealingOffsetStep": 1.45,
        "annealingOffsetStepPhi0": 1.45,
        "annealingOffsetRanges": [[1.45, 1.45], [1.45, 1.45]],
        "annealingDurationRange": [1, 2, 3],
        "couplers": [[1, 2], [2, 3]],
        "defaultAnnealingDuration": 1,
        "defaultProgrammingThermalizationDuration": 1,
        "defaultReadoutThermalizationDuration": 1,
        "extendedJRange": [1, 2, 3],
        "hGainScheduleRange": [1, 2, 3],
        "hRange": [1, 2, 3],
        "jRange": [1, 2, 3],
        "maximumAnnealingSchedulePoints": 1,
        "maximumHGainSchedulePoints": 1,
        "perQubitCouplingRange": [1, 2, 3],
        "programmingThermalizationDurationRange": [1, 2, 3],
        "qubits": [1, 2, 3],
        "qubitCount": 1,
        "quotaConversionRate": 1,
        "readoutThermalizationDurationRange": [1, 2, 3],
        "taskRunDurationRange": [1, 2, 3],
        "topology": {},
    },
    "service": {
        "executionWindows": [
            {"executionDay": "Everyday", "windowStartHour": "11:00", "windowEndHour": "12:00"}
        ],
        "shotsRange": [1, 10],
    },
    "action": {
        "braket.ir.annealing.problem": {
            "actionType": "braket.ir.annealing.problem",
            "version": ["1"],
        }
    },
    "deviceParameters": {},
}

MOCK_DWAVE_QPU_CAPABILITIES = DwaveDeviceCapabilities.parse_obj(MOCK_DWAVE_QPU_CAPABILITIES_JSON)


def test_d_wave_schema():
    validate(MOCK_DWAVE_QPU_CAPABILITIES_JSON, DwaveDeviceCapabilities.schema())


MOCK_DWAVE_QPU = {
    "deviceName": "Advantage_system1.1",
    "deviceType": "QPU",
    "providerName": "provider1",
    "deviceStatus": "ONLINE",
    "deviceCapabilities": MOCK_DWAVE_QPU_CAPABILITIES.json(),
}

MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES_JSON = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.simulators.gate_model_simulator_device_capabilities",
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
    "action": {
        "braket.ir.jaqcd.program": {
            "actionType": "braket.ir.jaqcd.program",
            "version": ["1"],
            "supportedOperations": ["H"],
        },
    },
    "paradigm": {"qubitCount": 30},
    "deviceParameters": {},
}

MOCK_GATE_MODEL_NOISE_SIMULATOR_CAPABILITIES_JSON = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.simulators.gate_model_simulator_device_capabilities",
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
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "version": ["1"],
            "supportedOperations": ["rx", "ry", "h", "cy", "cnot", "unitary"],
            "supportedResultTypes": [
                {
                    "name": "StateVector",
                    "observables": ["x", "y", "z"],
                    "minShots": 0,
                    "maxShots": 0,
                },
            ],
            "supportedPragmas": [
                "braket_noise_bit_flip",
                "braket_noise_depolarizing",
                "braket_noise_kraus",
                "braket_noise_pauli_channel",
                "braket_noise_generalized_amplitude_damping",
                "braket_noise_amplitude_damping",
                "braket_noise_phase_flip",
                "braket_noise_phase_damping",
                "braket_noise_two_qubit_dephasing",
                "braket_noise_two_qubit_depolarizing",
                "braket_unitary_matrix",
                "braket_result_type_sample",
                "braket_result_type_expectation",
                "braket_result_type_variance",
                "braket_result_type_probability",
                "braket_result_type_density_matrix",
            ],
        },
    },
    "paradigm": {"qubitCount": 30},
    "deviceParameters": {},
}

MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES = GateModelSimulatorDeviceCapabilities.parse_obj(
    MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES_JSON
)


def test_gate_model_sim_schema():
    validate(
        MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES_JSON, GateModelSimulatorDeviceCapabilities.schema()
    )


MOCK_GATE_MODEL_NOISE_SIMULATOR_CAPABILITIES = GateModelSimulatorDeviceCapabilities.parse_obj(
    MOCK_GATE_MODEL_NOISE_SIMULATOR_CAPABILITIES_JSON
)


def test_gate_model_sim_schema():
    validate(
        MOCK_GATE_MODEL_NOISE_SIMULATOR_CAPABILITIES_JSON,
        GateModelSimulatorDeviceCapabilities.schema(),
    )


MOCK_GATE_MODEL_SIMULATOR = {
    "deviceName": "SV1",
    "deviceType": "SIMULATOR",
    "providerName": "provider1",
    "deviceStatus": "ONLINE",
    "deviceCapabilities": MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES.json(),
}


MOCK_GATE_MODEL_NOISE_SIMULATOR = {
    "deviceName": "DM1",
    "deviceType": "SIMULATOR",
    "providerName": "provider1",
    "deviceStatus": "ONLINE",
    "deviceCapabilities": MOCK_GATE_MODEL_NOISE_SIMULATOR_CAPABILITIES.json(),
}


MOCK_DEFAULT_S3_DESTINATION_FOLDER = (
    "amazon-braket-us-test-1-00000000",
    "tasks",
)


@pytest.fixture(
    params=[
        "arn:aws:braket:us-west-1::device/quantum-simulator/amazon/sim",
        "arn:aws:braket:::device/quantum-simulator/amazon/sim",
    ]
)
def arn(request):
    return request.param


@pytest.fixture
def s3_destination_folder():
    return "bucket-foo", "key-bar"


@pytest.fixture
def bell_circuit():
    return Circuit().h(0)


@pytest.fixture
def openqasm_program():
    return OpenQasmProgram(source="OPENQASM 3.0; h $0;")


@pytest.fixture(params=["bell_circuit", "openqasm_program"])
def circuit(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def multiple_circuit_inputs():
    theta = FreeParameter("theta")
    beta = FreeParameter("beta")
    return Circuit().ry(angle=theta, target=0).rx(angle=beta, target=1)


@pytest.fixture()
def single_circuit_input():
    theta = FreeParameter("theta")
    return Circuit().ry(angle=theta, target=0)


@pytest.fixture
def aws_session():
    _boto_session = Mock()
    _boto_session.region_name = RIGETTI_REGION
    _boto_session.profile_name = "test-profile"

    creds = Mock()
    creds.method = "other"
    _boto_session.get_credentials.return_value = creds

    _aws_session = Mock()
    _aws_session.boto_session = _boto_session
    _aws_session._default_bucket = MOCK_DEFAULT_S3_DESTINATION_FOLDER[0]
    _aws_session.default_bucket.return_value = _aws_session._default_bucket
    _aws_session._custom_default_bucket = False
    _aws_session.account_id = "00000000"
    _aws_session.region = RIGETTI_REGION
    return _aws_session


@pytest.fixture
def device(aws_session):
    def _device(arn):
        aws_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
        aws_session.search_devices.return_value = [MOCK_GATE_MODEL_QPU_1]
        return AwsDevice(arn, aws_session)

    return _device


@pytest.mark.parametrize(
    "device_capabilities, get_device_data",
    [
        (MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES, MOCK_GATE_MODEL_SIMULATOR),
        (MOCK_GATE_MODEL_QPU_CAPABILITIES_1, MOCK_GATE_MODEL_QPU_1),
        (MOCK_DWAVE_QPU_CAPABILITIES, MOCK_DWAVE_QPU),
    ],
)
def test_device_aws_session(device_capabilities, get_device_data, arn):
    mock_session = Mock()
    mock_session.get_device.return_value = get_device_data
    mock_session.region = RIGETTI_REGION
    device = AwsDevice(arn, mock_session)
    _assert_device_fields(device, device_capabilities, get_device_data)
    assert device.aws_session == mock_session


@patch("braket.aws.aws_device.AwsSession")
def test_device_simulator_no_aws_session(aws_session_init, aws_session):
    arn = SV1_ARN
    aws_session_init.return_value = aws_session
    aws_session.get_device.return_value = MOCK_GATE_MODEL_SIMULATOR
    device = AwsDevice(arn)
    _assert_device_fields(device, MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES, MOCK_GATE_MODEL_SIMULATOR)
    aws_session.get_device.assert_called_with(arn)


@patch("braket.aws.aws_device.AwsSession.copy_session")
@patch("braket.aws.aws_device.AwsSession")
@pytest.mark.parametrize(
    "get_device_side_effect",
    [
        [MOCK_GATE_MODEL_QPU_1],
        [
            ClientError(
                {
                    "Error": {
                        "Code": "ResourceNotFoundException",
                    }
                },
                "getDevice",
            ),
            MOCK_GATE_MODEL_QPU_1,
        ],
    ],
)
def test_device_qpu_no_aws_session(
    aws_session_init, mock_copy_session, get_device_side_effect, aws_session
):
    arn = RIGETTI_ARN
    mock_session = Mock()
    mock_session.get_device.side_effect = get_device_side_effect
    aws_session.get_device.side_effect = ClientError(
        {
            "Error": {
                "Code": "ResourceNotFoundException",
            }
        },
        "getDevice",
    )
    aws_session_init.return_value = aws_session
    mock_copy_session.return_value = mock_session
    device = AwsDevice(arn)
    _assert_device_fields(device, MOCK_GATE_MODEL_QPU_CAPABILITIES_1, MOCK_GATE_MODEL_QPU_1)


@patch("braket.aws.aws_device.AwsSession.copy_session")
@patch("braket.aws.aws_device.AwsSession")
def test_regional_device_region_switch(aws_session_init, mock_copy_session, aws_session):
    device_region = "device-region"
    arn = f"arn:aws:braket:{device_region}::device/quantum-simulator/amazon/sim"
    aws_session_init.return_value = aws_session
    mock_session = Mock()
    mock_session.get_device.return_value = MOCK_GATE_MODEL_SIMULATOR
    mock_copy_session.return_value = mock_session
    device = AwsDevice(arn)
    aws_session.get_device.assert_not_called()
    mock_copy_session.assert_called_once()
    mock_copy_session.assert_called_with(aws_session, device_region)
    _assert_device_fields(device, MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES, MOCK_GATE_MODEL_SIMULATOR)


@patch("braket.aws.aws_device.AwsSession")
@pytest.mark.parametrize(
    "get_device_side_effect, expected_exception",
    [
        (
            [
                ClientError(
                    {
                        "Error": {
                            "Code": "ResourceNotFoundException",
                        }
                    },
                    "getDevice",
                )
            ],
            ValueError,
        ),
        (
            [
                ClientError(
                    {
                        "Error": {
                            "Code": "ThrottlingException",
                        }
                    },
                    "getDevice",
                )
            ],
            ClientError,
        ),
    ],
)
def test_regional_device_raises_error(
    aws_session_init, get_device_side_effect, expected_exception, aws_session
):
    arn = "arn:aws:braket:us-west-1::device/quantum-simulator/amazon/sim"
    aws_session.get_device.side_effect = get_device_side_effect
    aws_session_init.return_value = aws_session
    with pytest.raises(expected_exception):
        AwsDevice(arn)
        aws_session.get_device.assert_called_once()


def test_device_refresh_metadata(arn):
    mock_session = Mock()
    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    mock_session.region = RIGETTI_REGION
    device = AwsDevice(arn, mock_session)
    _assert_device_fields(device, MOCK_GATE_MODEL_QPU_CAPABILITIES_1, MOCK_GATE_MODEL_QPU_1)

    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_2
    device.refresh_metadata()
    _assert_device_fields(device, MOCK_GATE_MODEL_QPU_CAPABILITIES_2, MOCK_GATE_MODEL_QPU_2)


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
        }
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
        }
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
        "q0_ff": {
            "portId": "q0_ff",
            "direction": "tx",
            "portType": "ff",
            "dt": 1e-09,
            "qubitMappings": None,
            "centerFrequencies": [375000000.0],
            "qhpSpecificProperties": None,
        }
    },
    "nativeGateCalibrationssRef": "file://hostname/foo/bar",
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
        "deviceName": "M-2-Pulse",
        "deviceType": "QPU",
        "providerName": "Rigetti",
        "deviceStatus": "OFFLINE",
        "deviceCapabilities": device_obj.json(),
    }


@pytest.mark.parametrize(
    "pulse_device_capabilities",
    [
        MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_1,
        MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_2,
    ],
)
def test_device_pulse_metadata(pulse_device_capabilities):
    mock_session = Mock()
    mock_session.get_device.return_value = get_pulse_model(pulse_device_capabilities)
    mock_session.region = RIGETTI_REGION
    device = AwsDevice("arn:aws:braket:us-west-1::TestName", mock_session)
    assert device.ports == {"q0_ff": Port("q0_ff", 1e-9)}
    port = device.ports["q0_ff"]
    assert port.properties == pulse_device_capabilities["ports"]["q0_ff"]
    if "frames" in pulse_device_capabilities:
        assert device.frames == {
            "q0_q1_cphase_frame": Frame(
                "q0_q1_cphase_frame", Port("q0_ff", 1e-9), 4276236.85736918, 1.0
            )
        }
        frame = device.frames["q0_q1_cphase_frame"]
        assert frame.is_predefined is True
        assert frame.properties == pulse_device_capabilities["frames"]["q0_q1_cphase_frame"]
    else:
        assert device.frames == {}


def test_gate_calibration_refresh_no_url(arn):
    mock_session = Mock()
    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    mock_session.region = RIGETTI_REGION
    device = AwsDevice(arn, mock_session)

    assert device.refresh_gate_calibrations() is None


@patch("urllib.request.urlopen")
def test_device_gate_calibrations_exists(mock_url_request):
    # The data is accessed using a device manager so here data is prepped and passed for the return val.
    response_data_content = {
        "gates": {
            "0_1": {
                "cphaseshift": [
                    {
                        "name": "cphaseshift",
                        "qubits": ["0", "1"],
                        "arguments": ["-1.5707963267948966"],
                        "calibrations": [
                            {
                                "name": "play",
                                "arguments": [
                                    {
                                        "name": "waveform",
                                        "value": "wf_drag_gaussian_0",
                                        "type": "waveform",
                                    },
                                    {
                                        "name": "frame",
                                        "value": "q0_q1_cphase_frame",
                                        "type": "frame",
                                    },
                                ],
                            },
                        ],
                    }
                ],
                "rx_12": [{"name": "rx_12", "qubits": ["0"]}],
            },
        },
        "waveforms": {
            "wf_drag_gaussian_0": {
                "waveformId": "wf_drag_gaussian_0",
                "name": "drag_gaussian",
                "arguments": [
                    {"name": "length", "value": 6.000000000000001e-8, "type": "float"},
                    {"name": "sigma", "value": 6.369913502160144e-9, "type": "float"},
                    {"name": "amplitude", "value": -0.4549282253548838, "type": "float"},
                    {"name": "beta", "value": 7.494904522022295e-10, "type": "float"},
                ],
            },
        },
    }

    response_data_stream = io.BytesIO(json.dumps(response_data_content).encode("utf-8"))
    mock_url_request.return_value.__enter__.return_value = response_data_stream
    mock_session = Mock()
    mock_session.get_device.return_value = get_pulse_model(
        MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_1
    )
    device = AwsDevice(RIGETTI_ARN, mock_session)

    expected_waveforms = {
        "wf_drag_gaussian_0": DragGaussianWaveform(
            length=6.000000000000001e-8,
            sigma=6.369913502160144e-9,
            amplitude=-0.4549282253548838,
            beta=7.494904522022295e-10,
            id="wf_drag_gaussian_0",
        )
    }
    expected_ngc = GateCalibrations(
        pulse_sequences={
            (Gate.CPhaseShift(-1.5707963267948966), QubitSet([0, 1])): PulseSequence().play(
                device.frames["q0_q1_cphase_frame"], expected_waveforms["wf_drag_gaussian_0"]
            )
        }
    )
    assert device.gate_calibrations == expected_ngc
    # Called twice to check that the property stays the same after being initially fetched
    assert device.gate_calibrations == expected_ngc


@pytest.mark.xfail(raises=URLError)
@patch("urllib.request.urlopen")
def test_refresh_data_url_error(mock_url_request):
    mock_url_request.side_effect = URLError("mock reason")
    mock_session = Mock()
    mock_session.get_device.return_value = get_pulse_model(
        MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_1
    )
    device = AwsDevice(RIGETTI_ARN, mock_session)

    device.gate_calibrations


def test_equality(arn):
    mock_session = Mock()
    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    mock_session.region = RIGETTI_REGION
    device_1 = AwsDevice(arn, mock_session)
    device_2 = AwsDevice(arn, mock_session)
    other_device = AwsDevice("arn:aws:braket:::device/quantum-simulator/amazon/bar", mock_session)
    non_device = "HI"

    assert device_1 == device_2
    assert device_1 is not device_2
    assert device_1 != other_device
    assert device_1 != non_device


def test_repr(arn):
    mock_session = Mock()
    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    mock_session.region = RIGETTI_REGION
    device = AwsDevice(arn, mock_session)
    expected = f"Device('name': {device.name}, 'arn': {device.arn})"
    assert repr(device) == expected


def test_device_simulator_not_found():
    mock_session = Mock()
    mock_session.region = "test-region-1"
    mock_session.get_device.side_effect = ClientError(
        {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": (
                    "Braket device 'arn:aws:braket:::device/quantum-simulator/amazon/tn1' "
                    "not found in us-west-1. You can find a list of all supported device "
                    "ARNs and the regions in which they are available in the documentation: "
                    "https://docs.aws.amazon.com/braket/latest/developerguide/braket-devices.html"
                ),
            }
        },
        "getDevice",
    )
    simulator_not_found = (
        "Simulator 'arn:aws:braket:::device/simulator/a/b' not found in 'test-region-1'"
    )
    with pytest.raises(ValueError, match=simulator_not_found):
        AwsDevice("arn:aws:braket:::device/simulator/a/b", mock_session)


@patch("braket.aws.aws_device.AwsSession.copy_session")
def test_device_qpu_not_found(mock_copy_session):
    mock_session = Mock()
    mock_session.get_device.side_effect = ClientError(
        {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": (
                    "Braket device 'arn:aws:braket:::device/quantum-simulator/amazon/tn1' "
                    "not found in us-west-1. You can find a list of all supported device "
                    "ARNs and the regions in which they are available in the documentation: "
                    "https://docs.aws.amazon.com/braket/latest/developerguide/braket-devices.html"
                ),
            }
        },
        "getDevice",
    )
    mock_copy_session.return_value = mock_session
    qpu_not_found = "QPU 'arn:aws:braket:::device/qpu/a/b' not found"
    with pytest.raises(ValueError, match=qpu_not_found):
        AwsDevice("arn:aws:braket:::device/qpu/a/b", mock_session)


@patch("braket.aws.aws_device.AwsSession.copy_session")
def test_device_qpu_exception(mock_copy_session):
    mock_session = Mock()
    mock_session.get_device.side_effect = (
        ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": (
                        "Braket device 'arn:aws:braket:::device/quantum-simulator/amazon/tn1' "
                        "not found in us-west-1. You can find a list of all supported device "
                        "ARNs and the regions in which they are available in the documentation: "
                        "https://docs.aws.amazon.com/braket/latest/developerguide/braket-"
                        "devices.html"
                    ),
                }
            },
            "getDevice",
        ),
        ClientError(
            {
                "Error": {
                    "Code": "OtherException",
                    "Message": "Some other message",
                }
            },
            "getDevice",
        ),
    )
    mock_copy_session.return_value = mock_session
    qpu_exception = (
        "An error occurred \\(OtherException\\) when calling the "
        "getDevice operation: Some other message"
    )
    with pytest.raises(ClientError, match=qpu_exception):
        AwsDevice("arn:aws:braket:::device/qpu/a/b", mock_session)


@patch("braket.aws.aws_device.AwsSession.copy_session")
def test_device_non_qpu_region_error(mock_copy_session):
    mock_session = Mock()
    mock_session.get_device.side_effect = ClientError(
        {
            "Error": {
                "Code": "ExpiredTokenError",
                "Message": ("Some other error that isn't ResourceNotFoundException"),
            }
        },
        "getDevice",
    )
    mock_copy_session.return_value = mock_session
    expired_token = (
        "An error occurred \\(ExpiredTokenError\\) when calling the getDevice operation: "
        "Some other error that isn't ResourceNotFoundException"
    )
    with pytest.raises(ClientError, match=expired_token):
        AwsDevice("arn:aws:braket:::device/qpu/a/b", mock_session)


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_no_extra(aws_quantum_task_mock, device, circuit):
    _run_and_assert(
        aws_quantum_task_mock,
        device,
        circuit,
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_reservation_arn(aws_quantum_task_mock, device, circuit):
    _run_and_assert(
        aws_quantum_task_mock,
        device,
        circuit,
        reservation_arn="arn:aws:braket:us-west-2:123456789123:reservation/a1b123cd-45e6-789f-gh01-i234567jk8l9",
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask")
def test_run_param_circuit_with_no_inputs(
    aws_quantum_task_mock, single_circuit_input, device, s3_destination_folder
):
    cannot_execute_with_unbound = "Cannot execute circuit with unbound parameters: {'theta'}"

    with pytest.raises(ValueError, match=cannot_execute_with_unbound):
        _run_and_assert(
            aws_quantum_task_mock,
            device,
            single_circuit_input,
            s3_destination_folder,
            10,
            86400,
            0.25,
            {},
        )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_param_circuit_with_inputs(
    aws_quantum_task_mock, single_circuit_input, device, s3_destination_folder
):
    inputs = {"theta": 0.2}

    _run_and_assert(
        aws_quantum_task_mock,
        device,
        single_circuit_input,
        s3_destination_folder,
        10,
        86400,
        0.25,
        inputs,
    )


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_param_circuit_with_reservation_arn_batch_task(
    aws_quantum_task_mock,
    aws_session_mock,
    boto_session_mock,
    single_circuit_input,
    device,
    s3_destination_folder,
):
    inputs = {"theta": 0.2}
    circ_1 = Circuit().rx(angle=0.2, target=0)
    circuits = [circ_1, single_circuit_input]

    _run_batch_and_assert(
        aws_quantum_task_mock,
        aws_session_mock,
        device,
        circuits,
        s3_destination_folder,
        10,
        20,
        50,
        43200,
        0.25,
        inputs,
        {},
        reservation_arn="arn:aws:braket:us-west-2:123456789123:reservation/a1b123cd-45e6-789f-gh01-i234567jk8l9",
    )


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_param_circuit_with_inputs_batch_task(
    aws_quantum_task_mock,
    aws_session_mock,
    boto_session_mock,
    single_circuit_input,
    device,
    s3_destination_folder,
):
    inputs = {"theta": 0.2}
    circ_1 = Circuit().rx(angle=0.2, target=0)
    circuits = [circ_1, single_circuit_input]

    _run_batch_and_assert(
        aws_quantum_task_mock,
        aws_session_mock,
        device,
        circuits,
        s3_destination_folder,
        10,
        20,
        50,
        43200,
        0.25,
        inputs,
        {},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask")
def test_run_param_circuit_with_invalid_input(
    aws_quantum_task_mock, single_circuit_input, device, s3_destination_folder
):
    inputs = {"beta": 0.2}
    cannot_execute_with_unbound = "Cannot execute circuit with unbound parameters: {'theta'}"
    with pytest.raises(ValueError, match=cannot_execute_with_unbound):
        _run_and_assert(
            aws_quantum_task_mock,
            device,
            single_circuit_input,
            s3_destination_folder,
            10,
            86400,
            0.25,
            inputs,
        )


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_batch_param_circuit_with_no_inputs(
    aws_quantum_task_mock,
    aws_session_mock,
    boto_session_mock,
    single_circuit_input,
    device,
    s3_destination_folder,
):
    circ_1 = Circuit().ry(angle=3, target=0)
    circuits = [circ_1, single_circuit_input]

    cannot_execute_with_unbound = "Cannot execute circuit with unbound parameters: {'theta'}"

    with pytest.raises(ValueError, match=cannot_execute_with_unbound):
        _run_batch_and_assert(
            aws_quantum_task_mock,
            aws_session_mock,
            device,
            circuits,
            s3_destination_folder,
            1000,
            20,
            50,
            43200,
            0.25,
            {},
        )


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task_batch.AwsQuantumTask.create")
def test_run_multi_param_batch_circuit_with_input(
    aws_quantum_task_mock,
    aws_session_mock,
    boto_session_mock,
    multiple_circuit_inputs,
    device,
    s3_destination_folder,
):
    inputs = {"beta": 0.2}
    circ_1 = Circuit().ry(angle=3, target=0)
    circuits = [circ_1, multiple_circuit_inputs]

    cannot_execute_with_unbound = "Cannot execute circuit with unbound parameters: {'theta'}"
    with pytest.raises(ValueError, match=cannot_execute_with_unbound):
        _run_batch_and_assert(
            aws_quantum_task_mock,
            aws_session_mock,
            device,
            circuits,
            s3_destination_folder,
            1000,
            20,
            50,
            43200,
            0.25,
            inputs,
        )


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_param_batch_circuit_with_invalid_input(
    aws_quantum_task_mock,
    aws_session_mock,
    boto_session_mock,
    single_circuit_input,
    aws_session,
    device,
    s3_destination_folder,
):
    inputs = {"beta": 0.2}
    circ_1 = Circuit().ry(angle=3, target=0)
    circuits = [circ_1, single_circuit_input]
    cannot_execute_with_unbound = "Cannot execute circuit with unbound parameters: {'theta'}"
    with pytest.raises(ValueError, match=cannot_execute_with_unbound):
        _run_batch_and_assert(
            aws_quantum_task_mock,
            aws_session_mock,
            device,
            circuits,
            s3_destination_folder,
            1000,
            20,
            50,
            43200,
            0.25,
            inputs,
        )


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_batch_circuit_with_task_and_input_mismatch(
    aws_quantum_task_mock,
    aws_session_mock,
    boto_session_mock,
    single_circuit_input,
    openqasm_program,
    device,
    s3_destination_folder,
):
    inputs = [{"beta": 0.2}, {"gamma": 0.1}, {"theta": 0.2}]
    circ_1 = Circuit().ry(angle=3, target=0)
    task_specifications = [[circ_1, single_circuit_input], openqasm_program]
    wrong_number_of_inputs = (
        "Multiple inputs, task specifications and gate definitions must be equal in length."
    )

    with pytest.raises(ValueError, match=wrong_number_of_inputs):
        _run_batch_and_assert(
            aws_quantum_task_mock,
            aws_session_mock,
            device,
            task_specifications,
            s3_destination_folder,
            1000,
            20,
            50,
            43200,
            0.25,
            inputs,
            {},
        )


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_multiple_task_multiple_batch_inputs_invalid_config(
    aws_quantum_task_mock, aws_session_mock, boto_session_mock, device, s3_destination_folder
):
    theta = FreeParameter("theta")
    multiple_task = [Circuit().rx(angle=theta, target=1)] * 2
    multiple_inputs = [{"theta": 0.2}, {"beta": 0.3}]
    cannot_execute_with_unbound = "Cannot execute circuit with unbound parameters: {'theta'}"
    with pytest.raises(ValueError, match=cannot_execute_with_unbound):
        _run_batch_and_assert(
            aws_quantum_task_mock,
            aws_session_mock,
            device,
            multiple_task,
            s3_destination_folder,
            1000,
            20,
            50,
            43200,
            0.25,
            multiple_inputs,
        )


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_single_task_single_input_batch_missing_input(
    aws_quantum_task_mock, aws_session_mock, boto_session_mock, device, s3_destination_folder
):
    theta = FreeParameter("theta")
    task = Circuit().rx(angle=theta, target=0)
    inputs = {"beta": 0.2}
    cannot_execute_with_unbound = "Cannot execute circuit with unbound parameters: {'theta'}"
    with pytest.raises(ValueError, match=cannot_execute_with_unbound):
        _run_batch_and_assert(
            aws_quantum_task_mock,
            aws_session_mock,
            device,
            task,
            s3_destination_folder,
            1000,
            20,
            50,
            43200,
            0.25,
            inputs,
        )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_positional_args(aws_quantum_task_mock, device, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock,
        device,
        circuit,
        s3_destination_folder,
        100,
        86400,
        0.25,
        ["foo"],
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_kwargs(aws_quantum_task_mock, device, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock,
        device,
        circuit,
        s3_destination_folder,
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_shots(aws_quantum_task_mock, device, circuit, s3_destination_folder):
    _run_and_assert(aws_quantum_task_mock, device, circuit, s3_destination_folder, 100)


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_shots_kwargs(aws_quantum_task_mock, device, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock,
        device,
        circuit,
        s3_destination_folder,
        100,
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_default_bucket_not_called(aws_quantum_task_mock, device, circuit, s3_destination_folder):
    device = device(RIGETTI_ARN)
    run_and_assert(
        aws_quantum_task_mock,
        device,
        MOCK_DEFAULT_S3_DESTINATION_FOLDER,
        AwsDevice.DEFAULT_SHOTS_QPU,
        AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        circuit,
        s3_destination_folder,
        shots=None,
        poll_timeout_seconds=None,
        poll_interval_seconds=None,
        inputs=None,
        gate_definitions=None,
        reservation_arn=None,
        extra_args=None,
        extra_kwargs=None,
    )
    device._aws_session.default_bucket.assert_not_called()


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_device_poll_interval_kwargs(
    aws_quantum_task_mock, aws_session, circuit, s3_destination_folder
):
    poll_interval_seconds = 200
    capabilities = MOCK_GATE_MODEL_QPU_CAPABILITIES_1
    capabilities.service.getTaskPollIntervalMillis = poll_interval_seconds
    properties = {
        "deviceName": "Ankaa-2",
        "deviceType": "QPU",
        "providerName": "provider1",
        "deviceStatus": "OFFLINE",
        "deviceCapabilities": capabilities.json(),
    }
    aws_session.get_device.return_value = properties
    _run_and_assert(
        aws_quantum_task_mock,
        lambda arn: AwsDevice(arn, aws_session),
        circuit,
        s3_destination_folder,
        100,
        86400,
        poll_interval_seconds / 1000.0,
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_shots_poll_timeout_kwargs(
    aws_quantum_task_mock, device, circuit, s3_destination_folder
):
    _run_and_assert(
        aws_quantum_task_mock,
        device,
        circuit,
        s3_destination_folder,
        100,
        86400,
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_positional_args_and_kwargs(
    aws_quantum_task_mock, device, circuit, s3_destination_folder
):
    _run_and_assert(
        aws_quantum_task_mock,
        device,
        circuit,
        s3_destination_folder,
        100,
        86400,
        0.25,
        {},
        {},
        "arn:aws:braket:us-west-2:123456789123:reservation/a1b123cd-45e6-789f-gh01-i234567jk8l9",
        None,
        {"bar": 1, "baz": 2},
    )


@patch.dict(
    os.environ,
    {"AMZN_BRAKET_TASK_RESULTS_S3_URI": "s3://env_bucket/env/path"},
)
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_env_variables(aws_quantum_task_mock, device, circuit, arn):
    device(arn).run(circuit)
    assert aws_quantum_task_mock.call_args_list[0][0][3] == ("env_bucket", "env/path")


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_batch_no_extra(
    aws_quantum_task_mock,
    aws_session_mock,
    boto_session_mock,
    device,
    circuit,
    s3_destination_folder,
):
    _run_batch_and_assert(
        aws_quantum_task_mock,
        aws_session_mock,
        device,
        [circuit for _ in range(10)],
        s3_destination_folder,
        1000,
        20,
        50,
        43200,
        0.25,
        {},
        {},
    )


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_batch_with_shots(
    aws_quantum_task_mock,
    aws_session_mock,
    boto_session_mock,
    device,
    circuit,
    s3_destination_folder,
):
    _run_batch_and_assert(
        aws_quantum_task_mock,
        aws_session_mock,
        device,
        [circuit for _ in range(10)],
        s3_destination_folder,
        1000,
        20,
        50,
        43200,
        0.25,
        {},
        {},
    )


@patch("braket.aws.aws_session.boto3.Session")
@patch("braket.aws.aws_session.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_batch_with_max_parallel_and_kwargs(
    aws_quantum_task_mock,
    aws_session_mock,
    boto_session_mock,
    device,
    circuit,
    s3_destination_folder,
):
    _run_batch_and_assert(
        aws_quantum_task_mock,
        aws_session_mock,
        device,
        [circuit for _ in range(10)],
        s3_destination_folder,
        1000,
        20,
        50,
        43200,
        0.25,
        inputs={"theta": 0.2},
        gate_definitions={},
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_session.boto3.Session")
@patch.dict(
    os.environ,
    {"AMZN_BRAKET_TASK_RESULTS_S3_URI": "s3://env_bucket/env/path"},
)
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_batch_env_variables(aws_quantum_task_mock, boto_session_mock, device, circuit, arn):
    device(arn).run_batch([circuit])
    assert aws_quantum_task_mock.call_args_list[0][0][3] == ("env_bucket", "env/path")


def _run_and_assert(
    aws_quantum_task_mock,
    device_factory,
    circuit,
    s3_destination_folder=None,  # Treated as positional arg
    shots=None,  # Treated as positional arg
    poll_timeout_seconds=None,  # Treated as positional arg
    poll_interval_seconds=None,  # Treated as positional arg
    inputs=None,  # Treated as positional arg
    gate_definitions=None,  # Treated as positional arg
    reservation_arn=None,  # Treated as positional arg
    extra_args=None,
    extra_kwargs=None,
):
    run_and_assert(
        aws_quantum_task_mock,
        device_factory("arn:aws:braket:::device/quantum-simulator/amazon/sim"),
        MOCK_DEFAULT_S3_DESTINATION_FOLDER,
        AwsDevice.DEFAULT_SHOTS_SIMULATOR,
        AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        circuit,
        s3_destination_folder,
        shots,
        poll_timeout_seconds,
        poll_interval_seconds,
        inputs,
        gate_definitions,
        reservation_arn,
        extra_args,
        extra_kwargs,
    )


def _run_batch_and_assert(
    aws_quantum_task_mock,
    aws_session_mock,
    device_factory,
    circuits,
    s3_destination_folder=None,  # Treated as positional arg
    shots=None,  # Treated as positional arg
    max_parallel=None,  # Treated as positional arg
    max_connections=None,  # Treated as positional arg
    poll_timeout_seconds=None,  # Treated as a positional arg
    poll_interval_seconds=None,  # Treated as positional arg
    inputs=None,  # Treated as positional arg
    gate_definitions=None,  # Treated as positional arg
    reservation_arn=None,  # Treated as positional arg
    extra_args=None,
    extra_kwargs=None,
):
    run_batch_and_assert(
        aws_quantum_task_mock,
        aws_session_mock,
        device_factory("arn:aws:braket:::device/quantum-simulator/amazon/sim"),
        MOCK_DEFAULT_S3_DESTINATION_FOLDER,
        AwsDevice.DEFAULT_SHOTS_SIMULATOR,
        AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        circuits,
        s3_destination_folder,
        shots,
        max_parallel,
        max_connections,
        poll_timeout_seconds,
        poll_interval_seconds,
        inputs,
        gate_definitions,
        reservation_arn,
        extra_args,
        extra_kwargs,
    )


def _assert_device_fields(device, expected_properties, expected_device_data):
    assert device.name == expected_device_data.get("deviceName")
    assert device.properties == expected_properties
    assert device.status == expected_device_data.get("deviceStatus")
    assert device.provider_name == expected_device_data.get("providerName")
    assert device.type == AwsDeviceType(expected_device_data.get("deviceType"))
    if device.topology_graph:
        assert device.topology_graph.edges == device._construct_topology_graph().edges
    assert device.frames == {}
    assert device.ports == {}


@patch("braket.aws.aws_device.AwsSession.copy_session")
def test_get_devices(mock_copy_session, aws_session):
    aws_session.search_devices.side_effect = [
        # us-west-1
        [
            {
                "deviceArn": SV1_ARN,
                "deviceName": "SV1",
                "deviceType": "SIMULATOR",
                "deviceStatus": "ONLINE",
                "providerName": "Amazon Braket",
            }
        ],
        ValueError("should not be reachable"),
    ]
    aws_session.get_device.side_effect = [
        MOCK_GATE_MODEL_SIMULATOR,
        ValueError("should not be reachable"),
    ]
    session_for_region = Mock()
    session_for_region.search_devices.side_effect = [
        # us-east-1
        [
            {
                "deviceArn": IONQ_ARN,
                "deviceName": "IonQ Device",
                "deviceType": "QPU",
                "deviceStatus": "ONLINE",
                "providerName": "IonQ",
            },
        ],
        # us-west-2
        [
            {
                "deviceArn": DWAVE_ARN,
                "deviceName": "Advantage_system1.1",
                "deviceType": "QPU",
                "deviceStatus": "ONLINE",
                "providerName": "D-Wave",
            },
            # Should not be reached because already instantiated in us-west-1
            {
                "deviceArn": SV1_ARN,
                "deviceName": "SV1",
                "deviceType": "SIMULATOR",
                "deviceStatus": "ONLINE",
                "providerName": "Amazon Braket",
            },
        ],
        # eu-west-2
        [
            {
                "deviceArn": OQC_ARN,
                "deviceName": "Lucy",
                "deviceType": "QPU",
                "deviceStatus": "ONLINE",
                "providerName": "OQC",
            }
        ],
        # eu-north-1
        [
            {
                "deviceArn": SV1_ARN,
                "deviceName": "SV1",
                "deviceType": "SIMULATOR",
                "deviceStatus": "ONLINE",
                "providerName": "Amazon Braket",
            },
        ],
        # Only two regions to search outside of current
        ValueError("should not be reachable"),
    ]
    session_for_region.get_device.side_effect = [
        MOCK_DWAVE_QPU,
        MOCK_GATE_MODEL_QPU_2,
        MOCK_GATE_MODEL_QPU_3,
        ValueError("should not be reachable"),
    ]
    mock_copy_session.return_value = session_for_region
    # Search order: us-east-1, us-west-1, us-west-2, eu-west-2, eu-north-1
    results = AwsDevice.get_devices(
        arns=[SV1_ARN, DWAVE_ARN, IONQ_ARN, OQC_ARN],
        provider_names=["Amazon Braket", "D-Wave", "IonQ", "OQC"],
        statuses=["ONLINE"],
        aws_session=aws_session,
    )
    assert [result.name for result in results] == ["Advantage_system1.1", "Blah", "Lucy", "SV1"]


@patch("braket.aws.aws_device.AwsSession.copy_session")
def test_get_devices_simulators_only(mock_copy_session, aws_session):
    aws_session.search_devices.side_effect = [
        [
            {
                "deviceArn": SV1_ARN,
                "deviceName": "SV1",
                "deviceType": "SIMULATOR",
                "deviceStatus": "ONLINE",
                "providerName": "Amazon Braket",
            }
        ],
        ValueError("should not be reachable"),
    ]
    aws_session.get_device.side_effect = [
        MOCK_GATE_MODEL_SIMULATOR,
        ValueError("should not be reachable"),
    ]
    session_for_region = Mock()
    session_for_region.search_devices.side_effect = ValueError("should not be reachable")
    session_for_region.get_device.side_effect = ValueError("should not be reachable")
    mock_copy_session.return_value = session_for_region
    results = AwsDevice.get_devices(
        arns=[SV1_ARN, TN1_ARN],
        types=["SIMULATOR"],
        provider_names=["Amazon Braket"],
        statuses=["ONLINE"],
        aws_session=aws_session,
    )
    # Only one region should be searched
    assert [result.name for result in results] == ["SV1"]


@pytest.mark.filterwarnings("ignore:Test Code:")
@patch("braket.aws.aws_device.AwsSession.copy_session")
def test_get_devices_with_error_in_region(mock_copy_session, aws_session):
    aws_session.search_devices.side_effect = [
        # us-west-1
        [
            {
                "deviceArn": SV1_ARN,
                "deviceName": "SV1",
                "deviceType": "SIMULATOR",
                "deviceStatus": "ONLINE",
                "providerName": "Amazon Braket",
            }
        ],
        ValueError("should not be reachable"),
    ]
    aws_session.get_device.side_effect = [
        MOCK_GATE_MODEL_SIMULATOR,
        ValueError("should not be reachable"),
    ]
    session_for_region = Mock()
    session_for_region.search_devices.side_effect = [
        # us-east-1
        [
            {
                "deviceArn": IONQ_ARN,
                "deviceName": "IonQ Device",
                "deviceType": "QPU",
                "deviceStatus": "ONLINE",
                "providerName": "IonQ",
            },
        ],
        # us-west-2
        ClientError(
            {
                "Error": {
                    "Code": "Test Code",
                    "Message": "Test Message",
                }
            },
            "Test Operation",
        ),
        # eu-west-2
        [
            {
                "deviceArn": OQC_ARN,
                "deviceName": "Lucy",
                "deviceType": "QPU",
                "deviceStatus": "ONLINE",
                "providerName": "OQC",
            }
        ],
        # eu-north-1
        [
            {
                "deviceArn": SV1_ARN,
                "deviceName": "SV1",
                "deviceType": "SIMULATOR",
                "deviceStatus": "ONLINE",
                "providerName": "Amazon Braket",
            },
        ],
        # Only two regions to search outside of current
        ValueError("should not be reachable"),
    ]
    session_for_region.get_device.side_effect = [
        MOCK_GATE_MODEL_QPU_2,
        MOCK_GATE_MODEL_QPU_3,
        ValueError("should not be reachable"),
    ]
    mock_copy_session.return_value = session_for_region
    # Search order: us-east-1, us-west-1, us-west-2, eu-west-2, eu-north-1
    results = AwsDevice.get_devices(
        statuses=["ONLINE"],
        aws_session=aws_session,
    )
    assert [result.name for result in results] == ["Blah", "Lucy", "SV1"]


@pytest.mark.xfail(raises=ValueError)
def test_get_devices_invalid_order_by():
    AwsDevice.get_devices(order_by="foo")


@patch("braket.aws.aws_device.datetime")
def test_get_device_availability(mock_utc_now):
    class Expando:
        pass

    class MockDevice(AwsDevice):
        def __init__(self, status, *execution_window_args):
            self._status = status
            self._properties = Expando()
            self._properties.service = Expando()
            execution_windows = [
                DeviceExecutionWindow.parse_raw(
                    json.dumps({
                        "executionDay": execution_day,
                        "windowStartHour": window_start_hour,
                        "windowEndHour": window_end_hour,
                    })
                )
                for execution_day, window_start_hour, window_end_hour in execution_window_args
            ]
            self._properties.service.executionWindows = execution_windows

    test_sets = (
        {
            "test_devices": (
                ("always_on_device", MockDevice("ONLINE", ("Everyday", "00:00", "23:59:59"))),
                ("offline_device", MockDevice("OFFLINE", ("Everyday", "00:00", "23:59:59"))),
                ("retired_device", MockDevice("RETIRED", ("Everyday", "00:00", "23:59:59"))),
                ("missing_schedule_device", MockDevice("ONLINE")),
            ),
            "test_items": (
                (datetime(2021, 12, 6, 10, 0, 0), (1, 0, 0, 0)),
                (datetime(2021, 12, 7, 10, 0, 0), (1, 0, 0, 0)),
                (datetime(2021, 12, 8, 10, 0, 0), (1, 0, 0, 0)),
                (datetime(2021, 12, 9, 10, 0, 0), (1, 0, 0, 0)),
                (datetime(2021, 12, 10, 10, 0, 0), (1, 0, 0, 0)),
                (datetime(2021, 12, 11, 10, 0, 0), (1, 0, 0, 0)),
                (datetime(2021, 12, 12, 10, 0, 0), (1, 0, 0, 0)),
            ),
        },
        {
            "test_devices": (
                ("midday_everyday_device", MockDevice("ONLINE", ("Everyday", "07:00", "17:00"))),
                ("midday_weekday_device", MockDevice("ONLINE", ("Weekdays", "07:00", "17:00"))),
                ("midday_weekend_device", MockDevice("ONLINE", ("Weekend", "07:00", "17:00"))),
                ("evening_everyday_device", MockDevice("ONLINE", ("Everyday", "17:00", "07:00"))),
                ("evening_weekday_device", MockDevice("ONLINE", ("Weekdays", "17:00", "07:00"))),
                ("evening_weekend_device", MockDevice("ONLINE", ("Weekend", "17:00", "07:00"))),
            ),
            "test_items": (
                (datetime(2021, 12, 6, 5, 0, 0), (0, 0, 0, 1, 0, 1)),
                (datetime(2021, 12, 6, 10, 0, 0), (1, 1, 0, 0, 0, 0)),
                (datetime(2021, 12, 6, 20, 0, 0), (0, 0, 0, 1, 1, 0)),
                (datetime(2021, 12, 7, 5, 0, 0), (0, 0, 0, 1, 1, 0)),
                (datetime(2021, 12, 7, 10, 0, 0), (1, 1, 0, 0, 0, 0)),
                (datetime(2021, 12, 7, 20, 0, 0), (0, 0, 0, 1, 1, 0)),
                (datetime(2021, 12, 8, 5, 0, 0), (0, 0, 0, 1, 1, 0)),
                (datetime(2021, 12, 8, 10, 0, 0), (1, 1, 0, 0, 0, 0)),
                (datetime(2021, 12, 8, 20, 0, 0), (0, 0, 0, 1, 1, 0)),
                (datetime(2021, 12, 9, 5, 0, 0), (0, 0, 0, 1, 1, 0)),
                (datetime(2021, 12, 9, 10, 0, 0), (1, 1, 0, 0, 0, 0)),
                (datetime(2021, 12, 9, 20, 0, 0), (0, 0, 0, 1, 1, 0)),
                (datetime(2021, 12, 10, 5, 0, 0), (0, 0, 0, 1, 1, 0)),
                (datetime(2021, 12, 10, 10, 0, 0), (1, 1, 0, 0, 0, 0)),
                (datetime(2021, 12, 10, 20, 0, 0), (0, 0, 0, 1, 1, 0)),
                (datetime(2021, 12, 11, 5, 0, 0), (0, 0, 0, 1, 1, 0)),
                (datetime(2021, 12, 11, 10, 0, 0), (1, 0, 1, 0, 0, 0)),
                (datetime(2021, 12, 11, 20, 0, 0), (0, 0, 0, 1, 0, 1)),
                (datetime(2021, 12, 12, 5, 0, 0), (0, 0, 0, 1, 0, 1)),
                (datetime(2021, 12, 12, 10, 0, 0), (1, 0, 1, 0, 0, 0)),
                (datetime(2021, 12, 12, 20, 0, 0), (0, 0, 0, 1, 0, 1)),
            ),
        },
        {
            "test_devices": (
                ("monday_device", MockDevice("ONLINE", ("Monday", "07:00", "17:00"))),
                ("tuesday_device", MockDevice("ONLINE", ("Tuesday", "07:00", "17:00"))),
                ("wednesday_device", MockDevice("ONLINE", ("Wednesday", "07:00", "17:00"))),
                ("thursday_device", MockDevice("ONLINE", ("Thursday", "07:00", "17:00"))),
                ("friday_device", MockDevice("ONLINE", ("Friday", "07:00", "17:00"))),
                ("saturday_device", MockDevice("ONLINE", ("Saturday", "07:00", "17:00"))),
                ("sunday_device", MockDevice("ONLINE", ("Sunday", "07:00", "17:00"))),
                (
                    "monday_friday_device",
                    MockDevice(
                        "ONLINE", ("Monday", "07:00", "17:00"), ("Friday", "07:00", "17:00")
                    ),
                ),
            ),
            "test_items": (
                (datetime(2021, 12, 6, 5, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 6, 10, 0, 0), (1, 0, 0, 0, 0, 0, 0, 1)),
                (datetime(2021, 12, 6, 20, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 7, 5, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 7, 10, 0, 0), (0, 1, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 7, 20, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 8, 5, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 8, 10, 0, 0), (0, 0, 1, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 8, 20, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 9, 5, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 9, 10, 0, 0), (0, 0, 0, 1, 0, 0, 0, 0)),
                (datetime(2021, 12, 9, 20, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 10, 5, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 10, 10, 0, 0), (0, 0, 0, 0, 1, 0, 0, 1)),
                (datetime(2021, 12, 10, 20, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 11, 5, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 11, 10, 0, 0), (0, 0, 0, 0, 0, 1, 0, 0)),
                (datetime(2021, 12, 11, 20, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 12, 5, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
                (datetime(2021, 12, 12, 10, 0, 0), (0, 0, 0, 0, 0, 0, 1, 0)),
                (datetime(2021, 12, 12, 20, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
            ),
        },
    )

    for test_set in test_sets:
        for test_item in test_set["test_items"]:
            test_date = test_item[0]
            mock_utc_now.now.return_value = test_date

            # flake8: noqa: C501
            for i in range(len(test_item[1])):
                device_name = test_set["test_devices"][i][0]
                device = test_set["test_devices"][i][1]
                type(device).properties = PropertyMock(return_value=Expando())
                type(device).properties.service = PropertyMock(return_value=Expando())
                device.properties.service.executionWindows = (
                    device._properties.service.executionWindows
                )
                expected = bool(test_item[1][i])
                actual = device.is_available
                assert expected == actual, (
                    f"device_name: {device_name}, test_date: {test_date}, expected: {expected}, actual: {actual}"
                )


@pytest.mark.parametrize(
    "get_device_data, expected_graph",
    [
        (MOCK_GATE_MODEL_QPU_1, nx.DiGraph([(1, 2), (1, 3)])),
        (MOCK_GATE_MODEL_QPU_2, nx.complete_graph(30, nx.DiGraph())),
        (MOCK_DWAVE_QPU, nx.DiGraph([(1, 2), (2, 3)])),
    ],
)
def test_device_topology_graph_data(get_device_data, expected_graph, arn):
    mock_session = Mock()
    mock_session.get_device.return_value = get_device_data
    mock_session.region = RIGETTI_REGION
    device = AwsDevice(arn, mock_session)
    assert nx.is_isomorphic(device.topology_graph, expected_graph)
    new_val = "new_val"
    device._topology_graph = new_val
    assert device.topology_graph == new_val


def test_device_no_href():
    mock_session = Mock()
    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    AwsDevice(DWAVE_ARN, mock_session)


def test_parse_calibration_data():
    mock_session = Mock()
    mock_session.get_device.return_value = get_pulse_model(
        MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_1
    )
    device = AwsDevice(DWAVE_ARN, mock_session)
    calibration_data = device._parse_calibration_json(MOCK_gate_calibrations_JSON)
    device_ngc = GateCalibrations(calibration_data)

    expected_waveforms = {
        "wf_drag_gaussian_0": DragGaussianWaveform(
            length=6.000000000000001e-8,
            sigma=6.369913502160144e-9,
            amplitude=-0.4549282253548838,
            beta=7.494904522022295e-10,
            id="wf_drag_gaussian_0",
        )
    }
    expected_pulse_sequences = {
        (Gate.CPhaseShift(-1.5707963267948966), QubitSet([0, 1])): PulseSequence()
        .barrier(QubitSet(0))
        .play(device.frames["q0_q1_cphase_frame"], expected_waveforms["wf_drag_gaussian_0"])
        .barrier([device.frames["q0_q1_cphase_frame"]])
        .barrier([])
        .delay(QubitSet([0, 1]), 3e-07)
        .delay([device.frames["q0_q1_cphase_frame"]], 3e-07)
        .shift_phase(device.frames["q0_q1_cphase_frame"], 3e-07)
        .shift_frequency(device.frames["q0_q1_cphase_frame"], FreeParameter("theta")),
        (Gate.Rx(FreeParameter("theta")), QubitSet(0)): PulseSequence().barrier([]),
        (Gate.CZ(), QubitSet([1, 0])): PulseSequence().barrier([]),
    }
    expected_ngc = GateCalibrations(pulse_sequences=expected_pulse_sequences)
    assert device_ngc == expected_ngc


@pytest.mark.parametrize(
    "bad_input",
    [
        ({
            "gates": {
                "0": {
                    "rx": [
                        {
                            "name": "rx",
                            "qubits": ["0"],
                            "arguments": ["-1.5707963267948966"],
                            "calibrations": [
                                {
                                    "name": "incorrect_instr",
                                    "arguments": [
                                        {"name": "qubit", "value": "0", "type": "string"}
                                    ],
                                }
                            ],
                        }
                    ]
                }
            },
            "waveforms": {},
        }),
        ({
            "gates": {
                "0": {
                    "rx": [
                        {
                            "name": "cphaseshift",
                            "qubits": ["0"],
                            "arguments": ["-1.5707963267948966"],
                            "calibrations": [
                                {
                                    "name": "delay",
                                    "arguments": [
                                        {"name": "bad_value", "value": "1", "type": "float"},
                                        {"name": "qubit", "value": None, "type": "string"},
                                    ],
                                }
                            ],
                        }
                    ]
                }
            },
            "waveforms": {
                "blankId_waveform": {"waveformId": "blankId_waveform", "name": "bad_waveform"},
            },
        }),
    ],
)
@pytest.mark.xfail(raises=ValueError)
def test_parse_calibration_data_bad_instr(bad_input):
    mock_session = Mock()
    mock_session.get_device.return_value = get_pulse_model(
        MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_1
    )
    device = AwsDevice(DWAVE_ARN, mock_session)
    device._parse_calibration_json(bad_input)


def test_queue_depth(arn):
    mock_session = Mock()
    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    mock_session.region = RIGETTI_REGION
    device = AwsDevice(arn, mock_session)
    assert device.queue_depth() == QueueDepthInfo(
        quantum_tasks={QueueType.NORMAL: "19", QueueType.PRIORITY: "3"},
        jobs="0 (3 prioritized job(s) running)",
    )


@pytest.fixture
def noise_model():
    return (
        NoiseModel()
        .add_noise(Noise.BitFlip(0.05), GateCriteria(Gate.H))
        .add_noise(Noise.TwoQubitDepolarizing(0.10), GateCriteria(Gate.CNot))
    )


@patch.dict(
    os.environ,
    {"AMZN_BRAKET_TASK_RESULTS_S3_URI": "s3://env_bucket/env/path"},
)
@patch("braket.aws.aws_device.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_noise_model(aws_quantum_task_mock, aws_session_init, aws_session, noise_model):
    arn = DM1_ARN
    aws_session_init.return_value = aws_session
    aws_session.get_device.return_value = MOCK_GATE_MODEL_NOISE_SIMULATOR
    device = AwsDevice(arn, noise_model=noise_model)
    circuit = Circuit().h(0).cnot(0, 1)
    _ = device.run(circuit)

    expected_circuit = textwrap.dedent(
        """
        OPENQASM 3.0;
        bit[2] b;
        qubit[2] q;
        h q[0];
        #pragma braket noise bit_flip(0.05) q[0]
        cnot q[0], q[1];
        #pragma braket noise two_qubit_depolarizing(0.1) q[0], q[1]
        b[0] = measure q[0];
        b[1] = measure q[1];
        """
    ).strip()

    expected_circuit = Circuit().h(0).bit_flip(0, 0.05).cnot(0, 1).two_qubit_depolarizing(0, 1, 0.1)
    assert aws_quantum_task_mock.call_args_list[0][0][2] == expected_circuit


@patch.dict(
    os.environ,
    {"AMZN_BRAKET_TASK_RESULTS_S3_URI": "s3://env_bucket/env/path"},
)
@patch("braket.aws.aws_device.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_batch_with_noise_model(
    aws_quantum_task_mock, aws_session_init, aws_session, noise_model
):
    arn = DM1_ARN
    aws_session_init.return_value = aws_session
    aws_session.get_device.return_value = MOCK_GATE_MODEL_NOISE_SIMULATOR
    device = AwsDevice(arn, noise_model=noise_model)
    circuit = Circuit().h(0).cnot(0, 1)
    _ = device.run_batch([circuit] * 2)

    expected_circuit = textwrap.dedent(
        """
        OPENQASM 3.0;
        bit[2] b;
        qubit[2] q;
        h q[0];
        #pragma braket noise bit_flip(0.05) q[0]
        cnot q[0], q[1];
        #pragma braket noise two_qubit_depolarizing(0.1) q[0], q[1]
        b[0] = measure q[0];
        b[1] = measure q[1];
        """
    ).strip()

    expected_circuit = Circuit().h(0).bit_flip(0, 0.05).cnot(0, 1).two_qubit_depolarizing(0, 1, 0.1)
    assert aws_quantum_task_mock.call_args_list[0][0][2] == expected_circuit
