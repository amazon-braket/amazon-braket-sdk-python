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

import json
from unittest.mock import Mock

from braket.aws.aws_qpu_arns import AwsQpuArns
from braket.aws.aws_quantum_simulator_arns import AwsQuantumSimulatorArns


class MockDevices:

    MOCK_RIGETTI_QPU_1 = {
        "arn": AwsQpuArns.RIGETTI,
        "properties": {
            "gateModelProperties": {
                "qubitCount": 16,
                "connectivity": {
                    "connectivityGraph": {"0": ["1", "2"], "1": ["0", "2"], "2": ["0", "1"]}
                },
                "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "T"],
            }
        },
        "name": "Rigetti",
        "status": "AVAILABLE",
    }

    MOCK_RIGETTI_QPU_2 = {
        "arn": AwsQpuArns.RIGETTI,
        "properties": {
            "gateModelProperties": {
                "qubitCount": 30,
                "connectivity": {
                    "connectivityGraph": {"0": ["1", "2"], "1": ["0", "2"], "2": ["0", "1"]}
                },
                "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "T", "S"],
            }
        },
        "name": "Rigetti",
        "status": "UNAVAILABLE",
        "statusReason": "Under maintenance",
    }

    MOCK_DWAVE_QPU_1 = {
        "arn": AwsQpuArns.DWAVE,
        "properties": {
            "annealingModelProperties": {
                "dWaveProperties": {
                    "activeQubitCount": 2,
                    "annealingOffsetStep": 2.0,
                    "annealingOffsetStepPhi0": 4.0,
                    "annealingOffsetRanges": [[1.34, 5.23], [3.24, 1.44]],
                    "annealingDurationRange": [3, 5],
                    "couplers": [[1, 2]],
                    "defaultAnnealingDuration": 4,
                    "defaultProgrammingThermalizationDuration": 2,
                    "defaultReadoutThermalizationDuration": 1,
                    "extendedJRange": [3.0, 4.0],
                    "hGainScheduleRange": [2.0, 3.0],
                    "hRange": [3.4, 5.6],
                    "jRange": [1.0, 2.0],
                    "maximumAnnealingSchedulePoints": 3,
                    "maximumHGainSchedulePoints": 2,
                    "qubitCount": 3,
                    "qubits": [0, 2],
                    "perQubitCouplingRange": [1.0, 3.0],
                    "programmingThermalizationDurationRange": [1, 2],
                    "quotaConversionRate": 2.5,
                    "readoutThermalizationDurationRange": [4, 6],
                    "shotsRange": [3, 5],
                    "taskRunDurationRange": [3, 6],
                    "topology": {"type": "chimera", "topology": [1, 1, 1]},
                }
            }
        },
        "name": "D-Wave",
        "status": "AVAILABLE",
    }

    MOCK_DWAVE_QPU_2 = {
        "arn": AwsQpuArns.DWAVE,
        "properties": {
            "annealingModelProperties": {
                "dWaveProperties": {
                    "activeQubitCount": 3,
                    "annealingOffsetStep": 2.0,
                    "annealingOffsetStepPhi0": 4.0,
                    "annealingOffsetRanges": [[1.34, 5.23], [3.24, 1.44]],
                    "annealingDurationRange": [3, 5],
                    "couplers": [[1, 2]],
                    "defaultAnnealingDuration": 4,
                    "defaultProgrammingThermalizationDuration": 2,
                    "defaultReadoutThermalizationDuration": 1,
                    "extendedJRange": [3.0, 4.0],
                    "hGainScheduleRange": [2.0, 3.0],
                    "hRange": [3.4, 5.6],
                    "jRange": [1.0, 2.0],
                    "maximumAnnealingSchedulePoints": 3,
                    "maximumHGainSchedulePoints": 2,
                    "qubitCount": 3,
                    "qubits": [0, 1, 2],
                    "perQubitCouplingRange": [1.0, 3.0],
                    "programmingThermalizationDurationRange": [1, 2],
                    "quotaConversionRate": 2.5,
                    "readoutThermalizationDurationRange": [4, 6],
                    "shotsRange": [3, 5],
                    "taskRunDurationRange": [3, 6],
                    "topology": {"type": "chimera", "topology": [1, 1, 1]},
                }
            }
        },
        "name": "D-Wave",
        "status": "UNAVAILABLE",
        "statusReason": "Under maintenance",
    }

    MOCK_IONQ_QPU = {
        "arn": AwsQpuArns.IONQ,
        "properties": {
            "gateModelProperties": {
                "qubitCount": 11,
                "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "Toffoli"],
            }
        },
        "name": "IonQ",
        "status": "UNAVAILABLE",
        "statusReason": "Under maintenance",
    }

    MOCK_QS1_SIMULATOR_1 = {
        "arn": AwsQuantumSimulatorArns.QS1,
        "properties": {
            "gateModelProperties": {
                "qubitCount": 23,
                "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "Toffoli"],
            }
        },
        "name": "integ_test_simulator",
        "status": "AVAILABLE",
    }

    MOCK_QS1_SIMULATOR_2 = {
        "arn": AwsQuantumSimulatorArns.QS1,
        "properties": {
            "gateModelProperties": {
                "qubitCount": 30,
                "supportedQuantumOperations": [
                    "CNOT",
                    "H",
                    "RZ",
                    "RY",
                    "RZ",
                    "Toffoli",
                    "Phase",
                    "CPhase",
                ],
            }
        },
        "name": "integ_test_simulator",
        "status": "UNAVAILABLE",
        "statusReason": "Temporary network issue",
    }


