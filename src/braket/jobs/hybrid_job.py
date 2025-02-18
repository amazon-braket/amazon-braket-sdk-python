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

import functools
import importlib.util
import inspect
import os
import re
import shutil
import sys
import tempfile
import warnings
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from logging import Logger, getLogger
from pathlib import Path
from types import CodeType, ModuleType
from typing import Any

import cloudpickle

from braket.aws.aws_session import AwsSession
from braket.jobs._entry_point_template import run_entry_point, symlink_input_data
from braket.jobs.config import (
    CheckpointConfig,
    InstanceConfig,
    OutputDataConfig,
    S3DataSourceConfig,
    StoppingCondition,
)
from braket.jobs.image_uris import Framework, built_in_images, retrieve_image
from braket.jobs.local.local_job_container_setup import _get_env_input_data
from braket.jobs.quantum_job import QuantumJob
from braket.jobs.quantum_job_creation import _generate_default_job_name

DEFAULT_INPUT_CHANNEL = "input"
INNER_FUNCTION_SOURCE_INPUT_CHANNEL = "_braket_job_decorator_inner_function_source"
INNER_FUNCTION_SOURCE_INPUT_FOLDER = "_inner_function_source_folder"


def hybrid_job(
    *,
    device: str | None,
    include_modules: str | ModuleType | Iterable[str | ModuleType] | None = None,
    dependencies: str | Path | list[str] | None = None,
    local: bool = False,
    job_name: str | None = None,
    image_uri: str | None = None,
    input_data: str | dict | S3DataSourceConfig | None = None,
    wait_until_complete: bool = False,
    instance_config: InstanceConfig | None = None,
    distribution: str | None = None,
    copy_checkpoints_from_job: str | None = None,
    checkpoint_config: CheckpointConfig | None = None,
    role_arn: str | None = None,
    stopping_condition: StoppingCondition | None = None,
    output_data_config: OutputDataConfig | None = None,
    aws_session: AwsSession | None = None,
    tags: dict[str, str] | None = None,
    logger: Logger = getLogger(__name__),
    quiet: bool | None = None,
    reservation_arn: str | None = None,
) -> Callable:
    """Defines a hybrid job by decorating the entry point function. The job will be created
    when the decorated function is called.

    The job created will be a `LocalQuantumJob` when `local` is set to `True`, otherwise an
    `AwsQuantumJob`. The following parameters will be ignored when running a job with
    `local` set to `True`: `wait_until_complete`, `instance_config`, `distribution`,
    `copy_checkpoints_from_job`, `stopping_condition`, `tags`, `logger`, and `quiet`.

    Remarks:
        Hybrid jobs created using this decorator have limited access to the source code of
        functions defined outside of the decorated function. Functionality that depends on
        source code analysis may not work properly when referencing functions defined outside
        of the decorated function.

    Args:
        device (str | None): Device ARN of the QPU device that receives priority quantum
            task queueing once the hybrid job begins running. Each QPU has a separate hybrid jobs
            queue so that only one hybrid job is running at a time. The device string is accessible
            in the hybrid job instance as the environment variable "AMZN_BRAKET_DEVICE_ARN".
            When using embedded simulators, you may provide the device argument as string of the
            form: "local:<provider>/<simulator_name>" or `None`.

        include_modules (str | ModuleType | Iterable[str | ModuleType] | None): Either a
            single module or module name or a list of module or module names referring to local
            modules to be included. Any references to members of these modules in the hybrid job
            algorithm code will be serialized as part of the algorithm code. Default: `[]`

        dependencies (str | Path | list[str] | None): Path (absolute or relative) to a
            requirements.txt file, or alternatively a list of strings, with each string being a
            `requirement specifier <https://pip.pypa.io/en/stable/reference/requirement-specifiers/
            #requirement-specifiers>`_, to be used for the hybrid job.

        local (bool): Whether to use local mode for the hybrid job. Default: `False`

        job_name (str | None): A string that specifies the name with which the job is created.
            Allowed pattern for job name: `^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,50}$`. Defaults to
            f'{decorated-function-name}-{timestamp}'.

        image_uri (str | None): A str that specifies the ECR image to use for executing the job.
            `retrieve_image()` function may be used for retrieving the ECR image URIs
            for the containers supported by Braket. Default: `<Braket base image_uri>`.

        input_data (str | dict | S3DataSourceConfig | None): Information about the training
            data. Dictionary maps channel names to local paths or S3 URIs. Contents found
            at any local paths will be uploaded to S3 at
            f's3://{default_bucket_name}/jobs/{job_name}/data/{channel_name}'. If a local
            path, S3 URI, or S3DataSourceConfig is provided, it will be given a default
            channel name "input".
            Default: {}.

        wait_until_complete (bool): `True` if we should wait until the job completes.
            This would tail the job logs as it waits. Otherwise `False`. Ignored if using
            local mode. Default: `False`.

        instance_config (InstanceConfig | None): Configuration of the instance(s) for running the
            classical code for the hybrid job. Default:
            `InstanceConfig(instanceType='ml.m5.large', instanceCount=1, volumeSizeInGB=30)`.

        distribution (str | None): A str that specifies how the job should be distributed.
            If set to "data_parallel", the hyperparameters for the job will be set to use data
            parallelism features for PyTorch or TensorFlow. Default: `None`.

        copy_checkpoints_from_job (str | None): A str that specifies the job ARN whose
            checkpoint you want to use in the current job. Specifying this value will copy
            over the checkpoint data from `use_checkpoints_from_job`'s checkpoint_config
            s3Uri to the current job's checkpoint_config s3Uri, making it available at
            checkpoint_config.localPath during the job execution. Default: `None`

        checkpoint_config (CheckpointConfig | None): Configuration that specifies the
            location where checkpoint data is stored.
            Default: `CheckpointConfig(localPath='/opt/jobs/checkpoints',
            s3Uri=f's3://{default_bucket_name}/jobs/{job_name}/checkpoints')`.

        role_arn (str | None): A str providing the IAM role ARN used to execute the
            script. Default: IAM role returned by AwsSession's `get_default_jobs_role()`.

        stopping_condition (StoppingCondition | None): The maximum length of time, in seconds,
            and the maximum number of tasks that a job can run before being forcefully stopped.
            Default: StoppingCondition(maxRuntimeInSeconds=5 * 24 * 60 * 60).

        output_data_config (OutputDataConfig | None): Specifies the location for the output of
            the job.
            Default: `OutputDataConfig(s3Path=f's3://{default_bucket_name}/jobs/{job_name}/data',
            kmsKeyId=None)`.

        aws_session (AwsSession | None): AwsSession for connecting to AWS Services.
            Default: AwsSession()

        tags (dict[str, str] | None): Dict specifying the key-value pairs for tagging this job.
            Default: {}.

        logger (Logger): Logger object with which to write logs, such as task statuses
            while waiting for task to be in a terminal state. Default: `getLogger(__name__)`

        quiet (bool | None): Sets the verbosity of the logger to low and does not report queue
            position. Default is `False`.

        reservation_arn (str | None): the reservation window arn provided by Braket
            Direct to reserve exclusive usage for the device to run the hybrid job on.
            Default: None.

    Returns:
        Callable: the callable for creating a Hybrid Job.
    """
    _validate_python_version(image_uri, aws_session)

    def _hybrid_job(entry_point: Callable) -> Callable:
        @functools.wraps(entry_point)
        def job_wrapper(*args: Any, **kwargs: Any) -> Callable:
            """The job wrapper.

            Args:
                *args (Any): Arbitrary arguments.
                **kwargs (Any): Arbitrary keyword arguments.

            Returns:
                Callable: the callable for creating a Hybrid Job.
            """
            with (
                _IncludeModules(include_modules),
                tempfile.TemporaryDirectory(dir="", prefix="decorator_job_") as temp_dir,
                persist_inner_function_source(entry_point) as inner_source_input,
            ):
                job_input_data = _add_inner_function_source_to_input_data(
                    input_data, inner_source_input
                )

                temp_dir_path = Path(temp_dir)
                entry_point_file_path = Path("entry_point.py")
                with open(
                    temp_dir_path / entry_point_file_path, "w", encoding="utf-8"
                ) as entry_point_file:
                    template = "\n".join([
                        _process_input_data(input_data),
                        _serialize_entry_point(entry_point, args, kwargs),
                    ])
                    entry_point_file.write(template)

                if dependencies:
                    _process_dependencies(dependencies, temp_dir_path)

                job_args = {
                    "device": device or "local:none/none",
                    "source_module": temp_dir,
                    "entry_point": (
                        f"{temp_dir}.{entry_point_file_path.stem}:{entry_point.__name__}"
                    ),
                    "wait_until_complete": wait_until_complete,
                    "job_name": job_name or _generate_default_job_name(func=entry_point),
                    "hyperparameters": _log_hyperparameters(entry_point, args, kwargs),
                    "logger": logger,
                }
                optional_args = {
                    "image_uri": image_uri,
                    "input_data": job_input_data,
                    "instance_config": instance_config,
                    "distribution": distribution,
                    "checkpoint_config": checkpoint_config,
                    "copy_checkpoints_from_job": copy_checkpoints_from_job,
                    "role_arn": role_arn,
                    "stopping_condition": stopping_condition,
                    "output_data_config": output_data_config,
                    "aws_session": aws_session,
                    "tags": tags,
                    "quiet": quiet,
                    "reservation_arn": reservation_arn,
                }
                job_args.update({key: val for key, val in optional_args.items() if val is not None})
                return _create_job(job_args, local)

        return job_wrapper

    return _hybrid_job


