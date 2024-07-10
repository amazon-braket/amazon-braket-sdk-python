import json
from unittest.mock import Mock

import numpy as np
import pytest
from common_test_utils import RIGETTI_REGION

from braket.aws import AwsDevice
from braket.aws.aws_noise_models import (
    QPU_GATE_DURATIONS,
    GateDeviceCalibrationData,
    GateFidelity,
    _setup_calibration_specs,
    create_device_noise_model,
)
from braket.circuits import Gate
from braket.circuits.noise_model import GateCriteria, NoiseModel, ObservableCriteria
from braket.circuits.noises import (
    AmplitudeDamping,
    BitFlip,
    Depolarizing,
    PhaseDamping,
    TwoQubitDepolarizing,
)
from braket.device_schema.error_mitigation.debias import Debias
from braket.device_schema.ionq import IonqDeviceCapabilities, IonqDeviceParameters
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.devices import Devices

MOCK_STANDARDIZED_CALIBRATION_JSON = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
        "version": "1",
    },
    "oneQubitProperties": {
        "0": {
            "T1": {"value": 0.5, "standardError": None, "unit": "S"},
            "T2": {"value": 0.2, "standardError": None, "unit": "S"},
            "oneQubitFidelity": [
                {
                    "fidelityType": {"name": "RANDOMIZED_BENCHMARKING", "description": None},
                    "fidelity": 0.99,
                    "standardError": 1e-2,
                },
                {
                    "fidelityType": {
                        "name": "SIMULTANEOUS_RANDOMIZED_BENCHMARKING",
                        "description": None,
                    },
                    "fidelity": 0.9934,
                    "standardError": 0.0065,
                },
                {
                    "fidelityType": {"name": "READOUT", "description": None},
                    "fidelity": 0.958,
                    "standardError": None,
                },
            ],
        },
        "1": {
            "T1": {"value": 0.97, "standardError": None, "unit": "S"},
            "T2": {"value": 0.234, "standardError": None, "unit": "S"},
            "oneQubitFidelity": [
                {
                    "fidelityType": {"name": "RANDOMIZED_BENCHMARKING", "description": None},
                    "fidelity": 0.9983,
                    "standardError": 4e-5,
                },
                {
                    "fidelityType": {
                        "name": "SIMULTANEOUS_RANDOMIZED_BENCHMARKING",
                        "description": None,
                    },
                    "fidelity": 0.879,
                    "standardError": 0.00058,
                },
                {
                    "fidelityType": {"name": "READOUT", "description": None},
                    "fidelity": 0.989,
                    "standardError": None,
                },
            ],
        },
        "2": {
            "T1": {"value": 0.8, "standardError": None, "unit": "S"},
            "T2": {"value": 0.4, "standardError": None, "unit": "S"},
            "oneQubitFidelity": [
                {
                    "fidelityType": {"name": "READOUT", "description": None},
                    "fidelity": 0.958,
                    "standardError": None,
                }
            ],
        },
    },
    "twoQubitProperties": {
        "0-1": {
            "twoQubitGateFidelity": [
                {
                    "direction": None,
                    "gateName": "CZ",
                    "fidelity": 0.9358,
                    "standardError": 0.01437,
                    "fidelityType": {"name": "INTERLEAVED_RANDOMIZED_BENCHMARKING"},
                },
                {
                    "direction": None,
                    "gateName": "Two_Qubit_Clifford",
                    "fidelity": 0.9,
                    "standardError": 0.0237,
                    "fidelityType": {"name": "INTERLEAVED_RANDOMIZED_BENCHMARKING"},
                },
                {
                    "direction": None,
                    "gateName": "CPHASE",
                    "fidelity": 0.9,
                    "standardError": 0.01437,
                    "fidelityType": {"name": "INTERLEAVED_RANDOMIZED_BENCHMARKING"},
                },
            ]
        }
    },
}


MOCK_STANDARDIZED_QPU_CAPABILITIES_JSON_1 = {
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
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "version": ["1"],
            "supportedOperations": ["H"],
        }
    },
    "paradigm": {
        "qubitCount": 3,
        "nativeGateSet": ["cz", "cphaseshift"],
        "connectivity": {
            "fullyConnected": False,
            "connectivityGraph": {"0": ["1", "2"], "1": ["0"], "2": ["0"]},
        },
    },
    "standardized": MOCK_STANDARDIZED_CALIBRATION_JSON,
    "deviceParameters": {},
}

