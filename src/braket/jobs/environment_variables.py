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

import json
import os


def get_job_name() -> str:
    """Get the name of the current job.

    Returns:
        str: The name of the job if in a job, else an empty string.
    """
    return os.getenv("AMZN_BRAKET_JOB_NAME", "")


def get_job_device_arn() -> str:
    """Get the device ARN of the current job. If not in a job, default to "local:none/none".

    Returns:
        str: The device ARN of the current job or "local:none/none".
    """
    return os.getenv("AMZN_BRAKET_DEVICE_ARN", "local:none/none")


def get_input_data_dir(channel: str = "input") -> str:
    """Get the job input data directory.

    Args:
        channel (str): The name of the input channel. Default value
            corresponds to the default input channel name, `input`.

    Returns:
        str: The input directory, defaulting to current working directory.
    """
    input_dir = os.getenv("AMZN_BRAKET_INPUT_DIR", ".")
    return f"{input_dir}/{channel}" if input_dir != "." else input_dir


def get_results_dir() -> str:
    """Get the job result directory.

    Returns:
        str: The results directory, defaulting to current working directory.
    """
    return os.getenv("AMZN_BRAKET_JOB_RESULTS_DIR", ".")


def get_checkpoint_dir() -> str:
    """Get the job checkpoint directory.

    Returns:
        str: The checkpoint directory, defaulting to current working directory.
    """
    return os.getenv("AMZN_BRAKET_CHECKPOINT_DIR", ".")


def get_hyperparameters() -> dict[str, str]:
    """Get the job hyperparameters as a dict, with the values stringified.

    Returns:
        dict[str, str]: The hyperparameters of the job.
    """
    if "AMZN_BRAKET_HP_FILE" in os.environ:
        with open(os.getenv("AMZN_BRAKET_HP_FILE"), encoding="utf-8") as f:
            return json.load(f)
    return {}
