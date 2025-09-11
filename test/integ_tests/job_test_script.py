# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from braket.aws import AwsDevice
from braket.circuits import Circuit
from braket.jobs import (
    get_hyperparameters,
    get_job_device_arn,
    save_job_checkpoint,
    save_job_result,
)
from braket.jobs_data import PersistedJobDataFormat


def start_here():
    hyperparameters = get_hyperparameters()

    if hyperparameters["test_case"] == "completed":
        completed_job_script()
    else:
        failed_job_script()


def failed_job_script():
    print("Test job started!!!!!")
    open("fake_file")


def completed_job_script():
    print("Test job started!!!!!")

    # Use the device declared in the Orchestration Script
    device = AwsDevice(get_job_device_arn())

    bell = Circuit().h(0).cnot(0, 1)
    for _ in range(3):
        task = device.run(bell, shots=10)
        print(task.result().measurement_counts)
        save_job_result({"converged": True, "energy": -0.2})
        save_job_checkpoint({"some_data": "abc"}, checkpoint_file_suffix="plain_data")
        save_job_checkpoint({"some_data": "abc"}, data_format=PersistedJobDataFormat.PICKLED_V4)

    print("Test job completed!!!!!")


def job_helper():
    print("import successful!")
    return {"status": "SUCCESS"}
