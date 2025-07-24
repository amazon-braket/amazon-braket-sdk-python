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
import os
import re
import sys
import tarfile
import tempfile
import time
import warnings
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from braket.aws.aws_session import AwsSession
from braket.jobs.config import (
    CheckpointConfig,
    DeviceConfig,
    InstanceConfig,
    OutputDataConfig,
    S3DataSourceConfig,
    StoppingCondition,
)
from braket.jobs.image_uris import Framework, retrieve_image


def prepare_quantum_job(
    device: str,
    source_module: str,
    entry_point: str | None = None,
    image_uri: str | None = None,
    job_name: str | None = None,
    code_location: str | None = None,
    role_arn: str | None = None,
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
    reservation_arn: str | None = None,
) -> dict:
    """Creates a hybrid job by invoking the Braket CreateJob API.

    Args:
        device (str): Device ARN of the QPU device that receives priority quantum
            task queueing once the hybrid job begins running. Each QPU has a separate hybrid jobs
            queue so that only one hybrid job is running at a time. The device string is accessible
            in the hybrid job instance as the environment variable "AMZN_BRAKET_DEVICE_ARN".
            When using embedded simulators, you may provide the device argument as string of the
            form: "local:<provider>/<simulator_name>".

        source_module (str): Path (absolute, relative or an S3 URI) to a python module to be
            tarred and uploaded. If `source_module` is an S3 URI, it must point to a
            tar.gz file. Otherwise, source_module may be a file or directory.

        entry_point (str | None): A str that specifies the entry point of the hybrid job, relative
            to the source module. The entry point must be in the format
            `importable.module` or `importable.module:callable`. For example,
            `source_module.submodule:start_here` indicates the `start_here` function
            contained in `source_module.submodule`. If source_module is an S3 URI,
            entry point must be given. Default: source_module's name

        image_uri (str | None): A str that specifies the ECR image to use for executing the hybrid
            job.`image_uris.retrieve_image()` function may be used for retrieving the ECR image URIs
            for the containers supported by Braket. Default = `<Braket base image_uri>`.

        job_name (str | None): A str that specifies the name with which the hybrid job is created.
            The hybrid job name must be between 0 and 50 characters long and cannot contain
            underscores.
            Default: f'{image_uri_type}-{timestamp}'.

        code_location (str | None): The S3 prefix URI where custom code will be uploaded.
            Default: f's3://{default_bucket_name}/jobs/{job_name}/script'.

        role_arn (str | None): A str providing the IAM role ARN used to execute the
            script. Default: IAM role returned by AwsSession's `get_default_jobs_role()`.

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

        instance_config (InstanceConfig | None): Configuration of the instance(s) for running the
            classical code for the hybrid job. Defaults to
            `InstanceConfig(instanceType='ml.m5.large', instanceCount=1, volumeSizeInGB=30)`.

        distribution (str | None): A str that specifies how the hybrid job should be distributed.
            If set to "data_parallel", the hyperparameters for the hybrid job will be set to use
            data parallelism features for PyTorch or TensorFlow. Default: None.

        stopping_condition (StoppingCondition | None): The maximum length of time, in seconds,
            and the maximum number of quantum tasks that a hybrid job can run before being
            forcefully stopped. Default: StoppingCondition(maxRuntimeInSeconds=5 * 24 * 60 * 60).

        output_data_config (OutputDataConfig | None): Specifies the location for the output of the
            hybrid job.
            Default: OutputDataConfig(s3Path=f's3://{default_bucket_name}/jobs/{job_name}/data',
            kmsKeyId=None).

        copy_checkpoints_from_job (str | None): A str that specifies the hybrid job ARN whose
            checkpoint you want to use in the current hybrid job. Specifying this value will copy
            over the checkpoint data from `use_checkpoints_from_job`'s checkpoint_config s3Uri to
            the current hybrid job's checkpoint_config s3Uri, making it available at
            checkpoint_config.localPath during the hybrid job execution. Default: None

        checkpoint_config (CheckpointConfig | None): Configuration that specifies the location where
            checkpoint data is stored.
            Default: CheckpointConfig(localPath='/opt/jobs/checkpoints',
            s3Uri=f's3://{default_bucket_name}/jobs/{job_name}/checkpoints').

        aws_session (AwsSession | None): AwsSession for connecting to AWS Services.
            Default: AwsSession()

        tags (dict[str, str] | None): Dict specifying the key-value pairs for tagging this
            hybrid job.
            Default: {}.

        reservation_arn (str | None): the reservation window arn provided by Braket
            Direct to reserve exclusive usage for the device to run the hybrid job on.
            Default: None.

    Returns:
        dict: Hybrid job tracking the execution on Amazon Braket.

    Raises:
        ValueError: Raises ValueError if the parameters are not valid.
    """
    param_datatype_map = {
        "instance_config": (instance_config, InstanceConfig),
        "stopping_condition": (stopping_condition, StoppingCondition),
        "output_data_config": (output_data_config, OutputDataConfig),
        "checkpoint_config": (checkpoint_config, CheckpointConfig),
    }

    _validate_params(param_datatype_map)
    aws_session = aws_session or AwsSession()
    device_config = DeviceConfig(device)
    timestamp = str(int(time.time() * 1000))
    job_name = job_name or _generate_default_job_name(image_uri=image_uri, timestamp=timestamp)
    role_arn = role_arn or os.getenv("BRAKET_JOBS_ROLE_ARN", aws_session.get_default_jobs_role())
    hyperparameters = hyperparameters or {}
    hyperparameters = {str(key): str(value) for key, value in hyperparameters.items()}
    input_data = input_data or {}
    tags = tags or {}
    default_bucket = aws_session.default_bucket()
    input_data_list = _process_input_data(input_data, job_name, aws_session, timestamp)
    instance_config = instance_config or InstanceConfig()
    stopping_condition = stopping_condition or StoppingCondition()
    output_data_config = output_data_config or OutputDataConfig()
    checkpoint_config = checkpoint_config or CheckpointConfig()
    code_location = code_location or AwsSession.construct_s3_uri(
        default_bucket,
        "jobs",
        job_name,
        timestamp,
        "script",
    )

    if AwsSession.is_s3_uri(source_module):
        _process_s3_source_module(source_module, entry_point, aws_session, code_location)
    else:
        # if entry point is None, it will be set to default here
        entry_point = _process_local_source_module(
            source_module, entry_point, aws_session, code_location
        )
    algorithm_specification = {
        "scriptModeConfig": {
            "entryPoint": entry_point,
            "s3Uri": f"{code_location}/source.tar.gz",
            "compressionType": "GZIP",
        }
    }
    image_uri = image_uri or retrieve_image(Framework.BASE, aws_session.region)
    algorithm_specification["containerImage"] = {"uri": image_uri}
    if not output_data_config.s3Path:
        output_data_config.s3Path = AwsSession.construct_s3_uri(
            default_bucket,
            "jobs",
            job_name,
            timestamp,
            "data",
        )
    if not checkpoint_config.s3Uri:
        checkpoint_config.s3Uri = AwsSession.construct_s3_uri(
            default_bucket,
            "jobs",
            job_name,
            timestamp,
            "checkpoints",
        )
    if copy_checkpoints_from_job:
        checkpoints_to_copy = aws_session.get_job(copy_checkpoints_from_job)["checkpointConfig"][
            "s3Uri"
        ]
        aws_session.copy_s3_directory(checkpoints_to_copy, checkpoint_config.s3Uri)
    if distribution == "data_parallel":
        distributed_hyperparams = {
            "sagemaker_distributed_dataparallel_enabled": "true",
            "sagemaker_instance_type": instance_config.instanceType,
        }
        hyperparameters |= distributed_hyperparams

    create_job_kwargs = {
        "jobName": job_name,
        "roleArn": role_arn,
        "algorithmSpecification": algorithm_specification,
        "inputDataConfig": input_data_list,
        "instanceConfig": asdict(instance_config),
        "outputDataConfig": asdict(output_data_config, dict_factory=_exclude_nones_factory),
        "checkpointConfig": asdict(checkpoint_config),
        "deviceConfig": asdict(device_config),
        "hyperParameters": hyperparameters,
        "stoppingCondition": asdict(stopping_condition),
        "tags": tags,
    }

    if reservation_arn:
        create_job_kwargs["associations"] = [
            {
                "arn": reservation_arn,
                "type": "RESERVATION_TIME_WINDOW_ARN",
            }
        ]

    return create_job_kwargs


