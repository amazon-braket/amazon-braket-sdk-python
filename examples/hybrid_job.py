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

from braket.aws import AwsDevice
from braket.circuits import Circuit, FreeParameter, observables
from braket.devices import Devices
from braket.jobs import get_job_device_arn, hybrid_job
from braket.jobs.metrics import log_metric


@hybrid_job(
    device=Devices.Amazon.SV1,
    wait_until_complete=True,
    # If you want to run the job in a device reservation window,
    # change the device to the one you've reserved,
    # uncomment the following line and fill in your reservation ARN
    # reservation_arn="<reservation ARN>"
)
def run_hybrid_job(num_tasks=1):
    # declare AwsDevice within the hybrid job
    device = AwsDevice(get_job_device_arn())

    # create a parametric circuit
    circ = Circuit()
    circ.rx(0, FreeParameter("theta"))
    circ.cnot(0, 1)
    circ.expectation(observable=observables.X(0))

    # initial parameter
    theta = 0.0

    for i in range(num_tasks):
        # run task, specifying input parameter
        task = device.run(circ, shots=100, inputs={"theta": theta})
        exp_val = task.result().values[0]

        # modify the parameter (e.g. gradient descent)
        theta += exp_val

        log_metric(metric_name="exp_val", value=exp_val, iteration_number=i)

    return {"final_theta": theta, "final_exp_val": exp_val}


job = run_hybrid_job(num_tasks=5)
print(job.result())
