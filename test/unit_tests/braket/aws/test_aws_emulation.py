import json
from unittest.mock import Mock, patch

import networkx as nx
import numpy as np
import pytest
from common_test_utils import RIGETTI_ARN, RIGETTI_REGION

from braket.aws import AwsDevice
from braket.circuits import Circuit, Gate
from braket.circuits.noise_model import GateCriteria, NoiseModel, ObservableCriteria
from braket.circuits.noises import (
    AmplitudeDamping,
    BitFlip,
    Depolarizing,
    PhaseDamping,
    TwoQubitDepolarizing,
)
from braket.device_schema import DeviceCapabilities
from braket.device_schema.error_mitigation.debias import Debias
from braket.device_schema.ionq import IonqDeviceCapabilities, IonqDeviceParameters
from braket.device_schema.iqm import IqmDeviceCapabilities
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.devices import Devices
from braket.devices._aws_device_constants import _get_qpu_gate_translations
from braket.devices.device_noise_models import (
    GateDeviceCalibrationData,
    GateFidelity,
    _setup_calibration_specs,
    device_noise_model,
)
from braket.devices.local_simulator import LocalSimulator
from braket.emulation import Emulator
from braket.passes.circuit_passes import (
    ConnectivityValidator,
    GateConnectivityValidator,
    GateValidator,
    QubitCountValidator,
)

REGION = "us-west-1"

IONQ_ARN = "arn:aws:braket:::device/qpu/ionq/Forte1"
IQM_ARN = "arn:aws:braket:::device/qpu/iqm/Garnet"


MOCK_QPU_GATE_DURATIONS = {
    RIGETTI_ARN: {
        "single_qubit_gate_duration": 40e-9,
        "two_qubit_gate_duration": 240e-9,
    },
    IQM_ARN: {"single_qubit_gate_duration": 32e-9, "two_qubit_gate_duration": 60e-9},
}


@pytest.fixture
def basic_device_capabilities():
    return DeviceCapabilities.parse_obj(
        {
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
                },
                "braket.ir.jaqcd.program": {
                    "actionType": "braket.ir.jaqcd.program",
                    "version": ["1"],
                },
            },
            "deviceParameters": {},
        }
    )


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

MOCK_STANDARDIZED_CALIBRATION_JSON_2 = MOCK_STANDARDIZED_CALIBRATION_JSON.copy()
MOCK_STANDARDIZED_CALIBRATION_JSON_2["twoQubitProperties"]["0-1"]["twoQubitGateFidelity"][2][
    "gateName"
] = "CPhaseShift"

MOCK_RIGETTI_QPU_CAPABILITIES_1 = {
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
            "supportedOperations": ["H", "X", "CNot", "CZ", "Rx", "Ry", "YY"],
        }
    },
    "paradigm": {
        "qubitCount": 3,
        "nativeGateSet": ["cz", "prx", "cphaseshift"],
        "connectivity": {
            "fullyConnected": False,
            "connectivityGraph": {"0": ["1", "2"], "1": ["0"], "2": ["0"]},
        },
    },
    "standardized": MOCK_STANDARDIZED_CALIBRATION_JSON_2,
    "deviceParameters": {},
}

MOCK_IQM_QPU_CAPABILITIES_1 = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.iqm.iqm_device_capabilities",
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
            "supportedOperations": ["H", "CNot", "Ry", "XX", "YY"],
        }
    },
    "paradigm": {
        "qubitCount": 4,
        "nativeGateSet": ["cz", "prx", "cphaseshift"],
        "connectivity": {
            "fullyConnected": False,
            "connectivityGraph": {"0": ["1", "2"], "2": ["3"]},
        },
    },
    "standardized": MOCK_STANDARDIZED_CALIBRATION_JSON,
    "deviceParameters": {},
}


@pytest.fixture
def rigetti_device_capabilities():
    return RigettiDeviceCapabilities.parse_obj(MOCK_RIGETTI_QPU_CAPABILITIES_1)