def _generate_default_job_name(
    image_uri: str | None = None, func: Callable | None = None, timestamp: int | str | None = None
) -> str:
    """Generate default job name using the image uri and entrypoint function.

    Args:
        image_uri (str | None): URI for the image container.
        func (Callable | None): The entry point function.
        timestamp (int | str | None): Optional timestamp to use instead of generating one.

    Returns:
        str: Hybrid job name.
    """
    timestamp = timestamp if timestamp is not None else str(int(time.time() * 1000))

    if func:
        name = func.__name__.replace("_", "-")
        max_length = 50
        if len(name) + len(timestamp) > max_length:
            name = name[: max_length - len(timestamp) - 1]
            warnings.warn(
                f"Job name exceeded {max_length} characters. "
                f"Truncating name to {name}-{timestamp}.",
                stacklevel=1,
            )
    elif not image_uri:
        name = "braket-job-default"
    else:
        job_type_match = re.search(r"/amazon-braket-(.*)-jobs:", image_uri) or re.search(
            r"/amazon-braket-([^:/]*)", image_uri
        )
        container = f"-{job_type_match.groups()[0]}" if job_type_match else ""
        name = f"braket-job{container}"
    return f"{name}-{timestamp}"


def _process_s3_source_module(
    source_module: str, entry_point: str, aws_session: AwsSession, code_location: str
) -> None:
    """Check that the source module is an S3 URI of the correct type and that entry point is
    provided.

    Args:
        source_module (str): S3 URI pointing to the tarred source module.
        entry_point (str): Entry point for the hybrid job.
        aws_session (AwsSession): AwsSession to copy source module to code location.
        code_location (str): S3 URI pointing to the location where the code will be
            copied to.

    Raises:
        ValueError: The entry point is None or does not end with .tar.gz.
    """
    if entry_point is None:
        raise ValueError("If source_module is an S3 URI, entry_point must be provided.")
    if not source_module.lower().endswith(".tar.gz"):
        raise ValueError(
            "If source_module is an S3 URI, it must point to a tar.gz file. "
            f"Not a valid S3 URI for parameter `source_module`: {source_module}"
        )
    aws_session.copy_s3_object(source_module, f"{code_location}/source.tar.gz")