MOCK_STANDARDIZED_GATE_MODEL_RIGETTI_CAPABILITIES_1 = RigettiDeviceCapabilities.parse_obj(
    MOCK_STANDARDIZED_QPU_CAPABILITIES_JSON_1
)


MOCK_IONQ_GATE_MODEL_CAPABILITIES_JSON_1 = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.ionq.ionq_device_capabilities",
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
            "supportedOperations": ["x", "y"],
        }
    },
    "paradigm": {
        "qubitCount": 2,
        "nativeGateSet": ["CZ", "CPhaseShift", "GPI", "Toffoli"],
        "connectivity": {"fullyConnected": True, "connectivityGraph": {}},
    },
    "provider": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.ionq.ionq_provider_properties",
            "version": "1",
        },
        "errorMitigation": {Debias: {"minimumShots": 2500}},
        "fidelity": {"1Q": {"mean": 0.98}, "2Q": {"mean": 0.9625}, "spam": {"mean": 0.9}},
        "timing": {
            "1Q": 0.000135,
            "2Q": 0.0006,
            "T1": 10.0,
            "T2": 1.0,
            "readout": 0.0003,
            "reset": 2e-05,
        },
    },
    "deviceParameters": json.loads(IonqDeviceParameters.schema_json()),
}

MOCK_IONQ_DEVICE_CAPABILITIES = IonqDeviceCapabilities.parse_obj(
    MOCK_IONQ_GATE_MODEL_CAPABILITIES_JSON_1
)


@pytest.fixture
def rigetti_target_noise_model():
    gate_duration_1Q = QPU_GATE_DURATIONS[Devices.Rigetti.AspenM3]["single_qubit_gate_duration"]
    target_noise_model = (
        NoiseModel()
        .add_noise(AmplitudeDamping(1 - np.exp(-(gate_duration_1Q / 0.5))), GateCriteria(qubits=0))
        .add_noise(
            PhaseDamping(0.5 * (1 - np.exp(-(gate_duration_1Q / 0.2)))), GateCriteria(qubits=0)
        )
        .add_noise(Depolarizing(1 - 0.9934), GateCriteria(qubits=0))
        .add_noise(BitFlip(1 - 0.958), ObservableCriteria(qubits=0))
        .add_noise(AmplitudeDamping(1 - np.exp(-(gate_duration_1Q / 0.97))), GateCriteria(qubits=1))
        .add_noise(
            PhaseDamping(0.5 * (1 - np.exp(-(gate_duration_1Q / 0.234)))), GateCriteria(qubits=1)
        )
        .add_noise(Depolarizing(1 - 0.879), GateCriteria(qubits=1))
        .add_noise(BitFlip(1 - 0.989), ObservableCriteria(qubits=1))
        .add_noise(AmplitudeDamping(1 - np.exp(-(gate_duration_1Q / 0.8))), GateCriteria(qubits=2))
        .add_noise(
            PhaseDamping(0.5 * (1 - np.exp(-(gate_duration_1Q / 0.4)))), GateCriteria(qubits=2)
        )
        .add_noise(BitFlip(1 - 0.958), ObservableCriteria(qubits=2))
        .add_noise(TwoQubitDepolarizing(1 - 0.9358), GateCriteria(Gate.CZ, [(1, 0), (0, 1)]))
        .add_noise(TwoQubitDepolarizing(1 - 0.9), GateCriteria(Gate.CPhaseShift, [(1, 0), (0, 1)]))
    )

    return target_noise_model


@pytest.fixture
def ionq_target_noise_model():
    T1 = 10.0
    T2 = 1.0
    readout = 0.9
    gate_duration_1Q = 0.000135
    single_rb = 0.98
    two_qubit_rb = 0.9625
    target_noise_model = NoiseModel()
    qubit_count = MOCK_IONQ_DEVICE_CAPABILITIES.paradigm.qubitCount
    for i in range(qubit_count):
        target_noise_model = (
            target_noise_model.add_noise(
                AmplitudeDamping(1 - np.exp(-(gate_duration_1Q / T1))), GateCriteria(qubits=i)
            )
            .add_noise(
                PhaseDamping(0.5 * (1 - np.exp(-(gate_duration_1Q / T2)))), GateCriteria(qubits=i)
            )
            .add_noise(Depolarizing(1 - single_rb), GateCriteria(qubits=i))
            .add_noise(BitFlip(1 - readout), ObservableCriteria(qubits=i))
        )

    for i in range(qubit_count):
        for j in range(i, qubit_count):
            if i != j:
                target_noise_model = target_noise_model.add_noise(
                    TwoQubitDepolarizing(1 - two_qubit_rb), GateCriteria(Gate.CZ, [(i, j), (j, i)])
                ).add_noise(
                    TwoQubitDepolarizing(1 - two_qubit_rb),
                    GateCriteria(Gate.CPhaseShift, [(i, j), (j, i)]),
                )
    return target_noise_model