@pytest.fixture
def iqm_device_capabilities():
    return IqmDeviceCapabilities.parse_obj(MOCK_IQM_QPU_CAPABILITIES_1)


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
        "nativeGateSet": ["CZ", "CPhaseShift", "GPI"],
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


@pytest.fixture
def ionq_device_capabilities():
    return IonqDeviceCapabilities.parse_obj(MOCK_IONQ_GATE_MODEL_CAPABILITIES_JSON_1)


@pytest.fixture
def rigetti_target_noise_model():
    gate_duration_1Q = MOCK_QPU_GATE_DURATIONS[RIGETTI_ARN]["single_qubit_gate_duration"]
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
def iqm_target_noise_model():
    gate_duration_1Q = MOCK_QPU_GATE_DURATIONS[IQM_ARN]["single_qubit_gate_duration"]
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
def ionq_target_noise_model(ionq_device_capabilities):
    T1 = 10.0
    T2 = 1.0
    readout = 0.9
    gate_duration_1Q = 0.000135
    single_rb = 0.98
    two_qubit_rb = 0.9625
    target_noise_model = NoiseModel()
    qubit_count = ionq_device_capabilities.paradigm.qubitCount
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


@patch.dict("braket.devices.device_noise_models._QPU_GATE_DURATIONS", MOCK_QPU_GATE_DURATIONS)
def test_standardized_noise_model(rigetti_device_capabilities, rigetti_target_noise_model):
    noise_model = device_noise_model(rigetti_device_capabilities, RIGETTI_ARN)

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


def test_missing_gate_durations(rigetti_device_capabilities):
    with pytest.raises(ValueError):
        _setup_calibration_specs(rigetti_device_capabilities, "bad_arn")


def test_ionq_noise_model(ionq_device_capabilities, ionq_target_noise_model):
    # modify capabilities to include gate not supported by braket but included in IonQ capabilities.
    ionq_device_capabilities.paradigm.nativeGateSet.append("Two_Qubit_Clifford")
    noise_model = device_noise_model(ionq_device_capabilities, Devices.IonQ.Aria1)
    assert noise_model.instructions == ionq_target_noise_model.instructions


MOCK_DEFAULT_S3_DESTINATION_FOLDER = (
    "amazon-braket-us-test-1-00000000",
    "tasks",
)


@pytest.fixture
def mock_rigetti_qpu_device(rigetti_device_capabilities):
    return {
        "deviceName": "Ankaa-2",
        "deviceType": "QPU",
        "providerName": "Rigetti",
        "deviceStatus": "OFFLINE",
        "deviceCapabilities": rigetti_device_capabilities.json(),
        "deviceQueueInfo": [
            {"queue": "QUANTUM_TASKS_QUEUE", "queueSize": "19", "queuePriority": "Normal"},
            {"queue": "QUANTUM_TASKS_QUEUE", "queueSize": "3", "queuePriority": "Priority"},
            {"queue": "JOBS_QUEUE", "queueSize": "0 (3 prioritized job(s) running)"},
        ],
    }


@pytest.fixture
def mock_iqm_qpu_device(iqm_device_capabilities):
    return {
        "deviceName": "Harmony",
        "deviceType": "QPU",
        "providerName": "IQM",
        "deviceStatus": "OFFLINE",
        "deviceCapabilities": iqm_device_capabilities.json(),
        "deviceQueueInfo": [
            {"queue": "QUANTUM_TASKS_QUEUE", "queueSize": "19", "queuePriority": "Normal"},
            {"queue": "QUANTUM_TASKS_QUEUE", "queueSize": "3", "queuePriority": "Priority"},
            {"queue": "JOBS_QUEUE", "queueSize": "0 (3 prioritized job(s) running)"},
        ],
    }


