import time

import boto3

from braket.aws import AwsSession
from braket.aws.aws_quantum_job import AwsQuantumJob
from braket.jobs.config import StoppingCondition, OutputDataConfig, InputDataConfig, S3DataSource, DataSource, \
    InstanceConfig, CheckpointConfig

aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
s3_folder = (f"amazon-braket-{aws_account_id}", "annealing-test")
gamma_endpoint = "https://braket-gamma.us-west-2.amazonaws.com"
braket_client = boto3.client("braket", region_name="us-west-2", endpoint_url=gamma_endpoint)
aws_session = AwsSession(braket_client=braket_client)

bucket = f"amazon-braket-{aws_account_id}"
fake_job_name = "fake-job-name-0000"
s3_prefix = f"jobDevTests/{fake_job_name}"
job_script = "alpha_test_job/fancy_module/my_file.py"
f"s3://{bucket}/{s3_prefix}/script/{job_script}"

input_data = "inputdata.csv"
s3_client = boto3.client("s3")
input_object = f"{s3_prefix}/input/{input_data}"
s3_client.upload_file(input_data, bucket, input_object)

create_job_args = {
    "aws_session": aws_session,
    "entry_point": "alpha_test_job.fancy_module.my_file:start_here",
    "image_uri": "Base-Image-URI",
    "source_dir": "alpha_test_job",
    "job_name": None,
    "code_location": f"s3://{bucket}/{s3_prefix}/script",
    "role_arn": None,
    "wait": False,
    "priority_access_device_arn": "arn:aws:braket:::device/qpu/rigetti/Aspen-9",
    "hyper_parameters": {
        "user": "berdy",
        "bucket": f"s3://amazon-braket-318845237731",
    },
    # "metric_defintions": None,
    "input_data_config": [
        InputDataConfig(
            channelName="hellothere",
            dataSource=DataSource(
                s3DataSource=S3DataSource(
                    s3Uri=f"s3://{bucket}/{s3_prefix}/input",
                ),
            ),
        ),
    ],
    "instance_config": InstanceConfig(
        instanceType="ml.m5.large",
        instanceCount=1,
        volumeSizeInGb=1,
    ),
    "stopping_condition": StoppingCondition(
        maxRuntimeInSeconds=1200,
        maximumTaskLimit=10,
    ),
    "output_data_config": OutputDataConfig(
        s3Path=f"s3://{bucket}/{s3_prefix}/output",
    ),
    "copy_checkpoints_from_job": None,
    "checkpoint_config": CheckpointConfig(
        localPath="/opt/omega/checkpoints",
        s3Uri=f"s3://{bucket}/checkpoints",
    ),
    # "vpc_config": None,
    "tags": None,
}


job = AwsQuantumJob.create(**create_job_args)
arn = job._arn
# arn = "arn:aws:braket:us-west-2:318845237731:job/Base-Image-URI-20210625140940"

print(arn)
getJob = braket_client.get_job(jobArn=arn)
print(getJob)
status = None

while status not in ["FAILED", "COMPLETED"]:
    getJob = braket_client.get_job(jobArn=arn)
    print(status := getJob["status"])
    time.sleep(10)
