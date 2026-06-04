| Imports | `from braket.aws import AwsQuantumJob` |
| Create a job | `job = AwsQuantumJob.create(arn, source_module="algorithm_script.py", entry_point="algorithm_script:start_here", wait_until_complete=True)` |
| Queue position | `job.queue_position()` |
| Job decorator | `@hybrid_job(device=None, local=True)` |
| Records Braket Hybrid Job metrics | `log_metric(metric_name, value, iteration_number)` |