@contextmanager
def persist_inner_function_source(entry_point: callable) -> None:
    """Persist the source code of the cloudpickled function by saving its source code as input data
    and replace the source file path with the saved one.
    Args:
        entry_point (callable): The job decorated function.

    Yields:
        dict: if the inner function exists, a mapping of the input channel to the copy directory.
            Otherwise an empty dict
    """
    inner_source_mapping = _get_inner_function_source(entry_point.__code__)

    if len(inner_source_mapping) == 0:
        yield {}
    else:
        with tempfile.TemporaryDirectory(dir="", prefix="decorator_job_inner_source_") as temp_dir:
            copy_dir = f"{temp_dir}/{INNER_FUNCTION_SOURCE_INPUT_FOLDER}"
            os.mkdir(copy_dir)
            path_mapping = _save_inner_source_to_file(inner_source_mapping, copy_dir)
            entry_point.__code__ = _replace_inner_function_source_path(
                entry_point.__code__, path_mapping
            )
            yield {INNER_FUNCTION_SOURCE_INPUT_CHANNEL: copy_dir}


def _replace_inner_function_source_path(
    code_object: CodeType, path_mapping: dict[str, str]
) -> CodeType:
    """Recursively replace source code file path of the code object and of its child node's code
    objects.
    Args:
        code_object (CodeType): Code object which source code file path to be replaced.
        path_mapping (dict[str, str]): Mapping between local file path to path in a job
            environment.
    Returns:
        CodeType: Code object with the source code file path replaced
    """
    new_co_consts = []
    for const in code_object.co_consts:
        new_const = const
        if inspect.iscode(const):
            new_path = path_mapping[const.co_filename]
            new_const = const.replace(co_filename=new_path)
            new_const = _replace_inner_function_source_path(new_const, path_mapping)
        new_co_consts.append(new_const)

    return code_object.replace(co_consts=tuple(new_co_consts))


