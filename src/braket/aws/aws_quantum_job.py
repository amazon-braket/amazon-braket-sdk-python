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

from __future__ import annotations

import os.path
import re
import tarfile
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List

import boto3

from braket.aws.aws_session import AwsSession
from braket.jobs.config import (  # VpcConfig,
    CheckpointConfig,
    DeviceConfig,
    InputDataConfig,
    InstanceConfig,
    OutputDataConfig,
    PriorityAccessConfig,
    StoppingCondition,
)

# TODO: Have added metric file in metrics folder, but have to decide on the name for keep
# for the files, since all those metrics are retrieved from the CW.
from braket.jobs.metrics import MetricDefinition, MetricPeriod, MetricStatistic


class AwsQuantumJob:
    """Amazon Braket implementation of a quantum job."""

    @classmethod
    def create(
        cls,
        aws_session: AwsSession,
        entry_point: str,
        # TODO: Replace with the correct default image name.
        # This image_uri will be retrieved from `image_uris.retreive()` which will a different file
        # in the `jobs` folder and the function defined in it.
        image_uri: str = "Base-Image-URI",
        source_dir: str = None,
        # TODO: If job_name is specified by customer then we don't append timestamp to it.
        # TODO: Else, we extract image_uri_type from image_uri for job_name and append timestamp.
        # TODO: timestamp should be in epoch or any other date format we decide on like `yyyy-mm-dd`
        job_name: str = None,
        code_location: str = None,
        role_arn: str = None,
        wait_until_complete: bool = False,
        priority_access_device_arn: str = None,
        hyper_parameters: Dict[str, Any] = None,
        metric_definitions: List[MetricDefinition] = None,
        input_data_config: List[InputDataConfig] = None,
        instance_config: InstanceConfig = InstanceConfig(),
        stopping_condition: StoppingCondition = StoppingCondition(),
        output_data_config: OutputDataConfig = OutputDataConfig(),
        copy_checkpoints_from_job: str = None,
        checkpoint_config: CheckpointConfig = CheckpointConfig(),
        # vpc_config: VpcConfig = None,
        tags: Dict[str, str] = None,
        *args,
        **kwargs,
    ) -> "AwsQuantumJob":
        """Creates a job by invoking the Braket CreateJob API.

        Args:
            aws_session (AwsSession): AwsSession to connect to AWS with.

            entry_point (str): str specifying the 'module' or 'module:method' to be executed as
                an entry point for the job.

            image_uri (str): str specifying the ECR image to use for executing the job.
                `image_uris.retrieve()` function may be used for retrieving the ECR image uris
                for the containers supported by Braket. Default = `<Braket base image_uri>`.

            source_dir (str): Path (absolute, relative or an S3 URI) to a directory with any
                other source code dependencies aside from the entry point file. If `source_dir`
                is an S3 URI, it must point to a tar.gz file. Structure within this directory are
                preserved when executing on Amazon Braket. Default = `None`.

            job_name (str): str representing the name with which the job will be created.
                Default = `{image_uri_type}-{timestamp}`.

            code_location (str): The S3 prefix URI where custom code will be uploaded.
                Default = `'s3://{default_bucket_name}/jobs/{job_name}/source'`.

            role_arn (str): str representing the IAM role arn to be used for executing the
                script. Default = `IAM role returned by get_execution_role()`.

            wait_until_complete (bool): bool representing whether we should wait until the job
                completes. This would tail the job logs as it waits. Default = `False`.

            # TODO: wait until complete polling parameters?

            priority_access_device_arn (str): ARN for the AWS device which should have priority
                access for the execution of this job. Default = `None`.

            hyper_parameters (Dict[str, Any]): Hyperparameters that will be made accessible to
                the job. The hyperparameters are made accessible as a Dict[str, str] to the
                job. For convenience, this accepts other types for keys and values, but
                `str()` will be called to convert them before being passed on. Default = `None`.

            metric_definitions (List[MetricDefinition]): A list of MetricDefinitions that
                defines the metric(s) used to evaluate the training jobs. Default = `None`.

            input_data_config (Union[Any]): Information about the training data. Default = `None`.

            instance_config (InstanceConfig): Configuration of the instances to be used for
                executing the job. Default = `InstanceConfig(instanceType='ml.m5.large',
                instanceCount=1, volumeSizeInGB=30, volumeKmsKey=None)`.

            stopping_condition (StoppingCondition): Conditions denoting when the job should be
                forcefully stopped.
                Default = `StoppingCondition(maxRuntimeInSeconds=5 * 24 * 60 * 60,
                maxTaskLimit=100,000)`.

            output_data_config (OutputDataConfig): Configuration specifying the location for
                the output of the job.
                Default = `OutputDataConfig(s3Path=s3://{default_bucket_name}/jobs/{job_name}/
                output, kmsKeyId=None)`.

            copy_checkpoints_from_job (str): str specifying the job name whose checkpoint you wish
                to use in the current job. Specifying this value will copy over the checkpoint
                data from `use_checkpoints_from_job`'s checkpoint_config s3Uri to the current job's
                checkpoint_config s3Uri, making it available at checkpoint_config.localPath during
                the job execution.

            checkpoint_config (CheckpointConfig): Configuration specifying the location where
                checkpoint data would be stored.
                Default = `CheckpointConfig(localPath='/opt/jobs/checkpoints',
                s3Uri=None)`.

            vpc_config (VpcConfig): Configuration specifying the security groups and subnets
                to use for running the job. Default = `None`.

            tags (Dict[str, str]): Dict specifying the Key-Value pairs to tag the quantum job with.
                Default = `None`.

        Returns:
            AwsQuantumJob: Job tracking the execution on Amazon Braket.
        """
        job_name = job_name or AwsQuantumJob.generate_default_job_name(image_uri)
        role_arn = role_arn or aws_session.get_execution_role()
        hyper_parameters = hyper_parameters or {}
        device_config = DeviceConfig(
            priorityAccess=PriorityAccessConfig(
                devices=[arn for arn in [priority_access_device_arn] if arn]
            )
        )
        default_bucket = aws_session.default_bucket()
        code_location = code_location or aws_session.construct_s3_uri(
            default_bucket, job_name, "script"
        )
        input_data_config = input_data_config or []
        output_data_config = output_data_config or OutputDataConfig()
        if not output_data_config.s3Path:
            output_data_config.s3Path = aws_session.construct_s3_uri(
                default_bucket, job_name, "output"
            )
        checkpoint_config = checkpoint_config or CheckpointConfig()
        if not checkpoint_config.s3Uri:
            checkpoint_config.s3Uri = aws_session.construct_s3_uri(
                default_bucket, job_name, "checkpoints"
            )
        tarred_source_dir = AwsQuantumJob._process_source_dir(
            source_dir, aws_session, code_location
        )
        stopping_condition = stopping_condition or StoppingCondition()

        create_job_kwargs = {
            "jobName": job_name,
            "roleArn": role_arn,
            "algorithmSpecification": {
                "scriptModeConfig": {
                    "entryPoint": entry_point,
                    "s3Uri": f"{code_location}/{tarred_source_dir}",
                    "compressionType": "GZIP",
                }
            },
            "inputDataConfig": [asdict(input_channel) for input_channel in input_data_config],
            "instanceConfig": asdict(instance_config),
            "outputDataConfig": asdict(output_data_config),
            "checkpointConfig": asdict(checkpoint_config),
            "deviceConfig": asdict(device_config),
            "hyperParameters": hyper_parameters,
            "stoppingCondition": asdict(stopping_condition),
        }

        job_arn = aws_session.create_job(**create_job_kwargs)
        return AwsQuantumJob(job_arn, aws_session)

    def __init__(
        self,
        arn: str,
        aws_session: AwsSession = None,
    ):
        """
        Args:
            arn (str): The ARN of the job.
            aws_session (AwsSession, optional): The `AwsSession` for connecting to AWS services.
                Default is `None`, in which case an `AwsSession` object will be created with the
                region of the job.
        """
        self._arn: str = arn
        self._aws_session: AwsSession = aws_session or AwsQuantumJob._aws_session_for_job_arn(
            job_arn=arn
        )

    @staticmethod
    def _aws_session_for_job_arn(job_arn: str) -> AwsSession:
        """Get an AwsSession for the Job ARN. The AWS session should be in the region of the task.
        Args:
            job_arn (str): The ARN for the quantum job.
        Returns:
            AwsSession: `AwsSession` object with default `boto_session` in job's region.
        """
        try:
            job_region = re.match(r"^arn:aws:braket:([\w-]+):\d+:job/", job_arn).group(1)
        except AttributeError:
            raise ValueError(f"Not a valid job arn: {job_arn}")
        boto_session = boto3.Session(region_name=job_region)
        return AwsSession(boto_session=boto_session)

    # following AwsQuantumTask precedent for `id` over `arn`
    # is that what we want?
    @property
    def id(self) -> str:
        """str: The ARN of the quantum task."""
        return self._arn

    @staticmethod
    def generate_default_job_name(image_uri_type: str):
        return f"{image_uri_type}-{datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')}"

    @property
    def arn(self) -> str:  # do we want arn or id or both?
        """Returns the job arn corresponding to the job"""
        return self._arn

    @property
    def state(self) -> str:
        """Returns the status for the job"""

    def logs(self) -> None:
        """Prints the logs from cloudwatch to stdout"""

    def metadata(self) -> Dict[str, Any]:
        """Returns the job metadata defined in Amazon Braket (uses the GetJob API call).

        Returns:
            Dict[str, Any]: Dict specifying the job metadata defined in Amazon Braket.
        """

    def metrics(
        self,
        metric_names: List[str] = None,
        period: MetricPeriod = MetricPeriod.ONE_MINUTE,
        statistic: MetricStatistic = MetricStatistic.AVG,
    ) -> Dict[str, Any]:

        # TODO: We might have to update the method signature & associated enums based when we
        # integrate with metric retrieval classes.

        """Queries cloudwatch to retrieve the metric values for the specified metric_names
        for the job.

        Note: The function definition here is subject to change depending on our metric
        strategy for the console.

        Args:
            metric_names (List[str]): Metric names to retrieve for the job.
            period (MetricPeriod): Period over which the cloudwatch metric is aggregated.
            statistic (MetricStatistic): Metric data aggregation to use over the specified period.

        Returns:
            Dict[str, Any]: Dict containing the metric information represented with the keys
                "timestamp", "metric_name" and "value".
        """

    def cancel(self) -> str:
        """Cancels the job.

        Returns:
            str: Representing the status of the job.
        """

    def result(self) -> Dict[str, Any]:
        """Retrieves the job result persisted using save_job_result() function.

        Returns:
            Dict[str, Any]: Dict specifying the job results.
        """

    def download_results(self, extract_to=None) -> None:
        """Downloads the results from the job output S3 bucket and extracts the tar.gz
        bundle to the location specified by 'extract_to'. If no location is specified,
        the results are extracted to the current directory.

        Args:
            extract_to (str): Location where results will be extracted.
        """

    def __repr__(self) -> str:
        return f"AwsQuantumJob('id/jobArn':'{self.id}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, AwsQuantumJob):
            return self.id == other.id
        return NotImplemented  # should this be False?

    def __hash__(self) -> int:
        return hash(self.id)

    @staticmethod
    def _process_source_dir(source_dir, aws_session, code_location):
        tarred_source_dir = f"{source_dir.split('/')[-1]}.tar.gz"
        if source_dir.startswith("s3://"):
            aws_session.copy_source(source_dir, code_location)
        else:
            with tarfile.open(tarred_source_dir, "w:gz") as tar:
                tar.add(source_dir, arcname=os.path.basename(source_dir))
            aws_session.upload_source_to_s3(tarred_source_dir, code_location)
            os.remove(tarred_source_dir)
        return tarred_source_dir
