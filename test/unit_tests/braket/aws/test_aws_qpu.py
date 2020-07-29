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

import networkx as nx
import pytest
from common_test_utils import MockDevices, run_and_assert, IONQ_ARN, RIGETTI_ARN, DWAVE_ARN

from braket.aws import AwsQpu
from braket.circuits import Circuit

RIGETTI_REGION_KEY = 'rigetti'
IONQ_REGION_KEY = 'ionq'


@pytest.fixture
def qpu(aws_session):
    def _qpu(arn):
        aws_session.get_qpu_metadata.return_value = MockDevices.MOCK_RIGETTI_QPU_1
        return AwsQpu(arn, aws_session)

    return _qpu


@pytest.fixture
def s3_destination_folder():
    return "bucket-foo", "key-bar"


@pytest.fixture
def circuit():
    return Circuit().h(0)


@pytest.fixture
def boto_session():
    _boto_session = Mock()
    _boto_session.region_name = AwsQpu.QPU_REGIONS[RIGETTI_REGION_KEY][0]
    return _boto_session


@pytest.fixture
def aws_session():
    _boto_session = Mock()
    _boto_session.region_name = AwsQpu.QPU_REGIONS[RIGETTI_REGION_KEY][0]
    _aws_session = Mock()
    _aws_session.boto_session = _boto_session
    return _aws_session


def test_aws_session_in_qpu_region(aws_session):
    arn = RIGETTI_ARN
    aws_session.boto_session.region_name = AwsQpu.QPU_REGIONS[RIGETTI_REGION_KEY][0]
    aws_session.get_qpu_metadata.return_value = MockDevices.MOCK_RIGETTI_QPU_1
    AwsQpu(arn, aws_session)

    aws_session.get_qpu_metadata.assert_called_with(arn)


@patch("braket.aws.aws_qpu.AwsSession")
@patch("boto3.Session")
def test_aws_session_in_another_qpu_region(
    boto_session_init, aws_session_init, boto_session, aws_session
):
    arn = RIGETTI_ARN
    region = AwsQpu.QPU_REGIONS.get(RIGETTI_REGION_KEY)[0]

    boto_session_init.return_value = boto_session
    aws_session_init.return_value = aws_session
    aws_session.get_qpu_metadata.return_value = MockDevices.MOCK_RIGETTI_QPU_1

    creds = Mock()
    creds.access_key = "access key"
    creds.secret_key = "secret key"
    creds.token = "token"

    different_region_aws_session = Mock()
    different_region_aws_session.boto_session.get_credentials.return_value = creds
    different_region_aws_session.boto_session.profile_name = "profile name"
    different_region_aws_session.boto_session.region_name = "foobar"

    AwsQpu(arn, different_region_aws_session)

    # assert creds, and region were correctly supplied
    boto_session_init.assert_called_with(
        aws_access_key_id=creds.access_key,
        aws_secret_access_key=creds.secret_key,
        aws_session_token=creds.token,
        region_name=region,
    )

    # assert supplied session, different_region_aws_session, was replaced
    aws_session.get_qpu_metadata.assert_called_with(arn)


@patch("braket.aws.aws_qpu.AwsSession")
@patch("boto3.Session")
def test_no_aws_session_supplied(boto_session_init, aws_session_init, boto_session, aws_session):
    arn = RIGETTI_ARN
    region = AwsQpu.QPU_REGIONS.get(RIGETTI_REGION_KEY)[0]

    boto_session_init.return_value = boto_session
    aws_session_init.return_value = aws_session
    aws_session.get_qpu_metadata.return_value = MockDevices.MOCK_RIGETTI_QPU_1

    AwsQpu(arn)

    boto_session_init.assert_called_with(region_name=region)
    aws_session.get_qpu_metadata.assert_called_with(arn)


@pytest.mark.parametrize(
    "qpu_arn, properties_keys, initial_qpu_data, modified_qpu_data",
    [
        (
            RIGETTI_ARN,
            ["gateModelProperties"],
            MockDevices.MOCK_RIGETTI_QPU_1,
            MockDevices.MOCK_RIGETTI_QPU_2,
        ),
        (
            DWAVE_ARN,
            ["annealingModelProperties", "dWaveProperties"],
            MockDevices.MOCK_DWAVE_QPU_1,
            MockDevices.MOCK_DWAVE_QPU_2,
        ),
    ],
)
def test_qpu_refresh_metadata_success(
    aws_session, qpu_arn, properties_keys, initial_qpu_data, modified_qpu_data
):
    region_key = qpu_arn.split('/')[-2]
    aws_session.boto_session.region_name = AwsQpu.QPU_REGIONS[region_key][0]
    aws_session.get_qpu_metadata.return_value = initial_qpu_data
    qpu = AwsQpu(qpu_arn, aws_session)
    _assert_qpu_fields(qpu, properties_keys, initial_qpu_data)

    # describe_qpus now returns new metadata
    aws_session.get_qpu_metadata.return_value = modified_qpu_data
    qpu.refresh_metadata()
    _assert_qpu_fields(qpu, properties_keys, modified_qpu_data)


