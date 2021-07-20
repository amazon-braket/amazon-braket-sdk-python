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

import codecs
import os
import pickle
from typing import Any, Dict

from braket.jobs_data import PersistedJobData, PersistedJobDataFormat


def save_job_checkpoint(
    checkpoint_data: Dict[str, Any],
    checkpoint_file_suffix: str = "",
    data_format: PersistedJobDataFormat = PersistedJobDataFormat.PLAINTEXT,
) -> None:
    """
    Saves the specified `checkpoint_data` to the local output directory (specified by the container
    environment variable `CHECKPOINT_DIR`) with the filename
    `f"{job_name}(_{checkpoint_file_suffix}).json"`. The `job_name` refers to the name of the
    current job, and is retrieved from the container environment variable `JOB_NAME`. The
    `checkpoint_data` values are serialized to the specified `data_format`.

    Note: This function is only applicable for use inside the job container for storing
    the checkpoints.

    Args:
        checkpoint_data (Dict[str, Any]): Dict specifying the checkpoint data to be persisted.
        checkpoint_file_suffix (str): str specifying the file suffix to be used for
            the checkpoint filename. The resulting filename
            `f"{job_name}(_{checkpoint_file_suffix}).json"` will be used for saving the checkpoint
            file. Default: ""
        data_format (PersistedJobDataFormat): Data format to be used for serializing the
            values. Note that for `PICKLED` data formats, the values are base64 encoded
            after serialization. Default: PersistedJobDataFormat.PLAINTEXT

    Raises:
        ValueError: If the supplied `checkpoint_data` is `None` or empty.
    """
    if not checkpoint_data:
        raise ValueError("checkpoint_data can not be empty")
    checkpoint_directory = os.environ["CHECKPOINT_DIR"]
    job_name = os.environ["JOB_NAME"]
    checkpoint_file_path = (
        f"{checkpoint_directory}/{job_name}_{checkpoint_file_suffix}.json"
        if checkpoint_file_suffix
        else f"{checkpoint_directory}/{job_name}.json"
    )
    with open(checkpoint_file_path, "w") as f:
        serialized_data = _serialize_values(checkpoint_data or {}, data_format)
        persisted_data = PersistedJobData(dataDictionary=serialized_data, dataFormat=data_format)
        f.write(persisted_data.json())


def load_job_checkpoint(job_name: str, checkpoint_file_suffix: str = "") -> Dict[str, Any]:
    """
    Loads the job checkpoint data stored for the job with name 'job_name', with the checkpoint
    file ending with the `checkpoint_file_suffix`. The `job_name` can refer to any job whose
    checkpoint data you expect to be available in the file path specified by the `CHECKPOINT_DIR`
    container environment variable.

    Note: This function is only applicable for use inside the job container for loading job
    checkpoints.

    Args:
        job_name (str): str specifying the name of the job whose checkpoints
            need to be loaded.
        checkpoint_file_suffix (str): str specifying the file suffix to be used for
            locating the checkpoint file to load. The resulting file name
            `f"{job_name}(_{checkpoint_file_suffix}).json"` will be used for locating the
            checkpoint file. Default: ""

    Returns:
        Dict[str, Any]: Dict containing the checkpoint data persisted in the checkpoint file.

    Raises:
        FileNotFoundError: If the file `f"{job_name}(_{checkpoint_file_suffix})"` could not be found
            in the directory specified by the container environment variable `CHECKPOINT_DIR`.
        ValueError: If the data stored in the checkpoint file can't be deserialized (possibly due to
            corruption).
    """
    checkpoint_directory = os.environ["CHECKPOINT_DIR"]
    checkpoint_file_path = (
        f"{checkpoint_directory}/{job_name}_{checkpoint_file_suffix}.json"
        if checkpoint_file_suffix
        else f"{checkpoint_directory}/{job_name}.json"
    )
    with open(checkpoint_file_path, "r") as f:
        persisted_data = PersistedJobData.parse_raw(f.read())
        deserialized_data = _deserialize_values(
            persisted_data.dataDictionary, persisted_data.dataFormat
        )
        return deserialized_data


def save_job_result(
    result_data: Dict[str, Any],
    data_format: PersistedJobDataFormat = PersistedJobDataFormat.PLAINTEXT,
) -> None:
    """
    Saves the `result_data` to the local output directory (specified by the container
    environment variable `OUTPUT_DIR`) with the filename 'results.json'. The `result_data`
    values are serialized to the specified `data_format`.

    Note: This function is only applicable for use inside the job container for storing
    the results.

    Args:
        result_data (Dict[str, Any]): Dict specifying the result data to be persisted.
        data_format (PersistedJobDataFormat): Data format to be used for serializing the
            values. Note that for `PICKLED` data formats, the values are base64 encoded
            after serialization. Default: PersistedJobDataFormat.PLAINTEXT.

    Raises:
        ValueError: If the supplied `result_data` is `None` or empty.
    """
    if not result_data:
        raise ValueError("result_data can not be empty")
    result_directory = os.environ["OUTPUT_DIR"]
    result_path = f"{result_directory}/results.json"
    with open(result_path, "w") as f:
        serialized_data = _serialize_values(result_data or {}, data_format)
        persisted_data = PersistedJobData(dataDictionary=serialized_data, dataFormat=data_format)
        f.write(persisted_data.json())


def _serialize_values(
    data_dictionary: Dict[str, Any], data_format: PersistedJobDataFormat
) -> Dict[str, Any]:
    """
    Serializes the `data_dictionary` values to the format specified by `data_format`.

    Args:
        data_dictionary (Dict[str, Any]): Dict whose values need to be serialized.
        data_format (PersistedJobDataFormat): Data format to be used for serializing the
            values. Note that for `PICKLED` data formats, the values are base64 encoded
            after serialization (so that they represent valid UTF-8 text) and are compatible
            with `PersistedJobData.json()`.

    Returns:
        Dict[str, Any]: Dict with same keys as `data_dictionary`, and values serialized to
        the specified `data_format`.
    """
    return (
        {
            k: codecs.encode(pickle.dumps(v, protocol=4), "base64").decode()
            for k, v in data_dictionary.items()
        }
        if data_format == PersistedJobDataFormat.PICKLED_V4
        else data_dictionary
    )


def _deserialize_values(
    data_dictionary: Dict[str, Any], data_format: PersistedJobDataFormat
) -> Dict[str, Any]:
    """
    Deserializes the `data_dictionary` values from the format specified by `data_format`.

    Args:
        data_dictionary (Dict[str, Any]): Dict whose values need to be deserialized.
        data_format (PersistedJobDataFormat): Data format that the `data_dictionary` values
            are currently serialized with.

    Returns:
        Dict[str, Any]: Dict with same keys as `data_dictionary`, and values deserialized from
        the specified `data_format` to plaintext.
    """
    return (
        {k: pickle.loads(codecs.decode(v.encode(), "base64")) for k, v in data_dictionary.items()}
        if data_format == PersistedJobDataFormat.PICKLED_V4
        else data_dictionary
    )
