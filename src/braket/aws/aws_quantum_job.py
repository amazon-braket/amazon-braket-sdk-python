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

import math
import tarfile
import tempfile
import time
from enum import Enum
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, ClassVar

import boto3
from botocore.exceptions import ClientError

from braket.aws import AwsDevice
from braket.aws.aws_session import AwsSession
from braket.aws.queue_information import HybridJobQueueInfo
from braket.jobs import logs
from braket.jobs.config import (
    CheckpointConfig,
    InstanceConfig,
    OutputDataConfig,
    S3DataSourceConfig,
    StoppingCondition,
)
from braket.jobs.data_persistence import load_job_result
from braket.jobs.metrics_data.cwl_insights_metrics_fetcher import CwlInsightsMetricsFetcher

# TODO: Have added metric file in metrics folder, but have to decide on the name for keep
# for the files, since all those metrics are retrieved from the CW.
from braket.jobs.metrics_data.definitions import MetricStatistic, MetricType
from braket.jobs.quantum_job import QuantumJob
from braket.jobs.quantum_job_creation import prepare_quantum_job


class AwsQuantumJob(QuantumJob):
    """Amazon Braket implementation of a quantum job."""

    TERMINAL_STATES: ClassVar[set[str]] = {"CANCELLED", "COMPLETED", "FAILED"}
    RESULTS_FILENAME = "results.json"
    RESULTS_TAR_FILENAME = "model.tar.gz"
    LOG_GROUP = "/aws/braket/jobs"

    class LogState(Enum):
        """Log state enum."""

        TAILING = "tailing"
        JOB_COMPLETE = "job_complete"
        COMPLETE = "complete"

    @classmethod
    def create(
        cls,
        device: str,
        source_module: str,
        entry_point: str | None = None,
        image_uri: str | None = None,
        job_name: str | None = None,
        code_location: str | None = None,
        role_arn: str | None = None,
        wait_until_complete: bool = False,
        hyperparameters: dict[str, Any] | None = None,
        input_data: str | dict | S3DataSourceConfig | None = None,
        instance_config: InstanceConfig | None = None,
        distribution: str | None = None,
        stopping_condition: StoppingCondition | None = None,
        output_data_config: OutputDataConfig | None = None,
        copy_checkpoints_from_job: str | None = None,
        checkpoint_config: CheckpointConfig | None = None,
        aws_session: AwsSession | None = None,
        tags: dict[str, str] | None = None,
        logger: Logger = getLogger(__name__),
        quiet: bool = False,
        reservation_arn: str | None = None,
    ) -> AwsQuantumJob:
        """Creates a hybrid job by invoking the Braket CreateJob API.

        Args:
            device (str): Device ARN of the QPU device that receives priority quantum
                task queueing once the hybrid job begins running. Each QPU has a separate hybrid
                jobs queue so that only one hybrid job is running at a time. The device string is
                accessible in the hybrid job instance as the environment variable
                "AMZN_BRAKET_DEVICE_ARN". When using embedded simulators, you may provide the device
                argument as a string of the form: "local:<provider>/<simulator_name>".

            source_module (str): Path (absolute, relative or an S3 URI) to a python module to be
                tarred and uploaded. If `source_module` is an S3 URI, it must point to a
                tar.gz file. Otherwise, source_module may be a file or directory.

            entry_point (str | None): A str that specifies the entry point of the hybrid job,
                relative to the source module. The entry point must be in the format
                `importable.module` or `importable.module:callable`. For example,
                `source_module.submodule:start_here` indicates the `start_here` function
                contained in `source_module.submodule`. If source_module is an S3 URI,
                entry point must be given. Default: source_module's name

            image_uri (str | None): A str that specifies the ECR image to use for executing the
                hybrid job. `image_uris.retrieve_image()` function may be used for retrieving the
                ECR image URIs for the containers supported by Braket.
                Default = `<Braket base image_uri>`.

            job_name (str | None): A str that specifies the name with which the hybrid job is
                created. Allowed pattern for hybrid job name: `^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,50}$`
                Default: f'{image_uri_type}-{timestamp}'.

            code_location (str | None): The S3 prefix URI where custom code will be uploaded.
                Default: f's3://{default_bucket_name}/jobs/{job_name}/script'.

            role_arn (str | None): A str providing the IAM role ARN used to execute the
                script. Default: IAM role returned by AwsSession's `get_default_jobs_role()`.

            wait_until_complete (bool): `True` if we should wait until the hybrid job completes.
                This would tail the hybrid job logs as it waits. Otherwise `False`.
                Default: `False`.

            hyperparameters (dict[str, Any] | None): Hyperparameters accessible to the hybrid job.
                The hyperparameters are made accessible as a dict[str, str] to the hybrid job.
                For convenience, this accepts other types for keys and values, but `str()`
                is called to convert them before being passed on. Default: None.

            input_data (str | dict | S3DataSourceConfig | None): Information about the training
                data. Dictionary maps channel names to local paths or S3 URIs. Contents found
                at any local paths will be uploaded to S3 at
                f's3://{default_bucket_name}/jobs/{job_name}/data/{channel_name}. If a local
                path, S3 URI, or S3DataSourceConfig is provided, it will be given a default
                channel name "input".
                Default: {}.

            instance_config (InstanceConfig | None): Configuration of the instance(s) for running
                the classical code for the hybrid job. Default:
                `InstanceConfig(instanceType='ml.m5.large', instanceCount=1, volumeSizeInGB=30)`.

            distribution (str | None): A str that specifies how the hybrid job should be
                distributed. If set to "data_parallel", the hyperparameters for the hybrid job will
                be set to use data parallelism features for PyTorch or TensorFlow. Default: None.

            stopping_condition (StoppingCondition | None): The maximum length of time, in seconds,
                and the maximum number of quantum tasks that a hybrid job can run before being
                forcefully stopped.
                Default: StoppingCondition(maxRuntimeInSeconds=5 * 24 * 60 * 60).

            output_data_config (OutputDataConfig | None): Specifies the location for the output of
                the hybrid job.
                Default: OutputDataConfig(s3Path=f's3://{default_bucket_name}/jobs/{job_name}/data',
                kmsKeyId=None).

            copy_checkpoints_from_job (str | None): A str that specifies the hybrid job ARN whose
                checkpoint you want to use in the current hybrid job. Specifying this value will
                copy over the checkpoint data from `use_checkpoints_from_job`'s checkpoint_config
                s3Uri to the current hybrid job's checkpoint_config s3Uri, making it available at
                checkpoint_config.localPath during the hybrid job execution. Default: None

            checkpoint_config (CheckpointConfig | None): Configuration that specifies the location
                where checkpoint data is stored.
                Default: CheckpointConfig(localPath='/opt/jobs/checkpoints',
                s3Uri=f's3://{default_bucket_name}/jobs/{job_name}/checkpoints').

            aws_session (AwsSession | None): AwsSession for connecting to AWS Services.
                Default: AwsSession()

            tags (dict[str, str] | None): Dict specifying the key-value pairs for tagging this
                hybrid job.
                Default: {}.

            logger (Logger): Logger object with which to write logs, such as quantum task statuses
                while waiting for quantum task to be in a terminal state. Default is
                `getLogger(__name__)`

            quiet (bool): Sets the verbosity of the logger to low and does not report queue
                position. Default is `False`.

            reservation_arn (str | None): the reservation window arn provided by Braket
                Direct to reserve exclusive usage for the device to run the hybrid job on.
                Default: None.

        Returns:
            AwsQuantumJob: Hybrid job tracking the execution on Amazon Braket.

        Raises:
            ValueError: Raises ValueError if the parameters are not valid.
        """
        aws_session = AwsQuantumJob._initialize_session(aws_session, device, logger)

        create_job_kwargs = prepare_quantum_job(
            device=device,
            source_module=source_module,
            entry_point=entry_point,
            image_uri=image_uri,
            job_name=job_name,
            code_location=code_location,
            role_arn=role_arn,
            hyperparameters=hyperparameters,
            input_data=input_data,
            instance_config=instance_config,
            distribution=distribution,
            stopping_condition=stopping_condition,
            output_data_config=output_data_config,
            copy_checkpoints_from_job=copy_checkpoints_from_job,
            checkpoint_config=checkpoint_config,
            aws_session=aws_session,
            tags=tags,
            reservation_arn=reservation_arn,
        )

        job_arn = aws_session.create_job(**create_job_kwargs)
        job = AwsQuantumJob(job_arn, aws_session, quiet)

        if wait_until_complete:
            print(f"Initializing Braket Job: {job_arn}")
            job.logs(wait=True)

        return job

    def __init__(self, arn: str, aws_session: AwsSession | None = None, quiet: bool = False):
        """Initializes an `AwsQuantumJob`.

        Args:
            arn (str): The ARN of the hybrid job.
            aws_session (AwsSession | None): The `AwsSession` for connecting to AWS services.
                Default is `None`, in which case an `AwsSession` object will be created with the
                region of the hybrid job.
            quiet (bool): Sets the verbosity of the logger to low and does not report queue
                position. Default is `False`.

        Raises:
            ValueError: Supplied region and session region do not match.
        """
        self._arn: str = arn
        self._quiet = quiet
        if aws_session:
            if not self._is_valid_aws_session_region_for_job_arn(aws_session, arn):
                raise ValueError(
                    "The aws session region does not match the region for the supplied arn."
                )
            self._aws_session = aws_session
        else:
            self._aws_session = AwsQuantumJob._default_session_for_job_arn(arn)
        self._metadata = {}

    @staticmethod
    def _is_valid_aws_session_region_for_job_arn(aws_session: AwsSession, job_arn: str) -> bool:
        """Checks whether the job region and session region match.

        Returns:
            bool: `True` when the aws_session region matches the job_arn region; otherwise
            `False`.
        """
        job_region = job_arn.split(":")[3]
        return job_region == aws_session.region

    @staticmethod
    def _default_session_for_job_arn(job_arn: str) -> AwsSession:
        """Get an AwsSession for the Hybrid Job ARN. The AWS session should be in the region of the
           hybrid job.

        Args:
            job_arn (str): The ARN for the quantum hybrid job.

        Returns:
            AwsSession: `AwsSession` object with default `boto_session` in hybrid job's region.
        """
        job_region = job_arn.split(":")[3]
        boto_session = boto3.Session(region_name=job_region)
        return AwsSession(boto_session=boto_session)

    @property
    def arn(self) -> str:
        """str: The ARN (Amazon Resource Name) of the quantum hybrid job."""
        return self._arn

    @property
    def name(self) -> str:
        """str: The name of the quantum job."""
        return self.metadata(use_cached_value=True).get("jobName")

    @property
    def _logs_prefix(self) -> str:
        """str: the prefix for the job logs."""
        # jobs ARNs used to contain the job name and use a log prefix of `job-name`
        # now job ARNs use a UUID and a log prefix of `job-name/UUID`
        return (
            f"{self.name}"
            if self.arn.endswith(self.name)
            else f"{self.name}/{self.arn.split('/')[-1]}"
        )

    def state(self, use_cached_value: bool = False) -> str:
        """The state of the quantum hybrid job.

        Args:
            use_cached_value (bool): If `True`, uses the value most recently retrieved
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

    def queue_position(self) -> HybridJobQueueInfo:
        """The queue position details for the hybrid job.

        Returns:
            HybridJobQueueInfo: Instance of HybridJobQueueInfo class representing
            the queue position information for the hybrid job. The queue_position is
            only returned when the hybrid job is not in RUNNING/CANCELLING/TERMINAL states,
            else queue_position is returned as None. If the queue position of the hybrid
            job is greater than 15, we return '>15' as the queue_position return value.

        Examples:
            job status = QUEUED and position is 2 in the queue.
            >>> job.queue_position()
            HybridJobQueueInfo(queue_position='2', message=None)

            job status = QUEUED and position is 18 in the queue.
            >>> job.queue_position()
            HybridJobQueueInfo(queue_position='>15', message=None)

            job status = COMPLETED
            >>> job.queue_position()
            HybridJobQueueInfo(queue_position=None,
            message='Job is in COMPLETED status. AmazonBraket does
                        not show queue position for this status.')
        """
        response = self.metadata()["queueInfo"]
        queue_position = None if response.get("position") == "None" else response.get("position")
        message = response.get("message")

        return HybridJobQueueInfo(queue_position=queue_position, message=message)

    def logs(self, wait: bool = False, poll_interval_seconds: int = 5) -> None:
        """Display logs for a given hybrid job, optionally tailing them until hybrid job is
           complete.

        If the output is a tty or a Jupyter cell, it will be color-coded
        based on which instance the log entry is from.

        Args:
            wait (bool): `True` to keep looking for new log entries until the hybrid job completes;
                otherwise `False`. Default: `False`.

            poll_interval_seconds (int): The interval of time, in seconds, between polling for
                new log entries and hybrid job completion (default: 5).

        Raises:
            exceptions.UnexpectedStatusException: If waiting and the training hybrid job fails.
        """
        # The loop below implements a state machine that alternates between checking the hybrid job
        # status and reading whatever is available in the logs at this point. Note, that if we were
        # called with wait == False, we never check the hybrid job status.
        #
        # If wait == TRUE and hybrid job is not completed, the initial state is TAILING
        # If wait == FALSE, the initial state is COMPLETE (doesn't matter if the hybrid job really
        # is complete).
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
        stream_names = []  # The list of log streams
        positions = {}  # The current position in each stream, map of stream name -> position
        instance_count = self.metadata(use_cached_value=True)["instanceConfig"]["instanceCount"]
        has_streams = False
        color_wrap = logs.ColorWrap()
        previous_state = self.state()

        while True:
            time.sleep(poll_interval_seconds)
            current_state = self.state()
            has_streams = logs.flush_log_streams(
                self._aws_session,
                log_group,
                self._logs_prefix,
                stream_names,
                positions,
                instance_count,
                has_streams,
                color_wrap,
                [previous_state, current_state],
                None if self._quiet else self.queue_position().queue_position,
            )
            previous_state = current_state

            if log_state == AwsQuantumJob.LogState.COMPLETE:
                break

            if log_state == AwsQuantumJob.LogState.JOB_COMPLETE:
                log_state = AwsQuantumJob.LogState.COMPLETE
            elif current_state in AwsQuantumJob.TERMINAL_STATES:
                log_state = AwsQuantumJob.LogState.JOB_COMPLETE

    def metadata(self, use_cached_value: bool = False) -> dict[str, Any]:
        """Gets the hybrid job metadata defined in Amazon Braket.

        Args:
            use_cached_value (bool): If `True`, uses the value most recently retrieved
                from the Amazon Braket `GetJob` operation, if it exists; if does not exist,
                `GetJob` is called to retrieve the metadata. If `False`, always calls
                `GetJob`, which also updates the cached value. Default: `False`.

        Returns:
            dict[str, Any]: Dict that specifies the hybrid job metadata defined in Amazon Braket.
        """
        if not use_cached_value or not self._metadata:
            self._metadata = self._aws_session.get_job(self._arn)
        return self._metadata

    def metrics(
        self,
        metric_type: MetricType = MetricType.TIMESTAMP,
        statistic: MetricStatistic = MetricStatistic.MAX,
    ) -> dict[str, list[Any]]:
        """Gets all the metrics data, where the keys are the column names, and the values are a list
        containing the values in each row. For example, the table:
            timestamp energy
              0         0.1
              1         0.2
        would be represented as:
        { "timestamp" : [0, 1], "energy" : [0.1, 0.2] }
        values may be integers, floats, strings or None.

        Args:
            metric_type (MetricType): The type of metrics to get. Default: MetricType.TIMESTAMP.

            statistic (MetricStatistic): The statistic to determine which metric value to use
                when there is a conflict. Default: MetricStatistic.MAX.

        Returns:
            dict[str, list[Any]]: The metrics data.
        """
        fetcher = CwlInsightsMetricsFetcher(self._aws_session)
        metadata = self.metadata(True)
        job_start = None
        job_end = None
        if "startedAt" in metadata:
            job_start = int(metadata["startedAt"].timestamp())
        if self.state() in AwsQuantumJob.TERMINAL_STATES and "endedAt" in metadata:
            job_end = math.ceil(metadata["endedAt"].timestamp())
        return fetcher.get_metrics_for_job(
            self.name, metric_type, statistic, job_start, job_end, self._logs_prefix
        )

    def cancel(self) -> str:
        """Cancels the job.

        Returns:
            str: Indicates the status of the job.

        Raises:
            ClientError: If there are errors invoking the CancelJob API.
        """
        cancellation_response = self._aws_session.cancel_job(self._arn)
        return cancellation_response["cancellationStatus"]

    def result(
        self,
        poll_timeout_seconds: float = QuantumJob.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = QuantumJob.DEFAULT_RESULTS_POLL_INTERVAL,
    ) -> dict[str, Any]:
        """Retrieves the hybrid job result persisted using the `save_job_result` function.

        Args:
            poll_timeout_seconds (float): The polling timeout, in seconds, for `result()`.
                Default: 10 days.
            poll_interval_seconds (float): The polling interval, in seconds, for `result()`.
                Default: 5 seconds.

        Returns:
            dict[str, Any]: Dict specifying the job results.

        Raises:
            RuntimeError: if hybrid job is in a FAILED or CANCELLED state.
            TimeoutError: if hybrid job execution exceeds the polling timeout period.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            job_name = self.metadata(True)["jobName"]

            try:
                self.download_result(temp_dir, poll_timeout_seconds, poll_interval_seconds)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    return {}
                raise
            return AwsQuantumJob._read_and_deserialize_results(temp_dir, job_name)

    @staticmethod
    def _read_and_deserialize_results(temp_dir: str, job_name: str) -> dict[str, Any]:
        return load_job_result(Path(temp_dir, job_name, AwsQuantumJob.RESULTS_FILENAME))

    def download_result(
        self,
        extract_to: str | None = None,
        poll_timeout_seconds: float = QuantumJob.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = QuantumJob.DEFAULT_RESULTS_POLL_INTERVAL,
    ) -> None:
        """Downloads the results from the hybrid job output S3 bucket and extracts the tar.gz
        bundle to the location specified by `extract_to`. If no location is specified,
        the results are extracted to the current directory.

        Args:
            extract_to (str | None): The directory to which the results are extracted. The results
                are extracted to a folder titled with the hybrid job name within this directory.
                Default= `Current working directory`.
            poll_timeout_seconds (float): The polling timeout, in seconds, for `download_result()`.
                Default: 10 days.
            poll_interval_seconds (float): The polling interval, in seconds, for
                `download_result()`.Default: 5 seconds.

        Raises:
            RuntimeError: if hybrid job is in a FAILED or CANCELLED state.
            TimeoutError: if hybrid job execution exceeds the polling timeout period.
        """
        extract_to = extract_to or Path.cwd()

        timeout_time = time.time() + poll_timeout_seconds
        job_response = self.metadata(True)

        while time.time() < timeout_time:
            job_response = self.metadata(True)
            job_state = self.state()

            if job_state in AwsQuantumJob.TERMINAL_STATES:
                output_s3_path = job_response["outputDataConfig"]["s3Path"]
                output_s3_uri = f"{output_s3_path}/output/model.tar.gz"
                AwsQuantumJob._attempt_results_download(self, output_s3_uri, output_s3_path)
                AwsQuantumJob._extract_tar_file(f"{extract_to}/{self.name}")
                return
            time.sleep(poll_interval_seconds)

        raise TimeoutError(
            f"{job_response['jobName']}: Polling for job completion "
            f"timed out after {poll_timeout_seconds} seconds."
        )

    def _attempt_results_download(self, output_bucket_uri: str, output_s3_path: str) -> None:
        try:
            self._aws_session.download_from_s3(
                s3_uri=output_bucket_uri, filename=AwsQuantumJob.RESULTS_TAR_FILENAME
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "404":
                raise
            exception_response = {
                "Error": {
                    "Code": "404",
                    "Message": f"Error retrieving results, "
                    f"could not find results at '{output_s3_path}'",
                }
            }
            raise ClientError(exception_response, "HeadObject") from e

    @staticmethod
    def _extract_tar_file(extract_path: str) -> None:
        with tarfile.open(AwsQuantumJob.RESULTS_TAR_FILENAME, "r:gz") as tar:
            tar.extractall(extract_path)  # noqa: S202

    def __repr__(self) -> str:
        return f"AwsQuantumJob('arn':'{self.arn}')"

    def __eq__(self, other: AwsQuantumJob) -> bool:
        return self.arn == other.arn if isinstance(other, AwsQuantumJob) else False

    def __hash__(self) -> int:
        return hash(self.arn)

    @staticmethod
    def _initialize_session(session_value: AwsSession, device: str, logger: Logger) -> AwsSession:
        aws_session = session_value or AwsSession()
        if device.startswith("local:"):
            return aws_session
        device_region = AwsDevice.get_device_region(device)
        return (
            AwsQuantumJob._initialize_regional_device_session(aws_session, device, logger)
            if device_region
            else AwsQuantumJob._initialize_non_regional_device_session(aws_session, device, logger)
        )

    @staticmethod
    def _initialize_regional_device_session(
        aws_session: AwsSession, device: AwsDevice, logger: Logger
    ) -> AwsSession:
        device_region = AwsDevice.get_device_region(device)
        current_region = aws_session.region
        if current_region != device_region:
            aws_session = aws_session.copy_session(region=device_region)
            logger.info(f"Changed session region from '{current_region}' to '{device_region}'")
        try:
            aws_session.get_device(device)
        except ClientError as e:
            raise (
                ValueError(f"'{device}' not found.")
                if e.response["Error"]["Code"] == "ResourceNotFoundException"
                else e
            ) from e
        else:
            return aws_session

    @staticmethod
    def _initialize_non_regional_device_session(
        aws_session: AwsSession, device: AwsDevice, logger: Logger
    ) -> AwsSession:
        original_region = aws_session.region
        try:
            aws_session.get_device(device)
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceNotFoundException":
                raise

            if "qpu" not in device:
                raise ValueError(f"Simulator '{device}' not found in '{original_region}'") from e
        else:
            return aws_session
        for region in frozenset(AwsDevice.REGIONS) - {original_region}:
            device_session = aws_session.copy_session(region=region)
            try:
                device_session.get_device(device)
                logger.info(
                    f"Changed session region from '{original_region}' to '{device_session.region}'"
                )
            except ClientError as e:
                if e.response["Error"]["Code"] != "ResourceNotFoundException":
                    raise
            else:
                return device_session
        raise ValueError(f"QPU '{device}' not found.")
