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
from pathlib import Path
from typing import Any, Dict, List

from braket.aws.aws_session import AwsSession
from braket.jobs.config import (
    CheckpointConfig,
    DeviceConfig,
    InputDataConfig,
    InstanceConfig,
    OutputDataConfig,
    StoppingCondition,
    VpcConfig,
)


def prepare_quantum_job(
    device_arn: str,
    source_module: str,
    entry_point: str = None,
    image_uri: str = None,
    job_name: str = None,
    code_location: str = None,
    role_arn: str = None,
    hyperparameters: Dict[str, Any] = None,
    input_data_config: List[InputDataConfig] = None,
    instance_config: InstanceConfig = None,
    stopping_condition: StoppingCondition = None,
    output_data_config: OutputDataConfig = None,
    copy_checkpoints_from_job: str = None,
    checkpoint_config: CheckpointConfig = None,
    vpc_config: VpcConfig = None,
    aws_session: AwsSession = None,
):
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

        hyperparameters (Dict[str, Any]): Hyperparameters accessible to the job.
            The hyperparameters are made accessible as a Dict[str, str] to the job.
            For convenience, this accepts other types for keys and values, but `str()`
            is called to convert them before being passed on. Default: None.

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

    _validate_input(input_datatype_map)
    aws_session = aws_session or AwsSession()
    device_config = DeviceConfig(devices=[device_arn])
    job_name = job_name or _generate_default_job_name(image_uri)
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
        checkpoints_to_copy = aws_session.get_job(copy_checkpoints_from_job)["checkpointConfig"][
            "s3Uri"
        ]
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

    return create_job_kwargs


def _generate_default_job_name(image_uri: str):
    if not image_uri:
        job_type = "-default"
    else:
        job_type_match = re.search("/(.*)-jobs:", image_uri) or re.search("/([^:/]*)", image_uri)
        job_type = f"-{job_type_match.groups()[0]}" if job_type_match else ""

    return f"braket-job{job_type}-{time.time() * 1000:.0f}"


def _process_s3_source_module(source_module, entry_point, aws_session, code_location):
    if entry_point is None:
        raise ValueError("If source_module is an S3 URI, entry_point must be provided.")
    if not source_module.lower().endswith(".tar.gz"):
        raise ValueError(
            "If source_module is an S3 URI, it must point to a tar.gz file. "
            f"Not a valid S3 URI for parameter `source_module`: {source_module}"
        )
    aws_session.copy_s3_object(source_module, f"{code_location}/source.tar.gz")


def _process_local_source_module(source_module, entry_point, aws_session, code_location):
    try:
        # raises FileNotFoundError if not found
        abs_path_source_module = Path(source_module).resolve(strict=True)
    except FileNotFoundError:
        raise ValueError(f"Source module not found: {source_module}")

    entry_point = entry_point or abs_path_source_module.stem
    _validate_entry_point(abs_path_source_module, entry_point)
    _tar_and_upload_to_code_location(abs_path_source_module, aws_session, code_location)
    return entry_point


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


def _tar_and_upload_to_code_location(source_module_path, aws_session, code_location):
    with tempfile.TemporaryDirectory() as temp_dir:
        with tarfile.open(f"{temp_dir}/source.tar.gz", "w:gz", dereference=True) as tar:
            tar.add(source_module_path, arcname=source_module_path.name)
        aws_session.upload_to_s3(f"{temp_dir}/source.tar.gz", f"{code_location}/source.tar.gz")


def _validate_input(dict_arr):
    for parameter_name, value_tuple in dict_arr.items():
        user_input, expected_datatype = value_tuple

        if user_input:
            _validate_config_parameters(user_input, parameter_name, expected_datatype)


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
