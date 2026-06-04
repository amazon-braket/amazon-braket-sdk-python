| Imports | `from braket.aws import AwsQuantumJob`<br>`from braket.devices import Devices`<br>`from braket.jobs import hybrid_job, save_job_result`<br>`from braket.jobs.metrics import log_metric` |
| Create a script-based job | `job = AwsQuantumJob.create(Devices.Amazon.SV1, source_module="algorithm_script.py", entry_point="algorithm_script:start_here", wait_until_complete=True)` |
| Decorate an entry point<!-- LLM: . The job is created when the decorated function is called--> | `@hybrid_job(device=Devices.Amazon.SV1)`<br>`def my_job():`<br>`    return save_job_result({"theta": 0.5})` |
| Run the job (creates it) | `job = my_job()` |
| Run locally without creating an AWS job | `@hybrid_job(device=None, local=True)` |
| Add Python dependencies | `@hybrid_job(device=Devices.Amazon.SV1, dependencies="requirements.txt")` |
| Include extra source modules | `@hybrid_job(device=Devices.Amazon.SV1, include_modules=["my_module"])` |
| Pass input data | `@hybrid_job(device=Devices.Amazon.SV1, input_data="s3://my-bucket/input")` |
| Use a reservation | `@hybrid_job(device=Devices.IQM.Garnet, reservation_arn="<arn>")` |
| Record metrics inside the job | `log_metric(metric_name="loss", value=0.123, iteration_number=0)` |
| Retrieve the result | `job.result()` |
| Queue position | `job.queue_position()` |
