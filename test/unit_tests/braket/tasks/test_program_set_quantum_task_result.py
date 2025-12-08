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

import json
from unittest.mock import Mock, patch

import numpy as np
import pytest

from braket.circuits import Circuit
from braket.circuits.observables import X, Y, Z
from braket.parametric import FreeParameter
from braket.program_sets import CircuitBinding, ParameterSets, ProgramSet
from braket.schema_common import BraketSchemaBase
from braket.tasks import ProgramSetQuantumTaskResult
from braket.tasks.program_set_quantum_task_result import CompositeEntry, MeasuredEntry


@pytest.fixture
def execution_measurements():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_executable_result",
            "version": "1",
        },
        "measurements": [
            [0, 0],
            [0, 0],
            [1, 1],
            [0, 0],
            [1, 1],
            [0, 0],
            [1, 1],
            [0, 0],
            [1, 1],
            [0, 0],
            [1, 1],
            [0, 0],
            [0, 0],
            [0, 0],
            [1, 1],
            [1, 1],
            [1, 1],
            [0, 0],
            [1, 1],
            [0, 0],
        ],
        "measuredQubits": [0, 1],
        "inputsIndex": 0,
    }


@pytest.fixture
def execution_measurement_probabilities():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_executable_result",
            "version": "1",
        },
        "measurementProbabilities": {"00": 0.7, "11": 0.3},
        "measuredQubits": [0, 1],
        "inputsIndex": 0,
    }


@pytest.fixture
def execution_results_missing():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_executable_result",
            "version": "1",
        },
        "measuredQubits": [0, 1],
        "inputsIndex": 0,
    }


@pytest.fixture
def execution_failure():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_executable_failure",
            "version": "1",
        },
        "inputsIndex": 0,
        "failureMetadata": {
            "failureReason": "QPU was sick, should be good again after getting some sleep",
            "retryable": True,
            "category": "DEVICE",
        },
    }


@pytest.fixture
def program():
    return {
        "braketSchemaHeader": {"name": "braket.ir.openqasm.program", "version": "1"},
        "source": "OPENQASM 3.0;\nbit[2] b;\nqubit[2] q;\nh q[0];\ncnot q[0], q[1];\nb[0] = measure q[0];\nb[1] = measure q[1];",  # noqa
        "inputs": {"theta": [0.12, 2.1]},
    }


@pytest.fixture
def program_observables():
    return {
        "braketSchemaHeader": {"name": "braket.ir.openqasm.program", "version": "1"},
        "source": "OPENQASM 3.0;\nbit[2] b;\nqubit[2] q;\nh q[0];\ncnot q[0], q[1];\nb[0] = measure q[0];\nb[1] = measure q[1];",  # noqa
        "inputs": {
            "theta": [0.12, 0.12, 0.12, 2.1, 2.1, 2.1],
            "_OBSERVABLE_THETA_0": [0, np.pi / 2, 0, 0, np.pi / 2, 0],
            "_OBSERVABLE_PHI_0": [0, np.pi / 2, np.pi / 2, 0, np.pi / 2, np.pi / 2],
            "_OBSERVABLE_OMEGA_0": [0, np.pi / 2, np.pi / 2, 0, np.pi / 2, np.pi / 2],
        },
    }


@pytest.fixture
def program_result_local(execution_measurement_probabilities, execution_failure, program):
    return {
        "braketSchemaHeader": {"name": "braket.task_result.program_result", "version": "1"},
        "executableResults": [execution_measurement_probabilities, execution_failure],
        "source": program,
        "additionalMetadata": {
            "simulatorMetadata": {
                "braketSchemaHeader": {
                    "name": "braket.task_result.simulator_metadata",
                    "version": "1",
                },
                "executionDuration": 50,
            }
        },
    }


@pytest.fixture
def program_result_s3():
    return {
        "braketSchemaHeader": {"name": "braket.task_result.program_result", "version": "1"},
        "executableResults": ["executables/0.json"],
        "source": "program.json",
        "additionalMetadata": {
            "simulatorMetadata": {
                "braketSchemaHeader": {
                    "name": "braket.task_result.simulator_metadata",
                    "version": "1",
                },
                "executionDuration": 47,
            }
        },
    }


@pytest.fixture
def program_result_observables(execution_measurement_probabilities, program_observables):
    executable_results = [dict(execution_measurement_probabilities) for _ in range(6)]
    for i, executable_result in enumerate(executable_results):
        executable_result["inputsIndex"] = i
    result = {
        "braketSchemaHeader": {"name": "braket.task_result.program_result", "version": "1"},
        "executableResults": executable_results,
        "source": program_observables,
        "additionalMetadata": {
            "simulatorMetadata": {
                "braketSchemaHeader": {
                    "name": "braket.task_result.simulator_metadata",
                    "version": "1",
                },
                "executionDuration": 100,
            }
        },
    }
    return result