def test_qpu_refresh_metadata_error(aws_session):
    err_message = "nooo!"
    aws_session.get_qpu_metadata.side_effect = RuntimeError(err_message)
    with pytest.raises(RuntimeError) as excinfo:
        AwsQpu(RIGETTI_ARN, aws_session)
    assert err_message in str(excinfo.value)


def test_equality(qpu, aws_session):
    qpu_1 = qpu(RIGETTI_ARN)
    qpu_2 = qpu(RIGETTI_ARN)
    aws_session.get_qpu_metadata.return_value = MockDevices.MOCK_IONQ_QPU
    aws_session.boto_session.region_name = AwsQpu.QPU_REGIONS[IONQ_REGION_KEY][0]
    other_qpu = AwsQpu(IONQ_ARN, aws_session)
    non_qpu = "HI"

    assert qpu_1 == qpu_2
    assert qpu_1 is not qpu_2
    assert qpu_1 != other_qpu
    assert qpu_1 != non_qpu


def test_repr(qpu):
    qpu = qpu(RIGETTI_ARN)
    expected = "QPU('name': {}, 'arn': {})".format(qpu.name, qpu.arn)
    assert repr(qpu) == expected


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_no_extra(aws_quantum_task_mock, qpu, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock, qpu, circuit, s3_destination_folder,
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_positional_args(aws_quantum_task_mock, qpu, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock, qpu, circuit, s3_destination_folder, 100, 86400, 0.25, ["foo"]
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_kwargs(aws_quantum_task_mock, qpu, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock,
        qpu,
        circuit,
        s3_destination_folder,
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_shots(aws_quantum_task_mock, qpu, circuit, s3_destination_folder):
    _run_and_assert(aws_quantum_task_mock, qpu, circuit, s3_destination_folder, 100)


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_shots_kwargs(aws_quantum_task_mock, qpu, circuit, s3_destination_folder):
    _run_and_assert(
        aws_quantum_task_mock,
        qpu,
        circuit,
        s3_destination_folder,
        100,
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_shots_poll_timeout_kwargs(
    aws_quantum_task_mock, qpu, circuit, s3_destination_folder
):
    _run_and_assert(
        aws_quantum_task_mock,
        qpu,
        circuit,
        s3_destination_folder,
        100,
        86400,
        extra_kwargs={"bar": 1, "baz": 2},
    )


@patch("braket.aws.aws_quantum_task.AwsQuantumTask.create")
def test_run_with_positional_args_and_kwargs(
    aws_quantum_task_mock, qpu, circuit, s3_destination_folder
):
    _run_and_assert(
        aws_quantum_task_mock,
        qpu,
        circuit,
        s3_destination_folder,
        100,
        86400,
        0.25,
        ["foo"],
        {"bar": 1, "baz": 2},
    )


@pytest.mark.parametrize(
    "properties, expected_edges",
    [
        (
            {"connectivity": {"connectivityGraph": {"0": ["1"], "1": ["2", "3"]}}},
            [(0, 1), (1, 2), (1, 3)],
        ),
        (
            {"connectivity": {"connectivityGraph": {}}, "qubitCount": "3"},
            list(nx.complete_graph(3).edges),
        ),
        ({"couplers": [[0, 1], [1, 2]],}, [(0, 1), (1, 2)]),
        ({}, None),
    ],
)
def test_construct_topology_graph(qpu, properties, expected_edges):
    device = qpu(RIGETTI_ARN)
    with patch("braket.aws.aws_qpu.AwsQpu.properties", properties):
        if expected_edges is None:
            assert device._construct_topology_graph() is None
        else:
            assert list(device._construct_topology_graph().edges) == expected_edges


def _run_and_assert(
    aws_quantum_task_mock,
    qpu_factory,
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
        qpu_factory(RIGETTI_ARN),
        AwsQpu.DEFAULT_SHOTS_QPU,
        AwsQpu.DEFAULT_RESULTS_POLL_TIMEOUT_QPU,
        AwsQpu.DEFAULT_RESULTS_POLL_INTERVAL_QPU,
        circuit,
        s3_destination_folder,
        shots,
        poll_timeout_seconds,
        poll_interval_seconds,
        extra_args,
        extra_kwargs,
    )


def _assert_qpu_fields(qpu, properties_keys, expected_qpu_data):
    assert qpu.arn == expected_qpu_data.get("arn")
    assert qpu.name == expected_qpu_data.get("name")
    expected_qpu_properties = expected_qpu_data.get("properties")
    for key in properties_keys:
        expected_qpu_properties = expected_qpu_properties.get(key)
    for property_name in expected_qpu_properties:
        assert qpu.properties[property_name] == expected_qpu_properties.get(property_name)
    assert qpu.status == expected_qpu_data.get("status")
    assert qpu.status_reason == expected_qpu_data.get("statusReason")
    assert qpu.topology_graph.edges == qpu._construct_topology_graph().edges