def _process_local_source_module(
    source_module: str, entry_point: str, aws_session: AwsSession, code_location: str
) -> str:
    """Check that entry point is valid with respect to source module, or provide a default
    value if entry point is not given. Tar and upload source module to code location in S3.

    Args:
        source_module (str): Local path pointing to the source module.
        entry_point (str): Entry point relative to the source module.
        aws_session (AwsSession): AwsSession for uploading tarred source module.
        code_location (str): S3 URI pointing to the location where the code will
            be uploaded to.

    Raises:
        ValueError: Raised if the source module file is not found.

    Returns:
        str: Entry point.
    """
    try:
        # raises FileNotFoundError if not found
        abs_path_source_module = Path(source_module).resolve(strict=True)
    except FileNotFoundError as e:
        raise ValueError(f"Source module not found: {source_module}") from e

    entry_point = entry_point or abs_path_source_module.stem
    _validate_entry_point(abs_path_source_module, entry_point)
    _tar_and_upload_to_code_location(abs_path_source_module, aws_session, code_location)
    return entry_point


def _validate_entry_point(source_module_path: Path, entry_point: str) -> None:
    """Confirm that a valid entry point relative to source module is given.

    Args:
        source_module_path (Path): Path to source module.
        entry_point (str): Entry point relative to source module.

    Raises:
        ValueError: Raised if the module was not found.
    """
    importable, _, _method = entry_point.partition(":")
    sys.path.append(str(source_module_path.parent))
    try:
        # second argument allows relative imports
        importlib.invalidate_caches()
        module = importlib.util.find_spec(importable, source_module_path.stem)
        if module is None:
            raise AssertionError  # noqa: TRY301
    except (ModuleNotFoundError, AssertionError) as e:
        raise ValueError(f"Entry point module was not found: {importable}") from e
    finally:
        sys.path.pop()