def _save_inner_source_to_file(inner_source: dict[str, str], input_data_dir: str) -> dict[str, str]:
    """Saves the source code as input data for a job and returns a dictionary that maps the local
    source file path of a function to the one to be used in the job environment.
    Args:
        inner_source (dict[str, str]): Mapping between source file name and source code.
        input_data_dir (str): The path of the folder to be uploaded to job as input data.
    Returns:
        dict[str, str]: Mapping between local file path to path in a job environment.
    """
    path_mapping = {}
    for i, (local_path, source_code) in enumerate(inner_source.items()):
        copy_file_name = f"source_{i}.py"
        with open(f"{input_data_dir}/{copy_file_name}", "w", encoding="utf-8") as f:
            f.write(source_code)

        path_mapping[local_path] = os.path.join(
            _get_env_input_data()["AMZN_BRAKET_INPUT_DIR"],
            INNER_FUNCTION_SOURCE_INPUT_CHANNEL,
            copy_file_name,
        )
    return path_mapping


def _get_inner_function_source(code_object: CodeType) -> dict[str, str]:
    """Returns a dictionary that maps the source file name to source code for all source files
    used by the inner functions inside the job decorated function.
    Args:
        code_object (CodeType): Code object of a inner function.
    Returns:
        dict[str, str]: Mapping between source file name and source code.
    """
    inner_source = {}
    for const in code_object.co_consts:
        if inspect.iscode(const):
            source_file_path = inspect.getfile(code_object)
            lines, _ = inspect.findsource(code_object)
            inner_source.update({source_file_path: "".join(lines)})
            inner_source.update(_get_inner_function_source(const))
    return inner_source


