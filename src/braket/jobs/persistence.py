from typing import Dict, Any

# Below classes will be added in braket_schemas and have added here just for reference.
from enum import Enum


class JobFormat(Enum):
    """
    Enum class for the the required formats.
    """

    PLAINTEXT = None
    PICKLED = None


class PersistedJobDataFormat:
    """
    This is the model used by save_job_result/save_job_checkpoint/load_job_checkpoint.
    It defines how the dictionary passed in to the save* functions is persisted, and
    what the load_job_checkpoint function expects the persisted data to look like.
    """

    dataDictionary: dict[str, Any]
    format: Enum[JobFormat.PLAINTEXT, JobFormat.PICKLED]


# Functions defined for this file.


def save_job_checkpoint(
    checkpoint_data: Dict[str, Any],
    checkpoint_file_suffix: str = "",
    format: PersistedJobDataFormat = PersistedJobDataFormat.format.PLAINTEXT,
):
    """
    Saves the specified checkpoint data to the job's CheckpointConfig.localPath
    directory with the file name f'{JOB_NAME}#{checkpoint_file_suffix}'

    Args:
        checkpoint_data(Dict[str, Any]): Dict specifying the checkpoint data to be
          persisted.
        checkpoint_file_suffix(str): str specifying the file suffix to be used for
          the checkpoint file name. (default: '')
        pickled(bool): bool indicating whether the values in checkpoint_data should
          be pickled.
    """


def load_job_checkpoint(job_name: str, checkpoint_file_suffix: str = "") -> Dict[str, Any]:
    """
    Loads the job checkpoint data for 'job_name' with the checkpoint file ending
    with the checkpoint_file_suffix from the job's CheckpointConfig.localPath directory.
    Note that this method is guaranteed to work only for checkpoints persisted with
    the PersistedJobData model.

    Args:
        job_name(str): str specifying the job_name for the job whose checkpoints
           would be loaded.
        checkpoint_file_suffix(str): str specifying the file suffix to be used for
          locating the checkpoint file to load. (default: '')

    Returns:
        Dict[str, Any]: Dict containing the checkpoint data that had been persisted
        earlier.
    """


def save_job_result(
    result_data: Dict[str, Any],
    format: PersistedJobDataFormat = PersistedJobDataFormat.format.PLAINTEXT,
):
    """
    Saves the result_data to the local output directory with the filename 'result.json'.

    Args:
        result_data(Dict[str, Any]): Dict specifying the result data to be persisted.
        pickled(bool): bool indicating whether the result values should be pickled.
          (default: False)
    """
