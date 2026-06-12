| Task | Code |
|---|---|
| Imports | `from braket.aws import AwsQuantumJob`<br>`from braket.jobs import hybrid_job`<br>`from braket.jobs.metrics import log_metric` |
| Create a job from a script | `job = AwsQuantumJob.create(device=device_arn, source_module="algorithm_script.py", entry_point="algorithm_script:start_here", wait_until_complete=True)` |
| Queue position | `job.queue_position()` |
| Define a local hybrid job | `@hybrid_job(device=None, local=True)` |
| Define an AWS hybrid job | `@hybrid_job(device=device_arn)` |
| Add job dependencies | `@hybrid_job(device=device_arn, dependencies="requirements.txt")` |
| Include local modules | `@hybrid_job(device=device_arn, include_modules="my_module")` |
| Pass input data | `@hybrid_job(device=device_arn, input_data={"input": "data.csv"})` |
| Use a reservation ARN | `@hybrid_job(device=device_arn, reservation_arn=reservation_arn)` |
| Record Braket Hybrid Job metrics | `log_metric(metric_name="loss", value=loss, iteration_number=step)` |