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

import json
import os
import tempfile
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Dict

from braket.aws.aws_session import AwsSession
from braket.jobs.local.local_job_container import _LocalJobContainer


def setup_container(
    container: _LocalJobContainer, aws_session: AwsSession, **creation_kwargs
) -> Dict[str, str]:
    """Sets up a container with prerequisites for running a Braket Job. The prerequisites are
    based on the options the customer has chosen for the job. Similarly, any environment variables
    that are needed during runtime will be returned by this function.

    Args:
        container(_LocalJobContainer): The container that will run the braket job.
        aws_session (AwsSession): AwsSession for connecting to AWS Services.
        **creation_kwargs: Keyword arguments for the boto3 Amazon Braket `CreateJob` operation.

    Returns:
        (Dict[str, str]): A dictionary of environment variables that reflect Braket Jobs options
        requested by the customer.
    """
    logger = getLogger(__name__)
    _create_expected_paths(container, **creation_kwargs)
    run_environment_variables = {}
    run_environment_variables.update(_get_env_credentials(aws_session, logger))
    run_environment_variables.update(
        _get_env_script_mode_config(creation_kwargs["algorithmSpecification"]["scriptModeConfig"])
    )
    run_environment_variables.update(_get_env_additional_lib())
    run_environment_variables.update(_get_env_default_vars(aws_session, **creation_kwargs))
    if _copy_hyperparameters(container, **creation_kwargs):
        run_environment_variables.update(_get_env_hyperparameters())
    if _copy_input_data_list(container, aws_session, logger, **creation_kwargs):
        run_environment_variables.update(_get_env_input_data())
    return run_environment_variables


def _create_expected_paths(container: _LocalJobContainer, **creation_kwargs) -> None:
    """Creates the basic paths required for Braket Jobs to run.

    Args:
        container(_LocalJobContainer): The container that will run the braket job.
        **creation_kwargs: Keyword arguments for the boto3 Amazon Braket `CreateJob` operation.
    """
    container.makedir("/opt/ml/model")
    container.makedir(creation_kwargs["checkpointConfig"]["localPath"])


def _get_env_credentials(aws_session: AwsSession, logger: Logger) -> Dict[str, str]:
    """Gets the account credentials from boto so they can be added as environment variables to
    the running container.

    Args:
        aws_session (AwsSession): AwsSession for connecting to AWS Services.
        logger (Logger): Logger object with which to write logs. Default is `getLogger(__name__)`

    Returns:
        (Dict[str, str]): The set of key/value pairs that should be added as environment variables
        to the running container.
    """
    credentials = aws_session.boto_session.get_credentials()
    if credentials.token is None:
        logger.info("Using the long-lived AWS credentials found in session")
        return {
            "AWS_ACCESS_KEY_ID": str(credentials.access_key),
            "AWS_SECRET_ACCESS_KEY": str(credentials.secret_key),
        }
    logger.warning(
        "Using the short-lived AWS credentials found in session. They might expire while running."
    )
    return {
        "AWS_ACCESS_KEY_ID": str(credentials.access_key),
        "AWS_SECRET_ACCESS_KEY": str(credentials.secret_key),
        "AWS_SESSION_TOKEN": str(credentials.token),
    }


def _get_env_script_mode_config(script_mode_config: Dict[str, str]) -> Dict[str, str]:
    """Gets the environment variables related to the customer script mode config.

    Args:
        script_mode_config (Dict[str, str]): The values for scriptModeConfig in the boto3 input
        parameters for running a Braket Job.

    Returns:
        (Dict[str, str]): The set of key/value pairs that should be added as environment variables
        to the running container.
    """
    result = {
        "AMZN_BRAKET_SCRIPT_S3_URI": script_mode_config["s3Uri"],
        "AMZN_BRAKET_SCRIPT_ENTRY_POINT": script_mode_config["entryPoint"],
    }
    if "compressionType" in script_mode_config:
        result["AMZN_BRAKET_SCRIPT_COMPRESSION_TYPE"] = script_mode_config["compressionType"]
    return result


def _get_env_additional_lib() -> Dict[str, str]:
    """For preview, we have some libraries that are not available publicly (yet). The container
    will install these libraries if we set this env variable.

    Returns:
        (Dict[str, str]): The set of key/value pairs that should be added as environment variables
        to the running container.
    """
    return {
        "AMZN_BRAKET_IMAGE_SETUP_SCRIPT": "s3://braket-external-assets-preview-us-west-2/"
        "HybridJobsAccess/scripts/setup-container.sh",
    }


def _get_env_default_vars(aws_session: AwsSession, **creation_kwargs) -> Dict[str, str]:
    """This function gets the remaining 'simple' env variables, that don't require any
     additional logic to determine what they are or when they should be added as env variables.

    Returns:
        (Dict[str, str]): The set of key/value pairs that should be added as environment variables
        to the running container.
    """
    job_name = creation_kwargs["jobName"]
    bucket, location = aws_session.parse_s3_uri(creation_kwargs["outputDataConfig"]["s3Path"])
    return {
        "AWS_DEFAULT_REGION": aws_session.region,
        "AMZN_BRAKET_JOB_NAME": job_name,
        "AMZN_BRAKET_DEVICE_ARN": creation_kwargs["deviceConfig"]["devices"][0],
        "AMZN_BRAKET_JOB_RESULTS_DIR": "/opt/braket/model",
        "AMZN_BRAKET_CHECKPOINT_DIR": creation_kwargs["checkpointConfig"]["localPath"],
        "AMZN_BRAKET_OUT_S3_BUCKET": bucket,
        "AMZN_BRAKET_TASK_RESULTS_S3_URI": f"s3://{bucket}/jobs/{job_name}/tasks",
        "AMZN_BRAKET_JOB_RESULTS_S3_PATH": f"{location}/{job_name}/output",
    }


