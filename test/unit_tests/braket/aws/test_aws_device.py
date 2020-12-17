# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from unittest.mock import Mock, patch

import pytest
from common_test_utils import (
    DWAVE_ARN,
    IONQ_ARN,
    RIGETTI_ARN,
    SV1_ARN,
    run_and_assert,
    run_batch_and_assert,
)

from braket.aws import AwsDevice, AwsDeviceType, AwsQuantumTask
from braket.circuits import Circuit
from braket.device_schema.dwave import DwaveDeviceCapabilities
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.device_schema.simulators import GateModelSimulatorDeviceCapabilities

MOCK_GATE_MODEL_QPU_CAPABILITIES_1 = RigettiDeviceCapabilities.parse_obj(
    {
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
)

MOCK_GATE_MODEL_QPU_1 = {
    "deviceName": "Aspen-8",
    "deviceType": "QPU",
    "providerName": "provider1",
    "deviceStatus": "OFFLINE",
    "deviceCapabilities": MOCK_GATE_MODEL_QPU_CAPABILITIES_1.json(),
}

MOCK_GATE_MODEL_QPU_CAPABILITIES_2 = RigettiDeviceCapabilities.parse_obj(
    {
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
)

MOCK_GATE_MODEL_QPU_2 = {
    "deviceName": "blah",
    "deviceType": "QPU",
    "providerName": "blahhhh",
    "deviceStatus": "OFFLINE",
    "deviceCapabilities": MOCK_GATE_MODEL_QPU_CAPABILITIES_2.json(),
}

MOCK_DWAVE_QPU_CAPABILITIES = DwaveDeviceCapabilities.parse_obj(
    {
        "braketSchemaHeader": {
            "name": "braket.device_schema.dwave.dwave_device_capabilities",
            "version": "1",
        },
        "provider": {
            "annealingOffsetStep": 1.45,
            "annealingOffsetStepPhi0": 1.45,
            "annealingOffsetRanges": [[1.45, 1.45], [1.45, 1.45]],
            "annealingDurationRange": [1, 2, 3],
            "couplers": [[1, 2], [1, 2]],
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
)

MOCK_DWAVE_QPU = {
    "deviceName": "name3",
    "deviceType": "QPU",
    "providerName": "provider1",
    "deviceStatus": "ONLINE",
    "deviceCapabilities": MOCK_DWAVE_QPU_CAPABILITIES.json(),
}

MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES = GateModelSimulatorDeviceCapabilities.parse_obj(
    {
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
            }
        },
        "paradigm": {"qubitCount": 30},
        "deviceParameters": {},
    }
)

MOCK_GATE_MODEL_SIMULATOR = {
    "deviceName": "SV1",
    "deviceType": "SIMULATOR",
    "providerName": "provider1",
    "deviceStatus": "ONLINE",
    "deviceCapabilities": MOCK_GATE_MODEL_SIMULATOR_CAPABILITIES.json(),
}

RIGETTI_REGION_KEY = "rigetti"


@pytest.fixture
def arn():
    return "test_arn"


@pytest.fixture
def s3_destination_folder():
    return "bucket-foo", "key-bar"


@pytest.fixture
def circuit():
    return Circuit().h(0)


@pytest.fixture
def boto_session():
    _boto_session = Mock()
    _boto_session.region_name = AwsDevice.DEVICE_REGIONS[RIGETTI_REGION_KEY][0]
    return _boto_session


@pytest.fixture
def aws_session():
    _boto_session = Mock()
    _boto_session.region_name = AwsDevice.DEVICE_REGIONS[RIGETTI_REGION_KEY][0]

    creds = Mock()
    creds.access_key = "access key"
    creds.secret_key = "secret key"
    creds.token = "token"
    _boto_session.get_credentials.return_value = creds

    _aws_session = Mock()
    _aws_session.boto_session = _boto_session
    return _aws_session


@pytest.fixture
def device(aws_session):
    def _device(arn):
        aws_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
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
def test_device_creation(device_capabilities, get_device_data, arn):
    mock_session = Mock()
    mock_session.get_device.return_value = get_device_data
    device = AwsDevice(arn, mock_session)
    _assert_device_fields(device, device_capabilities, get_device_data)


def test_device_refresh_metadata(arn):
    mock_session = Mock()
    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    device = AwsDevice(arn, mock_session)
    _assert_device_fields(device, MOCK_GATE_MODEL_QPU_CAPABILITIES_1, MOCK_GATE_MODEL_QPU_1)

    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_2
    device.refresh_metadata()
    _assert_device_fields(device, MOCK_GATE_MODEL_QPU_CAPABILITIES_2, MOCK_GATE_MODEL_QPU_2)


def test_equality(arn):
    mock_session = Mock()
    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    device_1 = AwsDevice(arn, mock_session)
    device_2 = AwsDevice(arn, mock_session)
    other_device = AwsDevice("foo_bar", mock_session)
    non_device = "HI"

    assert device_1 == device_2
    assert device_1 is not device_2
    assert device_1 != other_device
    assert device_1 != non_device


def test_repr(arn):
    mock_session = Mock()
    mock_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    device = AwsDevice(arn, mock_session)
    expected = "Device('name': {}, 'arn': {})".format(device.name, device.arn)
    assert repr(device) == expected


def test_device_aws_session_in_qpu_region(aws_session):
    arn = RIGETTI_ARN
    aws_session.boto_session.region_name = AwsDevice.DEVICE_REGIONS[RIGETTI_REGION_KEY][0]
    aws_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    AwsDevice(arn, aws_session)

    aws_session.get_device.assert_called_with(arn)


@patch("braket.aws.aws_device.AwsSession")
@patch("boto3.Session")
def test_aws_session_in_another_qpu_region(
    boto_session_init, aws_session_init, boto_session, aws_session
):
    arn = RIGETTI_ARN
    region = AwsDevice.DEVICE_REGIONS.get(RIGETTI_REGION_KEY)[0]

    boto_session_init.return_value = boto_session
    aws_session_init.return_value = aws_session
    aws_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1

    creds = Mock()
    creds.access_key = "a"
    creds.secret_key = "b"
    creds.token = "c"

    different_region_aws_session = Mock()
    different_region_aws_session.boto_session.get_credentials.return_value = creds
    different_region_aws_session.boto_session.profile_name = "profile name"
    different_region_aws_session.boto_session.region_name = "foobar"

    AwsDevice(arn, different_region_aws_session)

    # assert creds, and region were correctly supplied
    boto_session_init.assert_called_with(
        aws_access_key_id=creds.access_key,
        aws_secret_access_key=creds.secret_key,
        aws_session_token=creds.token,
        region_name=region,
    )

    # assert supplied session, different_region_aws_session, was replaced
    aws_session.get_device.assert_called_with(arn)


@patch("braket.aws.aws_device.AwsSession")
@patch("boto3.Session")
def test_device_no_aws_session_supplied(
    boto_session_init, aws_session_init, boto_session, aws_session
):
    arn = RIGETTI_ARN
    region = AwsDevice.DEVICE_REGIONS.get(RIGETTI_REGION_KEY)[0]

    boto_session_init.return_value = boto_session
    aws_session_init.return_value = aws_session
    aws_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1

    AwsDevice(arn)

    boto_session_init.assert_called_with(region_name=region)
    aws_session.get_device.assert_called_with(arn)


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_no_extra(aws_quantum_task_mock, device, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock,
        device,
        circuit,
        s3_destination_folder,
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_positional_args(aws_quantum_task_mock, device, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock, device, circuit, s3_destination_folder, 100, 86400, 0.25, ["foo"]
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
def test_run_with_qpu_no_shots(aws_quantum_task_mock, device, circuit, s3_destination_folder):
    run_and_assert(
        aws_quantum_task_mock,
        device(RIGETTI_ARN),
        AwsDevice.DEFAULT_SHOTS_QPU,
        AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        circuit,
        s3_destination_folder,
        None,
        None,
        None,
        None,
        None,
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
        ["foo"],
        {"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_device.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_batch_no_extra(
    aws_quantum_task_mock, aws_session_mock, device, circuit, s3_destination_folder
):
    _run_batch_and_assert(
        aws_quantum_task_mock,
        aws_session_mock,
        device,
        [circuit for _ in range(10)],
        s3_destination_folder,
    )


@patch("braket.aws.aws_device.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_batch_with_shots(
    aws_quantum_task_mock, aws_session_mock, device, circuit, s3_destination_folder
):
    _run_batch_and_assert(
        aws_quantum_task_mock,
        aws_session_mock,
        device,
        [circuit for _ in range(10)],
        s3_destination_folder,
        1000,
    )


@patch("braket.aws.aws_device.AwsSession")
@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_batch_with_max_parallel_and_kwargs(
    aws_quantum_task_mock, aws_session_mock, device, circuit, s3_destination_folder
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
        extra_kwargs={"bar": 1, "baz": 2},
    )


def _run_and_assert(
    aws_quantum_task_mock,
    device_factory,
    circuit,
    s3_destination_folder,
    shots=None,  # Treated as positional arg
    poll_timeout_seconds=None,  # Treated as positional arg
    poll_interval_seconds=None,  # Treated as positional arg
    extra_args=None,
    extra_kwargs=None,
):
    run_and_assert(
        aws_quantum_task_mock,
        device_factory("foo_bar"),
        AwsDevice.DEFAULT_SHOTS_SIMULATOR,
        AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        circuit,
        s3_destination_folder,
        shots,
        poll_timeout_seconds,
        poll_interval_seconds,
        extra_args,
        extra_kwargs,
    )


def _run_batch_and_assert(
    aws_quantum_task_mock,
    aws_session_mock,
    device_factory,
    circuits,
    s3_destination_folder,
    shots=None,  # Treated as positional arg
    max_parallel=None,  # Treated as positional arg
    max_connections=None,  # Treated as positional arg
    poll_timeout_seconds=None,  # Treated as a positional arg
    poll_interval_seconds=None,  # Treated as positional arg
    extra_args=None,
    extra_kwargs=None,
):
    run_batch_and_assert(
        aws_quantum_task_mock,
        aws_session_mock,
        device_factory("foo_bar"),
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


@patch("braket.aws.aws_device.AwsDevice._copy_aws_session")
def test_get_devices(mock_copy_aws_session, aws_session):
    session_for_region = Mock()
    mock_copy_aws_session.return_value = session_for_region
    session_for_region.search_devices.side_effect = [
        [
            {
                "deviceArn": SV1_ARN,
                "deviceName": "SV1",
                "deviceType": "SIMULATOR",
                "deviceStatus": "ONLINE",
                "providerName": "Amazon Braket",
            }
        ],
        [
            {
                "deviceArn": RIGETTI_ARN,
                "deviceName": "Aspen-8",
                "deviceType": "QPU",
                "deviceStatus": "ONLINE",
                "providerName": "Rigetti",
            },
            {
                "deviceArn": SV1_ARN,
                "deviceName": "SV1",
                "deviceType": "SIMULATOR",
                "deviceStatus": "ONLINE",
                "providerName": "Amazon Braket",
            },
        ],
    ]
    session_for_region.get_device.side_effect = [MOCK_GATE_MODEL_SIMULATOR, MOCK_GATE_MODEL_QPU_1]
    results = AwsDevice.get_devices(
        arns=[SV1_ARN, RIGETTI_ARN],
        types=["SIMULATOR", "QPU"],
        provider_names=["Amazon Braket", "Rigetti"],
        statuses=["ONLINE"],
        aws_session=aws_session,
    )
    assert [result.name for result in results] == ["Aspen-8", "SV1"]


@pytest.mark.parametrize(
    "region,types", [("us-west-1", ["QPU", "SIMULATOR"]), ("us-west-2", ["QPU"])]
)
@patch("braket.aws.aws_device.AwsDevice._copy_aws_session")
def test_get_devices_session_regions(mock_copy_aws_session, region, types):
    _boto_session = Mock()
    _boto_session.region_name = region
    _aws_session = Mock()
    _aws_session.boto_session = _boto_session

    session_for_region = Mock()
    session_for_region.search_devices.return_value = [
        {
            "deviceArn": SV1_ARN,
            "deviceName": "SV1",
            "deviceType": "SIMULATOR",
            "deviceStatus": "ONLINE",
            "providerName": "Amazon Braket",
        }
    ]
    session_for_region.get_device.return_value = MOCK_GATE_MODEL_SIMULATOR
    mock_copy_aws_session.return_value = session_for_region

    arns = [RIGETTI_ARN]
    provider_names = ["Rigetti"]
    statuses = ["ONLINE"]

    AwsDevice.get_devices(
        arns=arns,
        types=["SIMULATOR", "QPU"],
        provider_names=provider_names,
        statuses=statuses,
        aws_session=_aws_session,
    )
    session_for_region.search_devices.assert_called_with(
        arns=arns,
        names=None,
        types=types,
        statuses=statuses,
        provider_names=provider_names,
    )


def test_get_devices_simulator_different_region():
    _boto_session = Mock()
    _boto_session.region_name = "us-west-2"
    _aws_session = Mock()
    _aws_session.boto_session = _boto_session

    assert (
        AwsDevice.get_devices(
            arns=None,
            types=["SIMULATOR"],
            # Force get_devices to only look in us-west-1
            provider_names=["Rigetti"],
            statuses=None,
            aws_session=_aws_session,
        )
        == []
    )


@pytest.mark.xfail(raises=ValueError)
def test_get_devices_invalid_order_by():
    AwsDevice.get_devices(order_by="foo")


@pytest.mark.parametrize(
    "input,output",
    [
        (
            {"arns": None, "provider_names": None},
            {"us-west-2", "us-west-1", "us-east-1"},
        ),
        (
            {"arns": [RIGETTI_ARN, DWAVE_ARN], "provider_names": None},
            {"us-west-2", "us-west-1"},
        ),
        (
            {
                "arns": [RIGETTI_ARN, DWAVE_ARN, IONQ_ARN],
                "provider_names": ["Rigetti", "Amazon Braket", "IONQ", "FOO"],
            },
            {"us-west-2", "us-west-1", "us-east-1"},
        ),
    ],
)
def test_get_devices_regions_set(input, output):
    assert AwsDevice._get_devices_regions_set(**input) == output