class MockS3:

    MOCK_S3_RESULT_1 = json.dumps(
        {
            "Measurements": [[0, 0], [0, 1], [0, 1], [0, 1]],
            "MeasuredQubits": [0, 1],
            "TaskMetadata": {
                "Id": "UUID_blah_1",
                "Status": "COMPLETED",
                "BackendArn": AwsQpuArns.RIGETTI,
                "Shots": 1000,
                "Ir": "{}",
            },
        }
    )

    MOCK_S3_RESULT_2 = json.dumps(
        {
            "Measurements": [[0, 0], [0, 0], [0, 0], [1, 1]],
            "MeasuredQubits": [0, 1],
            "TaskMetadata": {
                "Id": "UUID_blah_2",
                "Status": "COMPLETED",
                "BackendArn": AwsQpuArns.RIGETTI,
                "Shots": 1000,
                "Ir": "{}",
            },
        }
    )

    MOCK_S3_RESULT_3 = json.dumps(
        {
            "TaskMetadata": {
                "Id": "1231231",
                "Status": "COMPLETED",
                "BackendArn": "test_arn",
                "BackendTranslation": "...",
                "Created": 1574140385.0697668,
                "Modified": 1574140388.6908717,
                "Shots": 100,
                "GateModelConfig": {"QubitCount": 6},
                "Ir": "{}",
            },
            "MeasurementProbabilities": {"011000": 0.9999999999999982},
            "MeasuredQubits": [0, 1],
        }
    )

    MOCK_S3_RESULT_4 = json.dumps(
        {
            "Solutions": [[-1, -1, -1, -1], [1, -1, 1, 1], [1, -1, -1, 1]],
            "VariableCount": 4,
            "Values": [0.0, 1.0, 2.0],
            "SolutionCounts": None,
            "ProblemType": "ising",
            "DWaveMetadata": {
                "ActiveVariables": [0],
                "Timing": {
                    "QpuSamplingTime": 1575,
                    "QpuAnnealTimePerSample": 20,
                    "QpuReadoutTimePerSample": 274,
                    "QpuAccessTime": 10917,
                    "QpuAccessOverheadTime": 3382,
                    "QpuProgrammingTime": 9342,
                    "QpuDelayTimePerSample": 21,
                    "TotalPostProcessingTime": 117,
                    "PostProcessingOverheadTime": 117,
                    "TotalRealTime": 10917,
                    "RunTimeChip": 1575,
                    "AnnealTimePerRun": 20,
                    "ReadoutTimePerRun": 274,
                },
            },
            "TaskMetadata": {
                "Id": "UUID_blah_1",
                "Status": "COMPLETED",
                "BackendArn": AwsQpuArns.DWAVE,
                "Shots": 5,
            },
        }
    )


def run_and_assert(
    aws_quantum_task_mock,
    device,
    default_shots,
    default_timeout,
    default_poll_interval,
    circuit,
    s3_destination_folder,
    shots,  # Treated as positional arg
    poll_timeout_seconds,  # Treated as positional arg
    poll_interval_seconds,  # Treated as positional arg
    extra_args,
    extra_kwargs,
):
    task_mock = Mock()
    aws_quantum_task_mock.return_value = task_mock

    run_args = []
    if shots is not None:
        run_args.append(shots)
    if poll_timeout_seconds is not None:
        run_args.append(poll_timeout_seconds)
    if poll_interval_seconds is not None:
        run_args.append(poll_interval_seconds)
    run_args += extra_args if extra_args else []

    run_kwargs = extra_kwargs or {}

    task = device.run(circuit, s3_destination_folder, *run_args, **run_kwargs)
    assert task == task_mock

    create_args = [shots if shots is not None else default_shots]
    create_args += extra_args if extra_args else []

    create_kwargs = extra_kwargs or {}
    create_kwargs.update(
        {
            "poll_timeout_seconds": poll_timeout_seconds
            if poll_timeout_seconds is not None
            else default_timeout,
            "poll_interval_seconds": poll_interval_seconds
            if poll_interval_seconds is not None
            else default_poll_interval,
        }
    )
    aws_quantum_task_mock.assert_called_with(
        device._aws_session,
        device.arn,
        circuit,
        s3_destination_folder,
        *create_args,
        **create_kwargs
    )
