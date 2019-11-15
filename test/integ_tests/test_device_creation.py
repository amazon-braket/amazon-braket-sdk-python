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

from aqx.qdk.aws.aws_qpu import AwsQpu
from aqx.qdk.aws.aws_quantum_simulator import AwsQuantumSimulator


def test_aws_qpu_actual(aws_session):
    qpu_arn = "integ_test_qdk_qpu_arn"
    qpu = AwsQpu(qpu_arn, aws_session=aws_session)
    assert qpu.arn == qpu_arn
    assert qpu.connectivity_graph == {"0": ["1", "2"], "1": ["0", "2"], "2": ["0", "1"]}
    assert qpu.name == "Rigetti"
    assert qpu.qubit_count == 16
    assert qpu.status == "AVAILABLE"
    assert qpu.status_reason == "Up and running"
    assert qpu.supported_quantum_operations == ["CNOT", "H", "RZ", "RY", "RZ", "T"]


def test_get_simulator_metadata_actual(aws_session):
    simulator_arn = "integ_test_qdk_simulator_arn"
    simulator = AwsQuantumSimulator(simulator_arn, aws_session=aws_session)
    assert simulator.arn == simulator_arn
    assert simulator.status_reason == "Under maintenance"
    assert simulator.status == "UNAVAILABLE"
    assert simulator.qubit_count == 30
    assert simulator.name == "QuEST"
    assert simulator.supported_quantum_operations == ["CNOT", "H", "RZ", "RY", "RZ", "T"]