@pytest.fixture
def metadata():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_metadata",
            "version": "1",
        },
        "id": "arn:aws:braket:us-west-2:667256736152:quantum-task/bfebc86f-e4ed-4d6f-8131-addd1a49d6dc",  # noqa
        "deviceId": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        "requestedShots": 120,
        "successfulShots": 100,
        "programMetadata": [{"executables": [{}, {}, {}]}],
        "deviceParameters": {
            "braketSchemaHeader": {
                "name": "braket.device_schema.simulators.gate_model_simulator_device_parameters",
                "version": "1",
            },
            "paradigmParameters": {
                "braketSchemaHeader": {
                    "name": "braket.device_schema.gate_model_parameters",
                    "version": "1",
                },
                "qubitCount": 5,
                "disableQubitRewiring": False,
            },
        },
        "createdAt": "2024-10-15T19:06:58.986Z",
        "endedAt": "2024-10-15T19:07:00.382Z",
        "status": "COMPLETED",
        "totalFailedExecutables": 1,
    }


@pytest.fixture
def result_local(metadata, program_result_local):
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_result",
            "version": "1",
        },
        "programResults": [program_result_local],
        "taskMetadata": metadata,
    }


@pytest.fixture
def result_s3():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_result",
            "version": "1",
        },
        "programResults": ["programs/0/results.json"],
        "s3Location": ["amazon-braket-foo", "tasks/bar"],
        "taskMetadata": "metadata.json",
    }


@pytest.fixture
def result_observables(metadata, program_result_observables):
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_result",
            "version": "1",
        },
        "programResults": [program_result_observables],
        "taskMetadata": metadata,
    }


def test_local(result_local, metadata, execution_failure):
    result = ProgramSetQuantumTaskResult.from_object(
        BraketSchemaBase.parse_raw_schema(json.dumps(result_local))
    )
    assert len(result.programs) == 1
    assert result.num_executables == 3  # From metadata
    assert len(result) == 1

    entry = result[0]
    assert isinstance(entry, CompositeEntry)
    assert len(entry) == 2
    assert entry.inputs == ParameterSets({"theta": [0.12, 2.1]})
    with pytest.raises(ValueError):
        entry.expectation(0)
    assert entry.additional_metadata.simulatorMetadata.executionDuration == 50

    success = entry[0]
    assert isinstance(success, MeasuredEntry)
    assert success.probabilities == {"00": 0.7, "11": 0.3}
    assert success.counts["00"] == 28
    assert success.counts["11"] == 12
    assert len(success.counts) == 2
    assert len(success.measurements) == 40
    with pytest.warns(UserWarning):
        assert success.expectation is None
    assert entry[1] == BraketSchemaBase.parse_raw_schema(json.dumps(execution_failure))
    assert result.task_metadata == BraketSchemaBase.parse_raw_schema(json.dumps(metadata))


@patch("braket.tasks.program_set_quantum_task_result.boto3.client")
def test_s3(
    mock_boto3_client, result_s3, program_result_s3, program, execution_measurements, metadata
):
    mock_read_object = Mock()
    mock_read_object.decode.side_effect = [
        json.dumps(f) for f in [metadata, program_result_s3, program, execution_measurements]
    ]
    mock_body_object = Mock()
    mock_body_object.read.return_value = mock_read_object
    mock_client = Mock()
    mock_client.get_object.return_value = {"Body": mock_body_object}
    mock_boto3_client.return_value = mock_client
    result = ProgramSetQuantumTaskResult.from_object(
        BraketSchemaBase.parse_raw_schema(json.dumps(result_s3))
    )
    bucket = "amazon-braket-foo"
    assert mock_client.get_object.call_args_list == [
        (dict(Bucket=bucket, Key="tasks/bar/metadata.json"),),
        (dict(Bucket=bucket, Key="tasks/bar/programs/0/results.json"),),
        (dict(Bucket=bucket, Key="tasks/bar/programs/0/program.json"),),
        (dict(Bucket=bucket, Key="tasks/bar/programs/0/executables/0.json"),),
    ]

    assert len(result.programs) == 1
    assert result.num_executables == 3  # From metadata
    assert len(result) == 1

    entry = result[0]
    assert entry.inputs == ParameterSets({"theta": [0.12, 2.1]})
    with pytest.raises(ValueError):
        entry.expectation(0)
    assert entry.additional_metadata.simulatorMetadata.executionDuration == 47

    assert isinstance(entry, CompositeEntry)
    success = entry[0]
    assert isinstance(success, MeasuredEntry)
    assert len(success.measurements) == 20
    assert success.counts["00"] == 11
    assert success.counts["11"] == 9
    assert len(success.counts) == 2
    assert np.isclose(success.probabilities["00"], 0.55)
    assert np.isclose(success.probabilities["11"], 0.45)
    assert len(success.probabilities) == 2
    with pytest.warns(UserWarning):
        assert success.expectation is None


