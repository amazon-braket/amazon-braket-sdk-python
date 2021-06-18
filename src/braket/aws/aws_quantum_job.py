# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from typing import Any, Dict, List, Union

from braket.aws.aws_session import AwsSession
from braket.jobs.config import (
    CheckpointConfig,
    InstanceConfig,
    OutputDataConfig,
    StoppingCondition,
    VpcConfig,
)
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
        image_uri: str = "Base Image URI",
        source_dir: str = None,
        # TODO: Extract image_uri_type from image_uri for job_name.
        # TODO: Before passing the job_name to other parameters append timestamp to it.
        job_name: str = None,
        code_location: str = None,
        role_arn: str = None,
        wait: bool = False,
        priority_access_device_arn: str = None,
        hyper_parameters: Dict[str, Any] = None,
        metric_definitions: List[MetricDefinition] = None,
        input_data_config: Union[Any] = None,
        instance_config: InstanceConfig = InstanceConfig(),
        stopping_condition: StoppingCondition = StoppingCondition(),
        output_data_config: OutputDataConfig = OutputDataConfig(),
        copy_checkpoints_from_job: str = None,
        checkpoint_config: CheckpointConfig = CheckpointConfig(),
        vpc_config: VpcConfig = None,
        tags: Dict[str, str] = None,
        *args,
        **kwargs,
    ) -> AwsQuantumJob:
        """Creates a job by invoking the Braket CreateJob API.

        Args:
            aws_session (AwsSession): AwsSession to connect to AWS with.

            entry_point (str): str specifying the 'module' or 'module:method' to be executed as
                an entry point for the job.

            image_uri (str): str specifying the ECR image to use for executing the job.
                `image_uris.retrieve()` function may be used for retrieving the ECR image uris
                for the containers supported by Braket (default: <Braket base image_uri>).

            source_dir (str): Path (absolute, relative or an S3 URI) to a directory with any
                other source code dependencies aside from the entry point file. If `source_dir`
                is an S3 URI, it must point to a tar.gz file. Structure within this directory are
                preserved when executing on Amazon Braket. (default: None).

            job_name (str): str representing the name with which the job will be created.
                (default: {image_uri_type}-{timestamp})

            code_location (str): The S3 prefix URI where custom code will be uploaded.
                (default: 's3://{default_bucket_name}/jobs/{job_name}/source')

            role_arn (str): str representing the IAM role arn to be used for executing the
                script. (default: IAM role returned by get_execution_role())

            wait (bool): bool representing whether we should wait until the job completes.
                This would tail the job logs as it waits.

            priority_access_device_arn (str): ARN for the AWS device which should have priority
                access for the execution of this job.

            hyper_parameters (Dict[str, Any]): Hyperparameters that will be made accessible to
                the job. The hyperparameters are made accessible as a Dict[str, str] to the
                job. For convenience, this accepts other types for keys and values, but
                `str()` will be called to convert them before being passed on. (default: None)

            metric_definitions (List[MetricDefinition]): A list of MetricDefinitions that
                defines the metric(s) used to evaluate the training jobs. (default: None)

            input_data_config (Union[Any]): Information about the training data.

            instance_config (InstanceConfig): Configuration of the instances to be used for
                executing the job. (default: InstanceConfig(instanceType='ml.m5.large',
                instanceCount=1, volumeSizeInGB=30, volumeKmsKey=None))

            stopping_condition (StoppingCondition): Conditions denoting when the job should be
                forcefully stopped.
                (default: StoppingCondition(maxRuntimeInSeconds=5 * 24 * 60 * 60,
                maxTaskLimit=100,000))

            output_data_config (OutputDataConfig): Configuration specifying the location for
                the output of the job.
                (default:OutputDataConfig(s3Path=s3://{default_bucket_name}/jobs/{job_name}/output,
                kmsKeyId=None))

            copy_checkpoints_from_job (str): str specifying the job name whose checkpoint you wish
                to use in the current job. Specifying this value will copy over the checkpoint
                data from `use_checkpoints_from_job`'s checkpoint_config s3Uri to the current job's
                checkpoint_config s3Uri, making it available at checkpoint_config.localPath during
                the job execution.

            checkpoint_config (CheckpointConfig): Configuration specifying the location where
                checkpoint data would be stored.
                (default: CheckpointConfig(localPath='/opt/jobs/checkpoints',
                s3Uri='s3://{default_bucket_name}/jobs/{job_name}/checkpoints'))

            vpc_config (VpcConfig): Configuration specifying the security groups and subnets
                to use for running the job. (default: None)

            tags (Dict[str, str]): Dict specifying the Key-Value pairs to tag the quantum job with.
                (default: None)

        Returns:
            AwsQuantumJob: Job tracking the execution on Amazon Braket.
        """
        # TODO: if entry_point file is not provided, then we raise the error.
        # TODO: if job_name is None, then we set it to default_job_name
        # TODO: if code_location is not provided by the customer, then we default it with the
        # bucket_name with we get from the AwsSession object.
        # TODO: Decide on where default_bucket_name should be defined. If bucket is not present
        # in the customer's account then raise ValidationException.
        # TODO: call getExecutionRole() from aws_session.py

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

    @staticmethod
    def _aws_session_for_job_arn(job_arn: str) -> AwsSession:
        """Get an AwsSession for the Job ARN. The AWS session should be in the region of the task.

        Args:
            job_arn (str): The ARN for the quantum job.

        Returns:
            AwsSession: `AwsSession` object with default `boto_session` in job's region.
        """

    @property
    def arn(self) -> str:
        """Returns the job arn corresponding to the job"""

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
