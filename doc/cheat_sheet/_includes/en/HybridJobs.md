| Task | Snippet |
|---|---|
| Imports | `from braket.aws import AwsDevice, AwsQuantumJob`<br>`from braket.devices import Devices`<br>`from braket.jobs import get_job_device_arn, hybrid_job` |
| Create a script-based job | `job = AwsQuantumJob.create(device=Devices.Amazon.SV1, source_module="algorithm_script.py", entry_point="algorithm_script:run", wait_until_complete=True)` |
| Decorate an entry point | `@hybrid_job(device=Devices.Amazon.SV1, wait_until_complete=True)`<br>`def run_hybrid_job(num_tasks=1):`<br>`    device = AwsDevice(get_job_device_arn())` |
| Local decorator mode | `@hybrid_job(device=None, local=True)` |
| Pass dependencies | `@hybrid_job(device=Devices.Amazon.SV1, dependencies="requirements.txt")` |
| Use a reservation | `@hybrid_job(device=Devices.IonQ.Forte1, reservation_arn=reservation_arn)` |
| Log metrics inside a job | `from braket.jobs.metrics import log_metric`<br>`log_metric(metric_name="loss", value=loss, iteration_number=i)` |
| Read job output | `job.result()` |
| Queue position | `job.queue_position()` |
