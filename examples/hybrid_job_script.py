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

import os

from braket.aws import AwsDevice, AwsQuantumJob
from braket.circuits import Circuit, FreeParameter, Observable
from braket.devices import Devices
from braket.jobs import save_job_result
from braket.jobs.metrics import log_metric


def run_hybrid_job(num_tasks: int):
    # use the device specified in the hybrid job
    device = AwsDevice(os.environ.get("AMZN_BRAKET_DEVICE_ARN"))

    # create a parametric circuit
    circ = Circuit()
    circ.rx(0, FreeParameter("theta"))
    circ.cnot(0, 1)
    circ.expectation(observable=Observable.X(), target=0)

    theta = 0.0  # initial parameter

    for i in range(num_tasks):
        task = device.run(circ, shots=100, inputs={"theta": theta})  # input parameters
        exp_val = task.result().values[0]

        theta += exp_val  # modify the parameter (possibly gradient descent)

        log_metric(metric_name="exp_val", value=exp_val, iteration_number=i)

    save_job_result({"final_theta": theta, "final_exp_val": exp_val})


if __name__ == "__main__":
    job = AwsQuantumJob.create(
        device=Devices.Amazon.SV1,  # choose priority device
        source_module="hybrid_job_script.py",  # specify file or directory with code to run
        entry_point="hybrid_job_script:run_hybrid_job",  # specify function to run
        hyperparameters={"num_tasks": 5},
    )
    print(job)
    print(job.result())