def _add_inner_function_source_to_input_data(input_data: dict, inner_source_input: dict) -> dict:
    """Add the path of inner function source file as the input data of the job.

    Args:
        input_data (dict): Provided input data of the job.
        inner_source_input (dict): A dict that points to the path of inner function source file.

    Returns:
        dict: input_data with inner function source file added.
    """
    if input_data is None:
        job_input_data = inner_source_input
    elif isinstance(input_data, dict):
        if INNER_FUNCTION_SOURCE_INPUT_CHANNEL in input_data:
            raise ValueError(f"input channel cannot be {INNER_FUNCTION_SOURCE_INPUT_CHANNEL}")
        job_input_data = {**input_data, **inner_source_input}
    else:
        job_input_data = {DEFAULT_INPUT_CHANNEL: input_data, **inner_source_input}
    return job_input_data


def _validate_python_version(image_uri: str | None, aws_session: AwsSession | None = None) -> None:
    """Validate python version at job definition time"""
    aws_session = aws_session or AwsSession()
    # user provides a custom image_uri
    if image_uri and image_uri not in built_in_images(aws_session.region):
        print(
            "Skipping python version validation, make sure versions match "
            "between local environment and container."
        )
    else:
        # set default image_uri to base
        image_uri = image_uri or retrieve_image(Framework.BASE, aws_session.region)
        tag = aws_session.get_full_image_tag(image_uri)
        major_version, minor_version = re.search(r"-py(\d)(\d+)-", tag).groups()
        if (sys.version_info.major, sys.version_info.minor) != (
            int(major_version),
            int(minor_version),
        ):
            raise RuntimeError(
                "Python version must match between local environment and container. "
                f"Client is running Python {sys.version_info.major}.{sys.version_info.minor} "
                f"locally, but container uses Python {major_version}.{minor_version}."
            )


def _process_dependencies(dependencies: str | Path | list[str], temp_dir: Path) -> None:
    if isinstance(dependencies, (str, Path)):
        # requirements file
        shutil.copy(Path(dependencies).resolve(), temp_dir / "requirements.txt")
    else:
        # list of packages
        with open(temp_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(dependencies))


class _IncludeModules:
    def __init__(self, modules: str | ModuleType | Iterable[str | ModuleType] | None = None):
        modules = modules or []
        if isinstance(modules, (str, ModuleType)):
            modules = [modules]
        self._modules = [
            (importlib.import_module(module) if isinstance(module, str) else module)
            for module in modules
        ]

    def __enter__(self):
        """Register included modules with cloudpickle to be pickled by value"""
        for module in self._modules:
            cloudpickle.register_pickle_by_value(module)

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
        """Unregister included modules with cloudpickle to be pickled by value"""
        for module in self._modules:
            cloudpickle.unregister_pickle_by_value(module)


def _serialize_entry_point(entry_point: Callable, args: tuple, kwargs: dict) -> str:
    """Create an entry point from a function"""
    wrapped_entry_point = functools.partial(entry_point, *args, **kwargs)

    try:
        serialized = cloudpickle.dumps(wrapped_entry_point)
    except Exception as e:
        raise RuntimeError(
            "Serialization failed for decorator hybrid job. If you are referencing "
            "an object from outside the function scope, either directly or through "
            "function parameters, try instantiating the object inside the decorated "
            "function instead."
        ) from e

    return run_entry_point.format(
        serialized=serialized,
        function_name=entry_point.__name__,
    )


