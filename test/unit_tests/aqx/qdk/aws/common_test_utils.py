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

from aqx.qdk.devices.qpu.qpu_status import QpuStatus
from aqx.qdk.devices.qpu.qpu_type import QpuType
from aqx.qdk.devices.quantum_simulator.quantum_simulator_status import QuantumSimulatorStatus
from aqx.qdk.devices.quantum_simulator.quantum_simulator_type import QuantumSimulatorType


class MockDevices:

    MOCK_RIGETTI_QPU_1 = {
        "arn": QpuType.RIGETTI,
        "qubitCount": 16,
        "connectivity": {"connectivityGraph": {"0": ["1", "2"], "1": ["0", "2"], "2": ["0", "1"]}},
        "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "T"],
        "name": "Rigetti",
        "status": QpuStatus.AVAILABLE,
    }

    MOCK_RIGETTI_QPU_2 = {
        "arn": QpuType.RIGETTI,
        "qubitCount": 30,
        "connectivity": {"connectivityGraph": {"0": ["1", "2"], "1": ["0", "2"], "2": ["0", "1"]}},
        "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "T", "S"],
        "name": "Rigetti",
        "status": QpuStatus.UNAVAILABLE,
        "statusReason": "Under maintenance",
    }

    MOCK_IONQ_QPU = {
        "arn": QpuType.IONQ,
        "qubitCount": 11,
        "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "Toffoli"],
        "name": "IonQ",
        "status": QpuStatus.UNAVAILABLE,
        "statusReason": "Under maintenance",
    }

    MOCK_QUEST_SIMULATOR_1 = {
        "arn": QuantumSimulatorType.QUEST,
        "qubitCount": 23,
        "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "Toffoli"],
        "name": "QuEST",
        "status": QuantumSimulatorStatus.AVAILABLE,
    }

    MOCK_QUEST_SIMULATOR_2 = {
        "arn": QuantumSimulatorType.QUEST,
        "qubitCount": 30,
        "supportedQuantumOperations": ["CNOT", "H", "RZ", "RY", "RZ", "Toffoli", "Phase", "CPhase"],
        "name": "QuEST",
        "status": QuantumSimulatorStatus.UNAVAILABLE,
        "statusReason": "Temporary network issue",
    }


class MockS3:

    MOCK_S3_RESULT_1 = json.dumps(
        {
            "StateVector": {"00": 0.19999, "01": 0.80000, "10": 0.00000, "11": 0.00001},
            "Measurements": [[0, 0], [0, 1], [0, 1], [0, 1]],
            "TaskMetadata": {
                "Id": "UUID_blah_1",
                "Status": "COMPLETED",
                "BackendArn": "Rigetti_Arn",
                "CwLogGroupArn": "blah",
                "Program": "....",
            },
        }
    )

    MOCK_S3_RESULT_2 = json.dumps(
        {
            "StateVector": {"00": 0.80000, "01": 0.00000, "10": 0.00000, "11": 0.19999},
            "Measurements": [[0, 0], [0, 0], [0, 0], [1, 1]],
            "TaskMetadata": {
                "Id": "UUID_blah_2",
                "Status": "COMPLETED",
                "BackendArn": "Rigetti_Arn",
                "CwLogGroupArn": "blah",
                "Program": "....",
            },
        }
    )