def _get_env_hyperparameters():
    """Gets the env variable for hyperparameters. This should only be added if the customer has
    provided hyperpameters to the job.

    Returns:
        (Dict[str, str]): The set of key/value pairs that should be added as environment variables
        to the running container.
    """
    return {
        "AMZN_BRAKET_HP_FILE": "/opt/braket/input/config/hyperparameters.json",
    }


def _get_env_input_data():
    """Gets the env variable for input data. This should only be added if the customer has
    provided input data to the job.

    Returns:
        (Dict[str, str]): The set of key/value pairs that should be added as environment variables
        to the running container.
    """
    return {
        "AMZN_BRAKET_INPUT_DIR": "/opt/braket/input/data",
    }


def _copy_hyperparameters(container: _LocalJobContainer, **creation_kwargs) -> bool:
    """If hyperpameters are present, this function will store them as a JSON object in the
     container in the appropriate location on disk.

    Args:
        container(_LocalJobContainer): The container to save hyperparameters to.
        **creation_kwargs: Keyword arguments for the boto3 Amazon Braket `CreateJob` operation.

    Returns:
        (bool): True if any hyperparameters were copied to the container.
    """
    if "hyperParameters" not in creation_kwargs:
        return False
    hyperparameters = creation_kwargs["hyperParameters"]
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "hyperparameters.json")
        with open(file_path, "w") as write_file:
            json.dump(hyperparameters, write_file)
        container.copy_to(file_path, "/opt/ml/input/config/hyperparameters.json")
    return True


def _download_input_data(
    aws_session: AwsSession,
    s3_client: Any,
    download_dir: str,
    input_data: Dict[str, Any],
    logger: Logger,
) -> bool:
    """Downloads input data for a job.

    Args:
        aws_session (AwsSession): AwsSession for connecting to AWS Services.
        s3_client (Any): A boto3 s3 client.
        download_dir (str): The directory path to download to.
        input_data (Dict[str, Any]): One of the input data in the boto3 input parameters for
         running a Braket Job. We currently only support input data that are non-compressed
          files in S3.
        logger (Logger): Logger object with which to write logs. Default is `getLogger(__name__)`

    Returns:
        (bool): True if the input data was downloaded successfully.
    """
    if input_data["compressionType"] != "NONE":
        logger.warning(f"Not able to handle compression in input data. Skipping {input_data}")
        return False
    data_source = input_data["dataSource"]
    if "s3DataSource" not in data_source:
        logger.warning(f"Only able to handle S3 data source. Skipping {data_source}")
        return False
    s3_uri_prefix = input_data["dataSource"]["s3DataSource"]["s3Uri"]
    bucket, prefix = aws_session.parse_s3_uri(s3_uri_prefix)
    found_item = False
    has_more = True
    while has_more:
        kwargs = dict(Bucket=bucket, Prefix=prefix)
        list_objects = s3_client.list_objects_v2(**kwargs)
        for obj in list_objects["Contents"]:
            s3_key = obj["Key"]
            download_path = os.path.join(download_dir, s3_key)
            download_dir = os.path.dirname(download_path)
            Path(download_dir).mkdir(parents=True, exist_ok=True)
            s3_client.download_file(bucket, s3_key, download_path)
            found_item = True
        has_more = list_objects["IsTruncated"] and "NextContinuationToken" in list_objects
        if has_more:
            kwargs.update(ContinuationToken=list_objects["NextContinuationToken"])
    return found_item


def _copy_input_data_list(
    container: _LocalJobContainer, aws_session: AwsSession, logger: Logger, **creation_kwargs
) -> bool:
    """If the input data list is not empty, this function will download the input files and
    store them in the container.

    Args:
        container(_LocalJobContainer): The container to save input data to.
        aws_session (AwsSession): AwsSession for connecting to AWS Services.
        logger (Logger): Logger object with which to write logs. Default is `getLogger(__name__)`
        **creation_kwargs: Keyword arguments for the boto3 Amazon Braket `CreateJob` operation.

    Returns:
        (bool): True if any input data was copied to the container.
    """
    if "inputDataConfig" not in creation_kwargs:
        return False

    input_data_list = creation_kwargs["inputDataConfig"]
    s3_client = aws_session.s3_client
    with tempfile.TemporaryDirectory() as temp_dir:
        found_copy = False
        for input_data in input_data_list:
            if _download_input_data(aws_session, s3_client, temp_dir, input_data, logger):
                found_copy = True
        if found_copy:
            dir_contents = os.listdir(temp_dir)
            for dir_item in dir_contents:
                container.copy_to(os.path.join(temp_dir, dir_item), "/opt/ml/input/data/")
        return found_copy