def _log_hyperparameters(entry_point: Callable, args: tuple, kwargs: dict) -> dict:
    """Capture function arguments as hyperparameters"""
    signature = inspect.signature(entry_point)
    bound_args = signature.bind(*args, **kwargs)
    bound_args.apply_defaults()
    hyperparameters = {}
    for param, value in bound_args.arguments.items():
        param_kind = signature.parameters[param].kind
        if param_kind in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }:
            hyperparameters[param] = value
        elif param_kind == inspect.Parameter.VAR_KEYWORD:
            hyperparameters.update(**value)
        else:
            warnings.warn(
                "Positional only arguments will not be logged to the hyperparameters file.",
                stacklevel=1,
            )
    return {name: _sanitize(value) for name, value in hyperparameters.items()}


def _sanitize(hyperparameter: Any) -> str:
    """Sanitize forbidden characters from hp strings"""
    string_hp = str(hyperparameter)

    sanitized = (
        string_hp
        # replace forbidden characters with close matches
        .replace("\n", " ")
        .replace("$", "?")
        .replace("(", "{")
        .replace("&", "+")
        .replace("`", "'")
        # not technically forbidden, but to avoid mismatched parens
        .replace(")", "}")
    )

    # max allowed length for a hyperparameter is 2500
    if len(sanitized) > 2500:
        # show as much as possible, including the final 20 characters
        return f"{sanitized[: 2500 - 23]}...{sanitized[-20:]}"
    return sanitized


def _process_input_data(input_data: dict) -> list[str]:
    """Create symlinks to data.

    Logic chart for how the service moves files into the data directory on the instance:
        input data matches exactly one file: cwd/filename -> channel/filename
        input data matches exactly one directory: cwd/dirname/* -> channel/*
        else (multiple matches, possibly including exact):
            cwd/prefix_match -> channel/prefix_match, for each match
    """
    input_data = input_data or {}
    if not isinstance(input_data, dict):
        input_data = {"input": input_data}

    def matches(prefix: str) -> list[str]:
        return [str(path) for path in Path(prefix).parent.iterdir() if str(path).startswith(prefix)]

    def is_prefix(path: str) -> bool:
        return len(matches(path)) > 1 or not Path(path).exists()

    prefix_channels = set()
    directory_channels = set()
    file_channels = set()

    for channel, data in input_data.items():
        if AwsSession.is_s3_uri(str(data)) or isinstance(data, S3DataSourceConfig):
            channel_arg = f'channel="{channel}"' if channel != "input" else ""
            print(
                "Input data channels mapped to an S3 source will not be available in "
                f"the working directory. Use `get_input_data_dir({channel_arg})` to read "
                f"input data from S3 source inside the job container."
            )
        elif is_prefix(str(data)):
            prefix_channels.add(channel)
        elif Path(data).is_dir():
            directory_channels.add(channel)
        else:
            file_channels.add(channel)

    return symlink_input_data.format(
        prefix_matches={channel: matches(input_data[channel]) for channel in prefix_channels},
        input_data_items=[
            (channel, data)
            for channel, data in input_data.items()
            if channel in prefix_channels | directory_channels | file_channels
        ],
        prefix_channels=prefix_channels,
        directory_channels=directory_channels,
    )


def _create_job(job_args: dict[str, Any], local: bool = False) -> QuantumJob:
    """Create an AWS or Local hybrid job"""
    if local:
        from braket.jobs.local import LocalQuantumJob  # noqa: PLC0415

        for aws_only_arg in [
            "wait_until_complete",
            "copy_checkpoints_from_job",
            "instance_config",
            "distribution",
            "stopping_condition",
            "tags",
            "logger",
        ]:
            job_args.pop(aws_only_arg, None)
        return LocalQuantumJob.create(**job_args)
    from braket.aws import AwsQuantumJob  # noqa: PLC0415

    return AwsQuantumJob.create(**job_args)
