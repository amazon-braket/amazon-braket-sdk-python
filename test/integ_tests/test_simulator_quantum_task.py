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

from aqx.qdk.aws import AwsQuantumSimulator, AwsQuantumSimulatorArns
from aqx.qdk.circuits import Circuit

BUCKET_NAME = "simulator-output-bucket"
FILENAME = "integ-tests/test_task_simulator.json"

# TODO: sad path once we have exception types in API


def test_simulator_quantum_task(aws_session):

    device = AwsQuantumSimulator(AwsQuantumSimulatorArns.QS1, aws_session)
    s3_destination_folder = (BUCKET_NAME, FILENAME)

    bell = Circuit().h(0).cnot(0, 1)

    circ = Circuit()
    circ.add(bell)
    circ.add(bell, [1, 2])
    circ.add(bell, [2, 3])

    task = device.run(bell, s3_destination_folder)

    result = task.result()

    assert 0.40 < result.measurement_probabilities["00"] < 0.60
    assert 0.40 < result.measurement_probabilities["11"] < 0.60
