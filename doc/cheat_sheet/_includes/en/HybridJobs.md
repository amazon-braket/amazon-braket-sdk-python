| Imports | `from braket.aws import AwsQuantumJob`<br>`from braket.jobs import hybrid_job` |
| Create a job | `job = AwsQuantumJob.create(arn, source_module="algorithm_script.py", entry_point="algorithm_script:start_here", wait_until_complete=True)` |
| Jobs queue position | `job.queue_position()` |
| `@hybrid_job` decorator | `@hybrid_job(device=None, local=True)`<br>`def my_function(): ...` |
| Job configuration | `@hybrid_job(device=arn, instance_config=InstanceConfig(instanceType="ml.m5.large"))` |
| Local debugging | `@hybrid_job(device=None, local=True)` |
| Log metrics | `log_metric(metric_name, value, iteration_number)` |
