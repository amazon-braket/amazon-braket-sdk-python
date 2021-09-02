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

import importlib
import os.path
import tarfile
import tempfile
import time
from dataclasses import asdict
from enum import Enum
from typing import Any, Dict, List

import boto3

from braket.aws.aws_session import AwsSession
from braket.jobs import logs
from braket.jobs.config import (
    CheckpointConfig,
    DeviceConfig,
    InputDataConfig,
    InstanceConfig,
    OutputDataConfig,
    StoppingCondition,
    VpcConfig,
)
from braket.jobs.metrics_data.cwl_insights_metrics_fetcher import CwlInsightsMetricsFetcher

# TODO: Have added metric file in metrics folder, but have to decide on the name for keep
# for the files, since all those metrics are retrieved from the CW.
from braket.jobs.metrics_data.definitions import MetricDefinition, MetricStatistic, MetricType
from braket.jobs.serialization import deserialize_values
from braket.jobs_data import PersistedJobData


class AwsQuantumJob:
    """Amazon Braket implementation of a quantum job."""

    NO_RESULT_TERMINAL_STATES = {"FAILED", "CANCELLED"}
    RESULTS_READY_STATES = {"COMPLETED"}
    TERMINAL_STATES = RESULTS_READY_STATES.union(NO_RESULT_TERMINAL_STATES)
    DEFAULT_RESULTS_POLL_TIMEOUT = 864000
    DEFAULT_RESULTS_POLL_INTERVAL = 1
    RESULTS_FILENAME = "results.json"
    RESULTS_TAR_FILENAME = "model.tar.gz"
    DEFAULT_IMAGE_NAME = "Base-Image-URI"
    LOG_GROUP = "/aws/braket/jobs"

    class LogState(Enum):
        TAILING = "tailing"
        JOB_COMPLETE = "job_complete"
        COMPLETE = "complete"

    @classmethod
    def create(
        cls,
        entry_point: str,
        device_arn: str,
        source_dir: str = None,
        image_uri: str = None,
        job_name: str = None,
        code_location: str = None,
        role_arn: str = None,
        wait_until_complete: bool = False,
        hyper_parameters: Dict[str, Any] = None,
        metric_definitions: List[MetricDefinition] = None,
        input_data_config: List[InputDataConfig] = None,
        instance_config: InstanceConfig = None,
        stopping_condition: StoppingCondition = None,
        output_data_config: OutputDataConfig = None,
        copy_checkpoints_from_job: str = None,
        checkpoint_config: CheckpointConfig = None,
        vpc_config: VpcConfig = None,
        tags: Dict[str, str] = None,
        aws_session: AwsSession = None,
        *args,
        **kwargs,
    ) -> AwsQuantumJob:
        """Creates a job by invoking the Braket CreateJob API.

        Args:
            entry_point (str): str specifying the 'module' or 'module:method' to be executed as
                an entry point for the job. The entry_point should be specified relative to
                the source_dir. If source_dir is not provided then all the required modules
                for execution of entry_point should be within the folder containing the
                entry_point script.

                For example,
                if `entry_point = foo.bar.my_script:func`. Then all the required modules
                should be present within the `foo` or `bar` folder.

            device_arn (str): ARN for the AWS device which will be primarily
                accessed for the execution of this job.

            source_dir (str): Path (absolute, relative or an S3 URI) to a directory with any
                other source code dependencies aside from the entry point file. If `source_dir`
                is an S3 URI, it must point to a tar.gz file. Structure within this directory are
                preserved when executing on Amazon Braket. Default = `None`.

            image_uri (str): str specifying the ECR image to use for executing the job.
                `image_uris.retrieve()` function may be used for retrieving the ECR image uris
                for the containers supported by Braket. Default = `<Braket base image_uri>`.

            job_name (str): str representing the name with which the job will be created.
                Default = `{image_uri_type}-{timestamp}`.

            code_location (str): The S3 prefix URI where custom code will be uploaded.
                Default = `'s3://{default_bucket_name}/jobs/{job_name}/source'`.

            role_arn (str): str representing the IAM role arn to be used for executing the
                script. Default = `IAM role returned by get_execution_role()`.

            wait_until_complete (bool): bool representing whether we should wait until the job
                completes. This would tail the job logs as it waits. Default = `False`.

            hyper_parameters (Dict[str, Any]): Hyperparameters that will be made accessible to
                the job. The hyperparameters are made accessible as a Dict[str, str] to the
                job. For convenience, this accepts other types for keys and values, but
                `str()` will be called to convert them before being passed on. Default = `None`.

            metric_definitions (List[MetricDefinition]): A list of MetricDefinitions that
                defines the metric(s) used to evaluate the training jobs. Default = `None`.

            input_data_config (List[InputDataConfig]): Information about the training data.
                Default = `None`.

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

            copy_checkpoints_from_job (str): str specifying the job arn whose checkpoint you wish
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


            aws_session (AwsSession): AwsSession to connect to AWS with. Default = `AwsSession()`

        Returns:
            AwsQuantumJob: Job tracking the execution on Amazon Braket.

        Raises:
            ValueError: Raises ValueError if the parameters are not valid.
        """
        aws_session = aws_session or AwsSession()
        device_config = DeviceConfig(devices=[device_arn])
        job_name = job_name or AwsQuantumJob._generate_default_job_name(
            image_uri or AwsQuantumJob.DEFAULT_IMAGE_NAME
        )
        role_arn = role_arn or aws_session.get_execution_role()
        hyper_parameters = hyper_parameters or {}
        input_data_config = input_data_config or []
        instance_config = instance_config or InstanceConfig()
        stopping_condition = stopping_condition or StoppingCondition()
        output_data_config = output_data_config or OutputDataConfig()
        checkpoint_config = checkpoint_config or CheckpointConfig()
        # tags = tags or {}
        default_bucket = aws_session.default_bucket()
        code_location = code_location or aws_session.construct_s3_uri(
            default_bucket,
            "jobs",
            job_name,
            "script",
        )
        algorithm_specification = {
            "scriptModeConfig": {
                "entryPoint": entry_point,
                "s3Uri": f"{code_location}/source.tar.gz",
                "compressionType": "GZIP",
            }
        }
        if image_uri:
            algorithm_specification["containerImage"] = {"uri": image_uri}
        if not output_data_config.s3Path:
            output_data_config.s3Path = aws_session.construct_s3_uri(
                default_bucket,
                "jobs",
                job_name,
                "output",
            )
        if not checkpoint_config.s3Uri:
            checkpoint_config.s3Uri = aws_session.construct_s3_uri(
                default_bucket,
                "jobs",
                job_name,
                "checkpoints",
            )
        if copy_checkpoints_from_job:
            checkpoints_to_copy = aws_session.get_job(copy_checkpoints_from_job)[
                "checkpointConfig"
            ]["s3Uri"]
            aws_session.copy_s3_directory(checkpoints_to_copy, checkpoint_config.s3Uri)

        AwsQuantumJob._process_source_dir(
            entry_point,
            source_dir,
            aws_session,
            code_location,
        )

        create_job_kwargs = {
            "jobName": job_name,
            "roleArn": role_arn,
            "algorithmSpecification": algorithm_specification,
            "inputDataConfig": [asdict(input_channel) for input_channel in input_data_config],
            "instanceConfig": asdict(instance_config),
            "outputDataConfig": asdict(output_data_config),
            "checkpointConfig": asdict(checkpoint_config),
            "deviceConfig": asdict(device_config),
            "hyperParameters": hyper_parameters,
            "stoppingCondition": asdict(stopping_condition),
            # TODO: uncomment when tags works
            # "tags": tags,
        }

        if vpc_config:
            create_job_kwargs["vpcConfig"] = vpc_config

        job_arn = aws_session.create_job(**create_job_kwargs)
        job = AwsQuantumJob(job_arn, aws_session)

        if wait_until_complete:
            print(f"Initializing Braket Job: {job_arn}")
            job.logs(wait=True)

        return job

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
        if aws_session:
            if not self._is_valid_aws_session_region_for_job_arn(aws_session, arn):
                raise ValueError(
                    "The aws session region does not match the region for the supplied arn"
                )
            self._aws_session = aws_session
        else:
            self._aws_session = AwsQuantumJob._default_session_for_job_arn(arn)
        self._metadata = {}

    @staticmethod
    def _is_valid_aws_session_region_for_job_arn(aws_session: AwsSession, job_arn: str) -> bool:
        """bool: bool indicating whether the aws_session region matches the job_arn region"""
        job_region = job_arn.split(":")[3]
        return job_region == aws_session.braket_client.meta.region_name

    @staticmethod
    def _default_session_for_job_arn(job_arn: str) -> AwsSession:
        """Get an AwsSession for the Job ARN. The AWS session should be in the region of the job.

        Args:
            job_arn (str): The ARN for the quantum job.

        Returns:
            AwsSession: `AwsSession` object with default `boto_session` in job's region.
        """
        job_region = job_arn.split(":")[3]
        boto_session = boto3.Session(region_name=job_region)
        return AwsSession(boto_session=boto_session)

    @staticmethod
    def _generate_default_job_name(image_uri_type: str):
        return f"{image_uri_type}-{time.time() * 1000:.0f}"

    @property
    def arn(self) -> str:
        """str: The ARN (Amazon Resource Name) of the quantum job."""
        return self._arn

    @property
    def name(self) -> str:
        """str: The name of the quantum job."""
        return self._arn.partition("job/")[-1]

    def state(self, use_cached_value: bool = False) -> str:
        """The state of the quantum job.

        Args:
            use_cached_value (bool, optional): If `True`, uses the value most recently retrieved
                value from the Amazon Braket `GetJob` operation. If `False`, calls the
                `GetJob` operation to retrieve metadata, which also updates the cached
                value. Default = `False`.
        Returns:
            str: The value of `status` in `metadata()`. This is the value of the `status` key
            in the Amazon Braket `GetJob` operation.
        See Also:
            `metadata()`
        """
        return self.metadata(use_cached_value).get("status")

    def logs(self, wait: bool = False, poll: int = 5) -> None:
        """Display logs for a given job, optionally tailing them until job is complete.
        If the output is a tty or a Jupyter cell, it will be color-coded
        based on which instance the log entry is from.

        Args:
            wait (bool): Whether to keep looking for new log entries until the job completes
                (default: False).

            poll (int): The interval in seconds between polling for new log entries and job
                completion (default: 5).

        Raises:
            exceptions.UnexpectedStatusException: If waiting and the training job fails.
        """
        # The loop below implements a state machine that alternates between checking the job status
        # and reading whatever is available in the logs at this point. Note, that if we were
        # called with wait == False, we never check the job status.
        #
        # If wait == TRUE and job is not completed, the initial state is TAILING
        # If wait == FALSE, the initial state is COMPLETE (doesn't matter if the job really is
        # complete).
        #
        # The state table:
        #
        # STATE               ACTIONS                        CONDITION             NEW STATE
        # ----------------    ----------------               -----------------     ----------------
        # TAILING             Read logs, Pause, Get status   Job complete          JOB_COMPLETE
        #                                                    Else                  TAILING
        # JOB_COMPLETE        Read logs, Pause               Any                   COMPLETE
        # COMPLETE            Read logs, Exit                                      N/A
        #
        # Notes:
        # - The JOB_COMPLETE state forces us to do an extra pause and read any items that got to
        #   Cloudwatch after the job was marked complete.

        job_already_completed = self.state() in AwsQuantumJob.TERMINAL_STATES
        log_state = (
            AwsQuantumJob.LogState.TAILING
            if wait and not job_already_completed
            else AwsQuantumJob.LogState.COMPLETE
        )

        log_group = AwsQuantumJob.LOG_GROUP
        stream_prefix = f"{self.name}/"
        stream_names = []  # The list of log streams
        positions = {}  # The current position in each stream, map of stream name -> position
        instance_count = self.metadata(use_cached_value=True)["instanceConfig"]["instanceCount"]
        has_streams = False
        color_wrap = logs.ColorWrap()

        while True:
            time.sleep(poll)

            has_streams = logs.flush_log_streams(
                self._aws_session,
                log_group,
                stream_prefix,
                stream_names,
                positions,
                instance_count,
                has_streams,
                color_wrap,
            )

            if log_state == AwsQuantumJob.LogState.COMPLETE:
                break

            if log_state == AwsQuantumJob.LogState.JOB_COMPLETE:
                log_state = AwsQuantumJob.LogState.COMPLETE
            elif self.state() in AwsQuantumJob.TERMINAL_STATES:
                log_state = AwsQuantumJob.LogState.JOB_COMPLETE

    def metadata(self, use_cached_value: bool = False) -> Dict[str, Any]:
        """Get job metadata defined in Amazon Braket.

        Args:
            use_cached_value (bool, optional): If `True`, uses the value most recently retrieved
                value from the Amazon Braket `GetJob` operation, if it exists; if not,
                `GetJob` will be called to retrieve the metadata. If `False`, always calls
                `GetJob`, which also updates the cached value. Default: `False`.
        Returns:
            Dict[str, Any]: Dict specifying the job metadata defined in Amazon Braket.
        """
        if not use_cached_value or not self._metadata:
            self._metadata = self._aws_session.get_job(self._arn)
        return self._metadata

    def metrics(
        self,
        metric_type: MetricType = MetricType.TIMESTAMP,
        statistic: MetricStatistic = MetricStatistic.MAX,
    ) -> Dict[str, List[Any]]:
        """
        Gets all the metrics data, where the keys are the column names, and the values are a list
        containing the values in each row. For example, the table:
           timestamp energy
           0         0.1
           1         0.2
        would be represented as:
        { "timestamp" : [0, 1], "energy" : [0.1, 0.2] }
        values may be integers, floats, strings or None.
        Args:
            metric_type (MetricType): The type of metrics to get. Default is MetricType.TIMESTAMP.
            statistic (MetricStatistic): The statistic to determine which metric value to use
                when there is a conflict. Default is MetricStatistic.MAX.

        Returns:
            Dict[str, List[Union[str, float, int]]] : The metrics data.
        """
        fetcher = CwlInsightsMetricsFetcher(self._aws_session)
        metadata = self.metadata(True)
        job_name = metadata["jobName"]
        # TODO : Add job start and job end times
        return fetcher.get_metrics_for_job(job_name, metric_type, statistic)

    def cancel(self) -> str:
        """Cancels the job.

        Returns:
            str: Representing the status of the job.

        Raises:
            ClientError: If there are errors invoking the CancelJob API.
        """
        cancellation_response = self._aws_session.cancel_job(self._arn)
        return cancellation_response["cancellationStatus"]

    def result(
        self,
        poll_timeout_seconds: float = DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = DEFAULT_RESULTS_POLL_INTERVAL,
    ) -> Dict[str, Any]:
        """Retrieves the job result persisted using save_job_result() function.

        Args:
            poll_timeout_seconds (float): The polling timeout for `result()`. Default: 10 days.
            poll_interval_seconds (float): The polling interval for `result()`. Default: 1 second.

        Returns:
            Dict[str, Any]: Dict specifying the job results.

        Raises:
            RunTimeError: if job is in FAILED or CANCELLED state.
            TimeOutError: if job execution exceeds the polling timeout period.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            job_name = self.metadata(True)["jobName"]
            self.download_result(temp_dir, poll_timeout_seconds, poll_interval_seconds)
            with open(f"{temp_dir}/{job_name}/{AwsQuantumJob.RESULTS_FILENAME}", "r") as f:
                persisted_data = PersistedJobData.parse_raw(f.read())
                deserialized_data = deserialize_values(
                    persisted_data.dataDictionary, persisted_data.dataFormat
                )
                return deserialized_data

    def download_result(
        self,
        extract_to=None,
        poll_timeout_seconds: float = DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = DEFAULT_RESULTS_POLL_INTERVAL,
    ) -> None:
        """Downloads the results from the job output S3 bucket and extracts the tar.gz
        bundle to the location specified by 'extract_to'. If no location is specified,
        the results are extracted to the current directory.

        Args:
            extract_to (str): Directory where the results will be extracted to. The results
                are extracted to a folder titled with the job name within this directory.
                Default= `Current working directory`.
            poll_timeout_seconds: (float): The polling timeout for `download_result()`.
                Default: 10 days.
            poll_interval_seconds: (float): The polling interval for `download_result()`.
                Default: 1 second.

        Raises:
            RunTimeError: if job is in FAILED or CANCELLED state.
            TimeOutError: if job execution exceeds the polling timeout period.
        """

        extract_to = extract_to or os.getcwd()

        timeout_time = time.time() + poll_timeout_seconds
        job_response = self.metadata(True)

        while time.time() < timeout_time:
            job_response = self.metadata(True)
            job_state = self.state()

            if job_state in AwsQuantumJob.NO_RESULT_TERMINAL_STATES:
                message = (
                    f"Error retrieving results, your job is in {job_state} state. "
                    f"Your job has failed due to: {job_response['failureReason']}"
                    if job_state == "FAILED"
                    else f"Error retrieving results, your job is in {job_state} state."
                )
                raise RuntimeError(message)
            elif job_state in AwsQuantumJob.RESULTS_READY_STATES:
                output_s3_path, job_name = (
                    job_response["outputDataConfig"]["s3Path"],
                    job_response["jobName"],
                )

                output_bucket_uri = (
                    f"{output_s3_path}/BraketJob-"
                    f"{self._aws_session.account_id}-{job_name}/output/"
                    f"{AwsQuantumJob.RESULTS_TAR_FILENAME}"
                )
                self._aws_session.download_from_s3(
                    s3_uri=output_bucket_uri, filename=AwsQuantumJob.RESULTS_TAR_FILENAME
                )
                AwsQuantumJob._extract_tar_file(f"{extract_to}/{job_name}")
                return
            else:
                time.sleep(poll_interval_seconds)

        raise TimeoutError(
            f"{job_response['jobName']}: Polling for job completion "
            f"timed out after {poll_timeout_seconds} seconds."
        )

    @staticmethod
    def _extract_tar_file(extract_path):
        with tarfile.open(AwsQuantumJob.RESULTS_TAR_FILENAME, "r:gz") as tar:
            tar.extractall(extract_path)

    def __repr__(self) -> str:
        return f"AwsQuantumJob('arn':'{self.arn}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, AwsQuantumJob):
            return self.arn == other.arn
        return False

    def __hash__(self) -> int:
        return hash(self.arn)

    @staticmethod
    def _validate_entry_point(entry_point):
        module, _, function_name = entry_point.partition(":")
        try:
            module = importlib.import_module(module)
        except ModuleNotFoundError:
            raise ValueError(f"Entry point module not found: '{module}'")
        if function_name and not hasattr(module, function_name):
            raise ValueError(f"Entry function '{function_name}' not found in module '{module}'.")

    @staticmethod
    def _process_source_dir(entry_point, source_dir, aws_session, code_location):
        if source_dir:
            if source_dir.startswith("s3://"):
                AwsQuantumJob._process_s3_source_dir(aws_session, source_dir, code_location)
            else:
                AwsQuantumJob._process_local_source_dir(
                    aws_session, entry_point, source_dir, code_location
                )
        else:
            AwsQuantumJob._source_dir_not_provided(aws_session, entry_point, code_location)

    @staticmethod
    def _process_s3_source_dir(aws_session, source_dir, code_location):
        if not source_dir.endswith(".tar.gz"):
            raise ValueError(
                f"If source_dir is an S3 URI, it must point to a tar.gz file. "
                f"Not a valid S3 URI for parameter `source_dir`: {source_dir}"
            )
        aws_session.copy_s3_object(source_dir, f"{code_location}/source.tar.gz")

    @staticmethod
    def _process_local_source_dir(aws_session, entry_point, source_dir, code_location):
        module, _, func = entry_point.partition(":")
        entry_file = f"{module.replace('.', '/')}.py"

        if not os.path.abspath(entry_file).startswith(os.path.abspath(source_dir)):
            raise ValueError(
                f"`Entrypoint`: {entry_point} should be " f"within the `source_dir`: {source_dir}"
            )

        AwsQuantumJob._validate_entry_point(entry_point)
        AwsQuantumJob._tar_and_upload_to_code_location(aws_session, source_dir, code_location)

    @staticmethod
    def _source_dir_not_provided(aws_session, entry_point, code_location):
        AwsQuantumJob._validate_entry_point(entry_point)
        module, _, func = entry_point.partition(":")
        upload_dir = module.split(".")[0]

        AwsQuantumJob._tar_and_upload_to_code_location(aws_session, upload_dir, code_location)

    @staticmethod
    def _tar_and_upload_to_code_location(aws_session, source_dir, code_location):
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                with tarfile.open(f"{temp_dir}/source.tar.gz", "w:gz", dereference=True) as tar:
                    tar.add(source_dir, arcname=os.path.basename(source_dir))
            except FileNotFoundError:
                raise ValueError(f"Source directory not found: {source_dir}")
            aws_session.upload_to_s3(f"{temp_dir}/source.tar.gz", f"{code_location}/source.tar.gz")
