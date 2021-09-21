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

import importlib.util
import re
import sys
import tarfile
import tempfile
import time
from dataclasses import asdict
from enum import Enum
from pathlib import Path
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
    DEFAULT_RESULTS_POLL_INTERVAL = 5
    RESULTS_FILENAME = "results.json"
    RESULTS_TAR_FILENAME = "model.tar.gz"
    LOG_GROUP = "/aws/braket/jobs"

    class LogState(Enum):
        TAILING = "tailing"
        JOB_COMPLETE = "job_complete"
        COMPLETE = "complete"

    @classmethod
    def create(
        cls,
        device_arn: str,
        source_module: str,
        entry_point: str = None,
        image_uri: str = None,
        job_name: str = None,
        code_location: str = None,
        role_arn: str = None,
        wait_until_complete: bool = False,
        hyperparameters: Dict[str, Any] = None,
        metric_definitions: List[MetricDefinition] = None,
        input_data_config: List[InputDataConfig] = None,
        instance_config: InstanceConfig = None,
        stopping_condition: StoppingCondition = None,
        output_data_config: OutputDataConfig = None,
        copy_checkpoints_from_job: str = None,
        checkpoint_config: CheckpointConfig = None,
        vpc_config: VpcConfig = None,
        aws_session: AwsSession = None,
        *args,
        **kwargs,
    ) -> AwsQuantumJob:
        """Creates a job by invoking the Braket CreateJob API.

        Args:
            device_arn (str): ARN for the AWS device which is primarily
                accessed for the execution of this job.

            source_module (str): Path (absolute, relative or an S3 URI) to a python module to be
                tarred and uploaded. If `source_module` is an S3 URI, it must point to a
                tar.gz file. Otherwise, source_module may be a file or directory.

            entry_point (str): A str that specifies the entry point of the job, relative to
                the source module. The entry point must be in the format
                `importable.module` or `importable.module:callable`. For example,
                `source_module.submodule:start_here` indicates the `start_here` function
                contained in `source_module.submodule`. If source_module is an S3 URI,
                entry point must be given. Default: source_module's nam

            image_uri (str): A str that specifies the ECR image to use for executing the job.
                `image_uris.retrieve_image()` function may be used for retrieving the ECR image URIs
                for the containers supported by Braket. Default = `<Braket base image_uri>`.

            job_name (str): A str that specifies the name with which the job is created.
                Default: f'{image_uri_type}-{timestamp}'.

            code_location (str): The S3 prefix URI where custom code will be uploaded.
                Default: f's3://{default_bucket_name}/jobs/{job_name}/script'.

            role_arn (str): A str providing the IAM role ARN used to execute the
                script. Default: IAM role returned by get_execution_role().

            wait_until_complete (bool): `True` if we should wait until the job completes.
                This would tail the job logs as it waits. Otherwise `False`. Default: `False`.

            hyperparameters (Dict[str, Any]): Hyperparameters accessible to the job.
                The hyperparameters are made accessible as a Dict[str, str] to the job.
                For convenience, this accepts other types for keys and values, but `str()`
                is called to convert them before being passed on. Default: None.

            metric_definitions (List[MetricDefinition]): A list of MetricDefinitions that
                defines the metric(s) used to evaluate the training jobs. Default: None.

            input_data_config (List[InputDataConfig]): Information about the training data.
                Default: None.

            instance_config (InstanceConfig): Configuration of the instances to be used
                to execute the job. Default: InstanceConfig(instanceType='ml.m5.large',
                instanceCount=1, volumeSizeInGB=30, volumeKmsKey=None).

            stopping_condition (StoppingCondition): The maximum length of time, in seconds,
                and the maximum number of tasks that a job can run before being forcefully stopped.
                Default: StoppingCondition(maxRuntimeInSeconds=5 * 24 * 60 * 60).

            output_data_config (OutputDataConfig): Specifies the location for the output of the job.
                Default: OutputDataConfig(s3Path=f's3://{default_bucket_name}/jobs/{job_name}/
                output', kmsKeyId=None).

            copy_checkpoints_from_job (str): A str that specifies the job ARN whose checkpoint you
                want to use in the current job. Specifying this value will copy over the checkpoint
                data from `use_checkpoints_from_job`'s checkpoint_config s3Uri to the current job's
                checkpoint_config s3Uri, making it available at checkpoint_config.localPath during
                the job execution. Default: None

            checkpoint_config (CheckpointConfig): Configuration that specifies the location where
                checkpoint data is stored.
                Default: CheckpointConfig(localPath='/opt/jobs/checkpoints',
                s3Uri=None).

            vpc_config (VpcConfig): Configuration that specifies the security groups and subnets
                to use for running the job. Default: None.

            aws_session (AwsSession): AwsSession for connecting to AWS Services.
                Default: AwsSession()

        Returns:
            AwsQuantumJob: Job tracking the execution on Amazon Braket.

        Raises:
            ValueError: Raises ValueError if the parameters are not valid.
        """
        input_datatype_map = {
            "input_data_config": (input_data_config, List[InputDataConfig]),
            "instance_config": (instance_config, InstanceConfig),
            "stopping_condition": (stopping_condition, StoppingCondition),
            "output_data_config": (output_data_config, OutputDataConfig),
            "checkpoint_config": (checkpoint_config, CheckpointConfig),
            "vpc_config": (vpc_config, VpcConfig),
        }

        AwsQuantumJob._validate_input(input_datatype_map)
        aws_session = aws_session or AwsSession()
        device_config = DeviceConfig(devices=[device_arn])
        job_name = job_name or AwsQuantumJob._generate_default_job_name(image_uri)
        role_arn = role_arn or aws_session.get_execution_role()
        hyperparameters = hyperparameters or {}
        input_data_config = input_data_config or []
        instance_config = instance_config or InstanceConfig()
        stopping_condition = stopping_condition or StoppingCondition()
        output_data_config = output_data_config or OutputDataConfig()
        checkpoint_config = checkpoint_config or CheckpointConfig()
        default_bucket = aws_session.default_bucket()
        code_location = code_location or aws_session.construct_s3_uri(
            default_bucket,
            "jobs",
            job_name,
            "script",
        )
        if AwsSession.is_s3_uri(source_module):
            AwsQuantumJob._process_s3_source_module(
                source_module, entry_point, aws_session, code_location
            )
        else:
            # if entry point is None, it will be set to default here
            entry_point = AwsQuantumJob._process_local_source_module(
                source_module, entry_point, aws_session, code_location
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

        create_job_kwargs = {
            "jobName": job_name,
            "roleArn": role_arn,
            "algorithmSpecification": algorithm_specification,
            "inputDataConfig": [asdict(input_channel) for input_channel in input_data_config],
            "instanceConfig": asdict(instance_config),
            "outputDataConfig": asdict(output_data_config),
            "checkpointConfig": asdict(checkpoint_config),
            "deviceConfig": asdict(device_config),
            "hyperParameters": hyperparameters,
            "stoppingCondition": asdict(stopping_condition),
        }

        if vpc_config:
            create_job_kwargs["vpcConfig"] = asdict(vpc_config)

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
                    "The aws session region does not match the region for the supplied arn."
                )
            self._aws_session = aws_session
        else:
            self._aws_session = AwsQuantumJob._default_session_for_job_arn(arn)
        self._metadata = {}

    @staticmethod
    def _is_valid_aws_session_region_for_job_arn(aws_session: AwsSession, job_arn: str) -> bool:
        """
        bool: `True` when the aws_session region matches the job_arn region; otherwise `False`.
        """
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
    def _generate_default_job_name(image_uri: str):
        if not image_uri:
            job_type = "-default"
        else:
            job_type_match = re.search("/(.*)-jobs:", image_uri) or re.search(
                "/([^:/]*)", image_uri
            )
            job_type = f"-{job_type_match.groups()[0]}" if job_type_match else ""

        return f"braket-job{job_type}-{time.time() * 1000:.0f}"

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

    def logs(self, wait: bool = False, poll_interval_seconds: int = 5) -> None:
        """Display logs for a given job, optionally tailing them until job is complete.

        If the output is a tty or a Jupyter cell, it will be color-coded
        based on which instance the log entry is from.

        Args:
            wait (bool): `True` to keep looking for new log entries until the job completes;
                otherwise `False`. Default: `False`.

            poll_interval_seconds (int): The interval of time, in seconds, between polling for
                new log entries and job completion (default: 5).

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
            time.sleep(poll_interval_seconds)

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
        """Gets the job metadata defined in Amazon Braket.

        Args:
            use_cached_value (bool, optional): If `True`, uses the value most recently retrieved
                from the Amazon Braket `GetJob` operation, if it exists; if does not exist,
                `GetJob` is called to retrieve the metadata. If `False`, always calls
                `GetJob`, which also updates the cached value. Default: `False`.
        Returns:
            Dict[str, Any]: Dict that specifies the job metadata defined in Amazon Braket.
        """
        if not use_cached_value or not self._metadata:
            self._metadata = self._aws_session.get_job(self._arn)
        return self._metadata

    def metrics(
        self,
        metric_type: MetricType = MetricType.TIMESTAMP,
        statistic: MetricStatistic = MetricStatistic.MAX,
    ) -> Dict[str, List[Any]]:
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
            str: Indicates the status of the job.

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
            poll_timeout_seconds (float): The polling timeout, in seconds, for `result()`.
                Default: 10 days.

            poll_interval_seconds (float): The polling interval, in seconds, for `result()`.
                Default: 5 seconds.


        Returns:
            Dict[str, Any]: Dict specifying the job results.

        Raises:
            RuntimeError: if job is in a FAILED or CANCELLED state.
            TimeoutError: if job execution exceeds the polling timeout period.
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
        bundle to the location specified by `extract_to`. If no location is specified,
        the results are extracted to the current directory.

        Args:
            extract_to (str): The directory to which the results are extracted. The results
                are extracted to a folder titled with the job name within this directory.
                Default= `Current working directory`.

            poll_timeout_seconds: (float): The polling timeout, in seconds, for `download_result()`.
                Default: 10 days.

            poll_interval_seconds: (float): The polling interval, in seconds, for
                `download_result()`.Default: 5 seconds.

        Raises:
            RuntimeError: if job is in a FAILED or CANCELLED state.
            TimeoutError: if job execution exceeds the polling timeout period.
        """

        extract_to = extract_to or Path.cwd()

        timeout_time = time.time() + poll_timeout_seconds
        job_response = self.metadata(True)

        while time.time() < timeout_time:
            job_response = self.metadata(True)
            job_state = self.state()

            if job_state in AwsQuantumJob.NO_RESULT_TERMINAL_STATES:
                message = (
                    f"Error retrieving results, your job is in {job_state} state. "
                    "Your job has failed due to: "
                    f"{job_response.get('failureReason', 'unknown reason')}"
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
    def _process_s3_source_module(source_module, entry_point, aws_session, code_location):
        if entry_point is None:
            raise ValueError("If source_module is an S3 URI, entry_point must be provided.")
        if not source_module.lower().endswith(".tar.gz"):
            raise ValueError(
                "If source_module is an S3 URI, it must point to a tar.gz file. "
                f"Not a valid S3 URI for parameter `source_module`: {source_module}"
            )
        aws_session.copy_s3_object(source_module, f"{code_location}/source.tar.gz")

    @staticmethod
    def _process_local_source_module(source_module, entry_point, aws_session, code_location):
        try:
            # raises FileNotFoundError if not found
            abs_path_source_module = Path(source_module).resolve(strict=True)
        except FileNotFoundError:
            raise ValueError(f"Source module not found: {source_module}")

        entry_point = entry_point or abs_path_source_module.stem
        AwsQuantumJob._validate_entry_point(abs_path_source_module, entry_point)
        AwsQuantumJob._tar_and_upload_to_code_location(
            abs_path_source_module, aws_session, code_location
        )
        return entry_point

    @staticmethod
    def _validate_entry_point(source_module_path, entry_point):
        importable, _, _method = entry_point.partition(":")
        sys.path.append(str(source_module_path.parent))
        try:
            # second argument allows relative imports
            module = importlib.util.find_spec(importable, source_module_path.stem)
            assert module is not None
        # if entry point is nested (ie contains '.'), parent modules are imported
        except (ModuleNotFoundError, AssertionError):
            raise ValueError(f"Entry point module was not found: {importable}")
        finally:
            sys.path.pop()

    @staticmethod
    def _tar_and_upload_to_code_location(source_module_path, aws_session, code_location):
        with tempfile.TemporaryDirectory() as temp_dir:
            with tarfile.open(f"{temp_dir}/source.tar.gz", "w:gz", dereference=True) as tar:
                tar.add(source_module_path, arcname=source_module_path.name)
            aws_session.upload_to_s3(f"{temp_dir}/source.tar.gz", f"{code_location}/source.tar.gz")

    @staticmethod
    def _validate_input(dict_arr):
        for parameter_name, value_tuple in dict_arr.items():
            user_input, expected_datatype = value_tuple

            if user_input:
                AwsQuantumJob._validate_config_parameters(
                    user_input, parameter_name, expected_datatype
                )

    @staticmethod
    def _validate_config_parameters(user_input, parameter_name, expected_datatype):
        list_parameters = {"input_data_config": InputDataConfig}

        is_correct_data_type = (
            isinstance(user_input[0], list_parameters.get(parameter_name))
            if parameter_name in list_parameters
            else isinstance(user_input, expected_datatype)
        )

        if not is_correct_data_type:
            raise ValueError(
                f"'{parameter_name}' should be of '{expected_datatype}' "
                f"but user provided {type(user_input)}."
            )