def test_standardized_noise_model(rigetti_target_noise_model):
    noise_model = create_device_noise_model(
        MOCK_STANDARDIZED_GATE_MODEL_RIGETTI_CAPABILITIES_1, Devices.Rigetti.AspenM3
    )

    assert noise_model.instructions == rigetti_target_noise_model.instructions


@pytest.mark.parametrize(
    "single_qubit_gate_duration,two_qubit_gate_duration,qubit_labels,\
        single_qubit_specs,two_qubit_edge_specs",
    [
        (0.5, 0.2, {0, 1}, {2: {"h": 0.5}}, {(0, 1): GateFidelity(Gate.H, 0.5)}),
        (0.5, 0.2, {0, 1}, {0: {"h": 0.5}}, {(0, 2): GateFidelity(Gate.H, 0.5)}),
    ],
)
def test_invalid_gate_calibration_data(
    single_qubit_gate_duration,
    two_qubit_gate_duration,
    qubit_labels,
    single_qubit_specs,
    two_qubit_edge_specs,
):
    with pytest.raises(ValueError):
        GateDeviceCalibrationData(
            single_qubit_gate_duration,
            two_qubit_gate_duration,
            qubit_labels,
            single_qubit_specs,
            two_qubit_edge_specs,
        )


def test_missing_gate_durations():
    with pytest.raises(ValueError):
        _setup_calibration_specs(MOCK_STANDARDIZED_GATE_MODEL_RIGETTI_CAPABILITIES_1, "bad_arn")


def test_ionq_noise_model(ionq_target_noise_model):
    noise_model = create_device_noise_model(MOCK_IONQ_DEVICE_CAPABILITIES, Devices.IonQ.Aria1)
    assert noise_model.instructions == ionq_target_noise_model.instructions


MOCK_DEFAULT_S3_DESTINATION_FOLDER = (
    "amazon-braket-us-test-1-00000000",
    "tasks",
)

MOCK_GATE_MODEL_QPU_1 = {
    "deviceName": "Aspen-M3",
    "deviceType": "QPU",
    "providerName": "Rigetti",
    "deviceStatus": "OFFLINE",
    "deviceCapabilities": MOCK_STANDARDIZED_GATE_MODEL_RIGETTI_CAPABILITIES_1.json(),
    "deviceQueueInfo": [
        {"queue": "QUANTUM_TASKS_QUEUE", "queueSize": "19", "queuePriority": "Normal"},
        {"queue": "QUANTUM_TASKS_QUEUE", "queueSize": "3", "queuePriority": "Priority"},
        {"queue": "JOBS_QUEUE", "queueSize": "0 (3 prioritized job(s) running)"},
    ],
}

MOCK_GATE_MODEL_QPU_2 = {
    "deviceName": "Aria-1",
    "deviceType": "QPU",
    "providerName": "IonQ",
    "deviceStatus": "OFFLINE",
    "deviceCapabilities": MOCK_IONQ_DEVICE_CAPABILITIES.json(),
    "deviceQueueInfo": [
        {"queue": "QUANTUM_TASKS_QUEUE", "queueSize": "19", "queuePriority": "Normal"},
        {"queue": "QUANTUM_TASKS_QUEUE", "queueSize": "3", "queuePriority": "Priority"},
        {"queue": "JOBS_QUEUE", "queueSize": "0 (3 prioritized job(s) running)"},
    ],
}


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


@pytest.fixture(
    params=[
        "arn:aws:braket:us-west-1::device/quantum-simulator/amazon/sim",
        "arn:aws:braket:::device/quantum-simulator/amazon/sim",
    ]
)
def arn(request):
    return request.param


@pytest.fixture
def rigetti_device(aws_session):
    def _device(arn):
        aws_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
        aws_session.search_devices.return_value = [MOCK_GATE_MODEL_QPU_1]
        return AwsDevice(arn, aws_session)

    return _device


@pytest.fixture
def ionq_device(aws_session):
    def _device(arn):
        aws_session.get_device.return_value = MOCK_GATE_MODEL_QPU_2
        aws_session.search_devices.return_value = [MOCK_GATE_MODEL_QPU_2]
        return AwsDevice(arn, aws_session)

    return _device
