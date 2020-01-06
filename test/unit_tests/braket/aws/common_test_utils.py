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

from braket.aws.aws_qpu_arns import AwsQpuArns
from braket.aws.aws_quantum_simulator_arns import AwsQuantumSimulatorArns


class MockDevices:

    MOCK_RIGETTI_QPU_1 = {
        "arn": AwsQpuArns.RIGETTI,
        "qubitCount": 16,
        "connectivity": {"connectivityGraph": {"0": ["1", "2"], "1": ["0", "2"], "2": ["0", "1"]}},
        "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "T"],
        "name": "Rigetti",
        "status": "AVAILABLE",
    }

    MOCK_RIGETTI_QPU_2 = {
        "arn": AwsQpuArns.RIGETTI,
        "qubitCount": 30,
        "connectivity": {"connectivityGraph": {"0": ["1", "2"], "1": ["0", "2"], "2": ["0", "1"]}},
        "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "T", "S"],
        "name": "Rigetti",
        "status": "UNAVAILABLE",
        "statusReason": "Under maintenance",
    }

    MOCK_IONQ_QPU = {
        "arn": AwsQpuArns.IONQ,
        "qubitCount": 11,
        "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "Toffoli"],
        "name": "IonQ",
        "status": "UNAVAILABLE",
        "statusReason": "Under maintenance",
    }

    MOCK_QS1_SIMULATOR_1 = {
        "arn": AwsQuantumSimulatorArns.QS1,
        "qubitCount": 23,
        "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "Toffoli"],
        "name": "integ_test_simulator",
        "status": "AVAILABLE",
    }

    MOCK_QS1_SIMULATOR_2 = {
        "arn": AwsQuantumSimulatorArns.QS1,
        "qubitCount": 30,
        "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "Toffoli", "Phase", "CPhase"],
        "name": "integ_test_simulator",
        "status": "UNAVAILABLE",
        "statusReason": "Temporary network issue",
    }


class MockS3:

    MOCK_S3_RESULT_1 = json.dumps(
        {
            "StateVector": {"00": [0.2, 0.2], "01": [0.3, 0.1], "10": [0.1, 0.3], "11": [0.2, 0.2]},
            "Measurements": [[0, 0], [0, 1], [0, 1], [0, 1]],
            "TaskMetadata": {
                "Id": "UUID_blah_1",
                "Status": "COMPLETED",
                "BackendArn": AwsQpuArns.RIGETTI,
                "CwLogGroupArn": "blah",
                "Program": "....",
            },
        }
    )

    MOCK_S3_RESULT_2 = json.dumps(
        {
            "StateVector": {"00": [0.2, 0.2], "01": [0.3, 0.1], "10": [0.1, 0.3], "11": [0.2, 0.2]},
            "Measurements": [[0, 0], [0, 0], [0, 0], [1, 1]],
            "TaskMetadata": {
                "Id": "UUID_blah_2",
                "Status": "COMPLETED",
                "BackendArn": AwsQpuArns.RIGETTI,
                "CwLogGroupArn": "blah",
                "Program": "....",
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
            },
            "MeasurementProbabilities": {"011000": 0.9999999999999982},
        }
    )
