import json
import os
from typing import Dict


def get_job_name() -> str:
    """
    Get the name of the current job.

    Returns:
        str: The name of the job if in a job, else an empty string.
    """
    return os.getenv("AMZN_BRAKET_JOB_NAME", "")


def get_job_device_arn() -> str:
    """
    Get the device ARN of the current job. If not in a job, default to "local:none/none".

    Returns:
        str: The device ARN of the current job or "local:none/none".
    """
    return os.getenv("AMZN_BRAKET_DEVICE_ARN", "local:none/none")


def get_input_data_dir(channel: str = "input") -> str:
    """
    Get the job input data directory.

    Args:
        channel (str): The name of the input channel. Default value
            corresponds to the default input channel name, `input`.

    Returns:
        str: The input directory, defaulting to current working directory.
    """
    input_dir = os.getenv("AMZN_BRAKET_INPUT_DIR", ".")
    if input_dir != ".":
        return f"{input_dir}/{channel}"
    return input_dir


def get_results_dir() -> str:
    """
    Get the job result directory.

    Returns:
        str: The results directory, defaulting to current working directory.
    """
    return os.getenv("AMZN_BRAKET_JOB_RESULTS_DIR", ".")


def get_checkpoint_dir() -> str:
    """
    Get the job checkpoint directory.
    Returns:
        str: The checkpoint directory, defaulting to current working directory.
    """
    return os.getenv("AMZN_BRAKET_CHECKPOINT_DIR", ".")


def get_hyperparameters() -> Dict[str, str]:
    """
    Get the job checkpoint directory.
    Returns:
        str: The checkpoint directory, defaulting to current working directory.
    """
    if "AMZN_BRAKET_HP_FILE" in os.environ:
        with open(os.getenv("AMZN_BRAKET_HP_FILE"), "r") as f:
            return json.load(f)
    return {}