def _tar_and_upload_to_code_location(
    source_module_path: Path, aws_session: AwsSession, code_location: str
) -> None:
    """Tar and upload source module to code location.

    Args:
        source_module_path (Path): Path to source module.
        aws_session (AwsSession): AwsSession for uploading source module.
        code_location (str): S3 URI pointing to the location where the tarred
            source module will be uploaded to.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        with tarfile.open(f"{temp_dir}/source.tar.gz", "w:gz", dereference=True) as tar:
            tar.add(source_module_path, arcname=source_module_path.name)
        aws_session.upload_to_s3(f"{temp_dir}/source.tar.gz", f"{code_location}/source.tar.gz")


def _validate_params(dict_arr: dict[str, tuple[any, any]]) -> None:
    """Validate that config parameters are of the right type.

    Args:
        dict_arr (dict[str, tuple[any, any]]): dict mapping parameter names to
            a tuple containing the provided value and expected type.

    Raises:
        ValueError: If the user_input is not the same as the expected data type.
    """
    for parameter_name, value_tuple in dict_arr.items():
        user_input, expected_datatype = value_tuple

        if user_input and not isinstance(user_input, expected_datatype):
            raise ValueError(
                f"'{parameter_name}' should be of '{expected_datatype}' "
                f"but user provided {type(user_input)}."
            )


def _process_input_data(
    input_data: str | dict | S3DataSourceConfig,
    job_name: str,
    aws_session: AwsSession,
    subdirectory: str,
) -> list[dict[str, Any]]:
    """Convert input data into a list of dicts compatible with the Braket API.

    Args:
        input_data (str | dict | S3DataSourceConfig): Either a channel definition or a
            dictionary mapping channel names to channel definitions, where a channel definition
            can be an S3DataSourceConfig or a str corresponding to a local prefix or S3 prefix.
        job_name (str): Hybrid job name.
        aws_session (AwsSession): AwsSession for possibly uploading local data.
        subdirectory (str): Subdirectory within job name for S3 locations.

    Returns:
        list[dict[str, Any]]: A list of channel configs.
    """
    if not isinstance(input_data, dict):
        input_data = {"input": input_data}
    for channel_name, data in input_data.items():
        if not isinstance(data, S3DataSourceConfig):
            input_data[channel_name] = _process_channel(
                data, job_name, aws_session, channel_name, subdirectory
            )
    return _convert_input_to_config(input_data)


def _process_channel(
    location: str,
    job_name: str,
    aws_session: AwsSession,
    channel_name: str,
    subdirectory: str,
) -> S3DataSourceConfig:
    """Convert a location to an S3DataSourceConfig, uploading local data to S3, if necessary.

    Args:
        location (str): Local prefix or S3 prefix.
        job_name (str): Hybrid job name.
        aws_session (AwsSession): AwsSession to be used for uploading local data.
        channel_name (str): Name of the channel.
        subdirectory (str): Subdirectory within job name for S3 locations.

    Returns:
        S3DataSourceConfig: S3DataSourceConfig for the channel.
    """
    if AwsSession.is_s3_uri(location):
        return S3DataSourceConfig(location)
    # local prefix "path/to/prefix" will be mapped to
    # s3://bucket/jobs/job-name/subdirectory/data/input/prefix
    location_name = Path(location).name
    s3_prefix = AwsSession.construct_s3_uri(
        aws_session.default_bucket(),
        "jobs",
        job_name,
        subdirectory,
        "data",
        channel_name,
        location_name,
    )
    aws_session.upload_local_data(location, s3_prefix)
    return S3DataSourceConfig(s3_prefix)


def _convert_input_to_config(input_data: dict[str, S3DataSourceConfig]) -> list[dict[str, Any]]:
    """Convert a dictionary mapping channel names to S3DataSourceConfigs into a list of channel
    configs compatible with the Braket API.

    Args:
        input_data (dict[str, S3DataSourceConfig]): A dictionary mapping channel names to
            S3DataSourceConfig objects.

    Returns:
        list[dict[str, Any]]: A list of channel configs.
    """
    return [
        {
            "channelName": channel_name,
            **data_config.config,
        }
        for channel_name, data_config in input_data.items()
    ]


def _exclude_nones_factory(items: list[tuple]) -> dict:
    return {k: v for k, v in items if v is not None}