def test_observables(result_observables, metadata):
    result = ProgramSetQuantumTaskResult.from_object(
        BraketSchemaBase.parse_raw_schema(json.dumps(result_observables)),
        ProgramSet(
            CircuitBinding(
                Circuit().rx(0, FreeParameter("theta")),
                input_sets={"theta": [0.12, 2.1]},
                observables=10 * Z(0) + X(0) - 0.01 * Y(0) @ X(1),
            )
        ),
    )
    assert len(result.programs) == 1
    assert result.num_executables == 3  # From metadata
    assert len(result) == 1

    composite = result[0]
    assert isinstance(composite, CompositeEntry)
    assert composite.inputs == ParameterSets({"theta": [0.12, 2.1]})
    with pytest.raises(ValueError):
        composite.expectation()
    with pytest.raises(ValueError):
        composite.expectation(2)
    assert len(composite) == 6
    assert composite.additional_metadata.simulatorMetadata.executionDuration == 100

    for measured in composite:
        assert isinstance(measured, MeasuredEntry)
        assert measured.probabilities == {"00": 0.7, "11": 0.3}
        assert measured.counts["00"] == 28
        assert measured.counts["11"] == 12
        assert len(measured.counts) == 2
        assert len(measured.measurements) == 40
    assert composite[3].expectation == 4
    assert composite[4].expectation == 0.4
    assert composite[5].expectation == -0.01


def test_observables_no_inputs(result_observables, metadata):
    del result_observables["programResults"][0]["source"]["inputs"]["theta"]
    h = 10000 * Z(0) + 1000 * X(0) - 100 * Z(0) + 10 * Z(1) + X(1) - 0.1 * Y(1)
    result = ProgramSetQuantumTaskResult.from_object(
        BraketSchemaBase.parse_raw_schema(json.dumps(result_observables)),
        ProgramSet(CircuitBinding(Circuit().h(0).cnot(0, 1), observables=h)),
    )
    assert len(result.programs) == 1
    assert result.num_executables == 3  # From metadata
    assert len(result) == 1

    composite = result[0]
    assert isinstance(composite, CompositeEntry)
    assert composite.inputs == ParameterSets({})
    assert np.isclose(composite.expectation(), 4364.36)
    with pytest.raises(ValueError):
        composite.expectation(1)
    assert len(composite) == 6
    assert composite.additional_metadata.simulatorMetadata.executionDuration == 100

    for measured in composite:
        assert isinstance(measured, MeasuredEntry)
        assert measured.probabilities == {"00": 0.7, "11": 0.3}
        assert measured.counts["00"] == 28
        assert measured.counts["11"] == 12
        assert len(measured.counts) == 2
        assert len(measured.measurements) == 40


def test_results_missing(metadata, execution_results_missing, program):
    result = {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_result",
            "version": "1",
        },
        "programResults": [
            {
                "braketSchemaHeader": {"name": "braket.task_result.program_result", "version": "1"},
                "executableResults": [execution_results_missing],
                "source": program,
                "additionalMetadata": {
                    "simulatorMetadata": {
                        "braketSchemaHeader": {
                            "name": "braket.task_result.simulator_metadata",
                            "version": "1",
                        },
                        "executionDuration": 50,
                    }
                },
            }
        ],
        "taskMetadata": metadata,
    }
    with pytest.raises(ValueError):
        ProgramSetQuantumTaskResult.from_object(
            BraketSchemaBase.parse_raw_schema(json.dumps(result))
        )


def test_dispatch_executable_result_with_none_inputs(execution_measurement_probabilities):
    mock_program = Mock()
    mock_program.source = "OPENQASM 3.0;\nbit[2] b;\nqubit[2] q;\nh q[0];\ncnot q[0], q[1];\nb[0] = measure q[0];\nb[1] = measure q[1];"
    mock_program.inputs = None
    result = BraketSchemaBase.parse_raw_schema(json.dumps(execution_measurement_probabilities))

    measured_entry = CompositeEntry._dispatch_executable_result(
        result=result, program=mock_program, observables=None, shots_per_executable=40
    )
    assert isinstance(measured_entry, MeasuredEntry)
    assert measured_entry.inputs is None
    assert measured_entry.probabilities == {"00": 0.7, "11": 0.3}