@pytest.fixture
def mock_ionq_qpu_device(ionq_device_capabilities):
    return {
        "deviceName": "Aspen-M3",
        "deviceType": "QPU",
        "providerName": "Rigetti",
        "deviceStatus": "OFFLINE",
        "deviceCapabilities": ionq_device_capabilities.json(),
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
def ionq_device(aws_session, mock_ionq_qpu_device):
    def _device():
        aws_session.get_device.return_value = mock_ionq_qpu_device
        aws_session.search_devices.return_value = [mock_ionq_qpu_device]
        return AwsDevice(IONQ_ARN, aws_session)

    return _device()


@pytest.fixture
def iqm_device(aws_session, mock_iqm_qpu_device):
    def _device():
        aws_session.get_device.return_value = mock_iqm_qpu_device
        aws_session.search_devices.return_value = [mock_iqm_qpu_device]
        return AwsDevice(IQM_ARN, aws_session)

    return _device()


@pytest.fixture
def rigetti_device(aws_session, mock_rigetti_qpu_device):
    def _device():
        aws_session.get_device.return_value = mock_rigetti_qpu_device
        aws_session.search_devices.return_value = [mock_rigetti_qpu_device]
        return AwsDevice(RIGETTI_ARN, aws_session)

    return _device()


def test_ionq_emulator(ionq_device):
    emulator = ionq_device.emulator
    target_emulator_passes = [
        QubitCountValidator(ionq_device.properties.paradigm.qubitCount),
        GateValidator(
            supported_gates=["x", "Y"],
            native_gates=["cz", "gpi", "cphaseshift"],
        ),
        ConnectivityValidator(nx.from_edgelist([(0, 1), (1, 0)], create_using=nx.DiGraph())),
        GateConnectivityValidator(
            nx.from_dict_of_dicts(
                {
                    0: {1: {"supported_gates": set(["CZ", "CPhaseShift", "GPi"])}},
                    1: {0: {"supported_gates": set(["CZ", "CPhaseShift", "GPi"])}},
                },
                create_using=nx.DiGraph(),
            )
        ),
    ]
    emulator._emulator_passes == target_emulator_passes


@patch.dict("braket.devices.device_noise_models._QPU_GATE_DURATIONS", MOCK_QPU_GATE_DURATIONS)
def test_rigetti_emulator(rigetti_device, rigetti_target_noise_model):
    emulator = rigetti_device.emulator
    assert emulator.noise_model
    assert len(emulator.noise_model.instructions) == len(rigetti_target_noise_model.instructions)
    assert all(
        i1 == i2
        for i1, i2 in zip(
            emulator.noise_model.instructions, rigetti_target_noise_model.instructions
        )
    )

    target_emulator_passes = [
        QubitCountValidator(rigetti_device.properties.paradigm.qubitCount),
        GateValidator(
            supported_gates=["H", "X", "CNot", "CZ", "Rx", "Ry", "YY"],
            native_gates=["cz", "prx", "cphaseshift"],
        ),
        ConnectivityValidator(
            nx.from_edgelist([(0, 1), (0, 2), (1, 0), (2, 0)], create_using=nx.DiGraph())
        ),
        GateConnectivityValidator(
            nx.from_dict_of_dicts(
                {
                    0: {
                        1: {"supported_gates": set(["CZ", "CPhaseShift", "Two_Qubit_Clifford"])},
                        2: {"supported_gates": set()},
                    },
                    1: {0: {"supported_gates": set(["CZ", "CPhaseShift", "Two_Qubit_Clifford"])}},
                    2: {0: {"supported_gates": set()}},
                },
                create_using=nx.DiGraph(),
            )
        ),
    ]
    assert emulator._emulator_passes == target_emulator_passes


@patch.dict("braket.devices.device_noise_models._QPU_GATE_DURATIONS", MOCK_QPU_GATE_DURATIONS)
def test_iqm_emulator(iqm_device, iqm_target_noise_model):
    emulator = iqm_device.emulator
    assert emulator.noise_model
    assert len(emulator.noise_model.instructions) == len(iqm_target_noise_model.instructions)
    assert emulator.noise_model.instructions == iqm_target_noise_model.instructions
    target_emulator_passes = [
        QubitCountValidator(iqm_device.properties.paradigm.qubitCount),
        GateValidator(
            supported_gates=["H", "CNot", "Ry", "XX", "YY"],
            native_gates=["cz", "prx", "cphaseshift"],
        ),
        ConnectivityValidator(
            nx.from_edgelist(
                [(0, 1), (0, 2), (1, 0), (2, 0), (2, 3), (3, 2)], create_using=nx.DiGraph()
            )
        ),
        GateConnectivityValidator(
            nx.from_dict_of_dicts(
                {
                    0: {
                        1: {"supported_gates": set(["CZ", "CPhaseShift", "Two_Qubit_Clifford"])},
                        2: {"supported_gates": set()},
                    },
                    1: {0: {"supported_gates": set(["CZ", "CPhaseShift", "Two_Qubit_Clifford"])}},
                    2: {0: {"supported_gates": set()}, 3: {"supported_gates": set()}},
                    3: {2: {"supported_gates": set()}},
                },
                create_using=nx.DiGraph(),
            )
        ),
    ]

    for i in range(4):
        assert emulator._emulator_passes[i] == target_emulator_passes[i]


@pytest.mark.parametrize(
    "device_capabilities,gate_name,expected_result",
    [
        ("basic_device_capabilities", "fake_gate", "fake_gate"),
        ("rigetti_device_capabilities", "CPHASE", "CPhaseShift"),
        ("ionq_device_capabilities", "GPI", "GPi"),
        ("ionq_device_capabilities", ["GPI", "GPI2", "fake_gate"], ["GPi", "GPi2", "fake_gate"]),
    ],
)
def test_get_gate_translations(device_capabilities, gate_name, expected_result, request):
    device_capabilities_obj = request.getfixturevalue(device_capabilities)
    assert _get_qpu_gate_translations(device_capabilities_obj, gate_name) == expected_result


@patch.dict("braket.devices.device_noise_models._QPU_GATE_DURATIONS", MOCK_QPU_GATE_DURATIONS)
@pytest.mark.parametrize(
    "circuit,is_valid",
    [
        (Circuit(), True),
        (Circuit().cnot(0, 1).h(2), True),
        (Circuit().x(4).yy(4, 8, np.pi), True),
        (Circuit().add_verbatim_box(Circuit().cz(0, 1)).h(5), False),
        (Circuit().x(range(5)), False),
        (Circuit().add_verbatim_box(Circuit().cz(0, 1)).rx(1, np.pi / 4), True),
        (Circuit().add_verbatim_box(Circuit().cz(0, 2)), False),
        (Circuit().xx(0, 1, np.pi / 4), False),
    ],
)
def test_emulator_passes(circuit, is_valid, rigetti_device):
    if is_valid:
        rigetti_device.validate(circuit)
        assert rigetti_device.transform(circuit, apply_noise_model=False) == circuit
    else:
        with pytest.raises(Exception):
            rigetti_device.validate(circuit)


@patch.dict("braket.devices.device_noise_models._QPU_GATE_DURATIONS", MOCK_QPU_GATE_DURATIONS)
@patch.object(LocalSimulator, "run")
def test_device_emulate(mock_run, rigetti_device):
    circuit = Circuit().h(0).cnot(0, 1)
    rigetti_device.emulate(circuit, shots=100)
    mock_run.assert_called_once()


@patch.dict("braket.devices.device_noise_models._QPU_GATE_DURATIONS", MOCK_QPU_GATE_DURATIONS)
@patch.object(AwsDevice, "_setup_emulator", return_value=Emulator())
def test_get_emulator_multiple(mock_setup, rigetti_device):
    emulator = rigetti_device.emulator
    assert emulator._emulator_passes == []
    emulator = rigetti_device.emulator
    mock_setup.assert_called_once()
