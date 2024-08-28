# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
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

import os
import time
from typing import Any

from braket.aws.aws_session import AwsSession
from braket.jobs.config import CheckpointConfig, OutputDataConfig, S3DataSourceConfig
from braket.jobs.image_uris import Framework, retrieve_image
from braket.jobs.local.local_job_container import _LocalJobContainer
from braket.jobs.local.local_job_container_setup import setup_container
from braket.jobs.metrics_data.definitions import MetricStatistic, MetricType
from braket.jobs.metrics_data.log_metrics_parser import LogMetricsParser
from braket.jobs.quantum_job import QuantumJob
from braket.jobs.quantum_job_creation import prepare_quantum_job
from braket.jobs.serialization import deserialize_values
from braket.jobs_data import PersistedJobData


class LocalQuantumJob(QuantumJob):
    """Amazon Braket implementation of a hybrid job that runs locally."""

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
        hyperparameters: dict[str, Any] | None = None,
        input_data: str | dict | S3DataSourceConfig | None = None,
        output_data_config: OutputDataConfig | None = None,
        checkpoint_config: CheckpointConfig | None = None,
        aws_session: AwsSession | None = None,
        local_container_update: bool = True,
    ) -> LocalQuantumJob:
        """Creates and runs hybrid job by setting up and running the customer script in a local
        docker container.

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
                created.
                Default: f'{image_uri_type}-{timestamp}'.

            code_location (str | None): The S3 prefix URI where custom code will be uploaded.
                Default: f's3://{default_bucket_name}/jobs/{job_name}/script'.

            role_arn (str | None): This field is currently not used for local hybrid jobs. Local
                hybrid jobs will use the current role's credentials. This may be subject to change.

            hyperparameters (dict[str, Any] | None): Hyperparameters accessible to the hybrid job.
                The hyperparameters are made accessible as a Dict[str, str] to the hybrid job.
                For convenience, this accepts other types for keys and values, but `str()`
                is called to convert them before being passed on. Default: None.

            input_data (str | dict | S3DataSourceConfig | None): Information about the training
                data. Dictionary maps channel names to local paths or S3 URIs. Contents found
                at any local paths will be uploaded to S3 at
                f's3://{default_bucket_name}/jobs/{job_name}/data/{channel_name}. If a local
                path, S3 URI, or S3DataSourceConfig is provided, it will be given a default
                channel name "input".
                Default: {}.

            output_data_config (OutputDataConfig | None): Specifies the location for the output of
                the hybrid job.
                Default: OutputDataConfig(s3Path=f's3://{default_bucket_name}/jobs/{job_name}/data',
                kmsKeyId=None).

            checkpoint_config (CheckpointConfig | None): Configuration that specifies the location
                where checkpoint data is stored.
                Default: CheckpointConfig(localPath='/opt/jobs/checkpoints',
                s3Uri=f's3://{default_bucket_name}/jobs/{job_name}/checkpoints').

            aws_session (AwsSession | None): AwsSession for connecting to AWS Services.
                Default: AwsSession()

            local_container_update (bool): Perform an update, if available, from ECR to the local
                container image. Optional.
                Default: True.

        Raises:
            ValueError: Local directory with the job name already exists.

        Returns:
            LocalQuantumJob: The representation of a local Braket Hybrid Job.
        """
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
            output_data_config=output_data_config,
            checkpoint_config=checkpoint_config,
            aws_session=aws_session,
        )

        job_name = create_job_kwargs["jobName"]
        if os.path.isdir(job_name):
            raise ValueError(
                f"A local directory called {job_name} already exists. "
                f"Please use a different job name."
            )

        session = aws_session or AwsSession()
        algorithm_specification = create_job_kwargs["algorithmSpecification"]
        if "containerImage" in algorithm_specification:
            image_uri = algorithm_specification["containerImage"]["uri"]
        else:
            image_uri = retrieve_image(Framework.BASE, session.region)

        with _LocalJobContainer(
            image_uri=image_uri, force_update=local_container_update
        ) as container:
            env_variables = setup_container(container, session, **create_job_kwargs)
            container.run_local_job(env_variables)
            container.copy_from("/opt/ml/model", job_name)
            with open(os.path.join(job_name, "log.txt"), "w", encoding="utf-8") as log_file:
                log_file.write(container.run_log)
            if "checkpointConfig" in create_job_kwargs:
                checkpoint_config = create_job_kwargs["checkpointConfig"]
                if "localPath" in checkpoint_config:
                    checkpoint_path = checkpoint_config["localPath"]
                    container.copy_from(checkpoint_path, os.path.join(job_name, "checkpoints"))
            run_log = container.run_log
        return LocalQuantumJob(f"local:job/{job_name}", run_log)

    def __init__(self, arn: str, run_log: str | None = None):
        """Initializes a `LocalQuantumJob`.

        Args:
            arn (str): The ARN of the hybrid job.
            run_log (str | None): The container output log of running the hybrid job with the given
                arn.

        Raises:
            ValueError: Local job is not found.
        """
        if not arn.startswith("local:job/"):
            raise ValueError(f"Arn {arn} is not a valid local job arn")
        self._arn = arn
        self._run_log = run_log
        self._name = arn.partition("job/")[-1]
        if not run_log and not os.path.isdir(self.name):
            raise ValueError(f"Unable to find local job results for {self.name}")

    @property
    def arn(self) -> str:
        """str: The ARN (Amazon Resource Name) of the hybrid job."""
        return self._arn

    @property
    def name(self) -> str:
        """str: The name of the hybrid job."""
        return self._name

    @property
    def run_log(self) -> str:
        """Gets the run output log from running the hybrid job.

        Raises:
            ValueError: The log file is not found.

        Returns:
            str:  The container output log from running the hybrid job.
        """
        if not self._run_log:
            try:
                with open(os.path.join(self.name, "log.txt"), encoding="utf-8") as log_file:
                    self._run_log = log_file.read()
            except FileNotFoundError as e:
                raise ValueError(
                    f"Unable to find logs in the local job directory {self.name}."
                ) from e
        return self._run_log

    def state(self, use_cached_value: bool = False) -> str:
        """The state of the hybrid job.

        Args:
            use_cached_value (bool): If `True`, uses the value most recently retrieved
                value from the Amazon Braket `GetJob` operation. If `False`, calls the
                `GetJob` operation to retrieve metadata, which also updates the cached
                value. Default = `False`.

        Returns:
            str: Returns "COMPLETED".
        """
        return "COMPLETED"

    def metadata(self, use_cached_value: bool = False) -> dict[str, Any]:
        """When running the hybrid job in local mode, the metadata is not available.

        Args:
            use_cached_value (bool): If `True`, uses the value most recently retrieved
                from the Amazon Braket `GetJob` operation, if it exists; if does not exist,
                `GetJob` is called to retrieve the metadata. If `False`, always calls
                `GetJob`, which also updates the cached value. Default: `False`.

        Returns:
            dict[str, Any]: None
        """

    def cancel(self) -> str:
        """When running the hybrid job in local mode, the cancelling a running is not possible.

        Returns:
            str: None
        """

    def download_result(
        self,
        extract_to: str | None = None,
        poll_timeout_seconds: float = QuantumJob.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = QuantumJob.DEFAULT_RESULTS_POLL_INTERVAL,
    ) -> None:
        """When running the hybrid job in local mode, results are automatically stored locally.

        Args:
            extract_to (str | None): The directory to which the results are extracted. The results
                are extracted to a folder titled with the hybrid job name within this directory.
                Default= `Current working directory`.
            poll_timeout_seconds (float): The polling timeout, in seconds, for `result()`.
                Default: 10 days.
            poll_interval_seconds (float): The polling interval, in seconds, for `result()`.
                Default: 5 seconds.
        """

    def result(
        self,
        poll_timeout_seconds: float = QuantumJob.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = QuantumJob.DEFAULT_RESULTS_POLL_INTERVAL,
    ) -> dict[str, Any]:
        """Retrieves the `LocalQuantumJob` result persisted using `save_job_result` function.

        Args:
            poll_timeout_seconds (float): The polling timeout, in seconds, for `result()`.
                Default: 10 days.
            poll_interval_seconds (float): The polling interval, in seconds, for `result()`.
                Default: 5 seconds.

        Raises:
            ValueError: The local job directory does not exist.

        Returns:
            dict[str, Any]: Dict specifying the hybrid job results.
        """
        try:
            with open(os.path.join(self.name, "results.json"), encoding="utf-8") as f:
                persisted_data = PersistedJobData.parse_raw(f.read())
                return deserialize_values(persisted_data.dataDictionary, persisted_data.dataFormat)
        except FileNotFoundError as e:
            raise ValueError(
                f"Unable to find results in the local job directory {self.name}."
            ) from e

    def metrics(
        self,
        metric_type: MetricType = MetricType.TIMESTAMP,
        statistic: MetricStatistic = MetricStatistic.MAX,
    ) -> dict[str, list[Any]]:
        """Gets all the metrics data, where the keys are the column names, and the values are a list
        containing the values in each row.

        Args:
            metric_type (MetricType): The type of metrics to get. Default: MetricType.TIMESTAMP.
            statistic (MetricStatistic): The statistic to determine which metric value to use
                when there is a conflict. Default: MetricStatistic.MAX.

        Example:
            timestamp energy
              0         0.1
              1         0.2
            would be represented as:
            { "timestamp" : [0, 1], "energy" : [0.1, 0.2] }
            values may be integers, floats, strings or None.

        Returns:
            dict[str, list[Any]]: The metrics data.
        """
        parser = LogMetricsParser()
        current_time = str(time.time())
        for line in self.run_log.splitlines():
            if line.startswith("Metrics -"):
                parser.parse_log_message(current_time, line)
        return parser.get_parsed_metrics(metric_type, statistic)

    def logs(self, wait: bool = False, poll_interval_seconds: int = 5) -> None:
        """Display container logs for a given hybrid job

        Args:
            wait (bool): `True` to keep looking for new log entries until the hybrid job completes;
                otherwise `False`. Default: `False`.
            poll_interval_seconds (int): The interval of time, in seconds, between polling for
                new log entries and hybrid job completion (default: 5).

        """
        return print(self.run_log)
