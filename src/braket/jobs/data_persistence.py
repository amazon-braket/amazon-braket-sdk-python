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

from pathlib import Path
from typing import Any

from braket.jobs.environment_variables import get_checkpoint_dir, get_job_name, get_results_dir
from braket.jobs.serialization import deserialize_values, serialize_values
from braket.jobs_data import PersistedJobData, PersistedJobDataFormat


def save_job_checkpoint(
    checkpoint_data: dict[str, Any],
    checkpoint_file_suffix: str = "",
    data_format: PersistedJobDataFormat = PersistedJobDataFormat.PLAINTEXT,
) -> None:
    """Saves the specified `checkpoint_data` to the local output directory, specified by
    the container environment variable `CHECKPOINT_DIR`, with the filename
    `f"{job_name}(_{checkpoint_file_suffix}).json"`. The `job_name` refers to the name of the
    current job and is retrieved from the container environment variable `JOB_NAME`. The
    `checkpoint_data` values are serialized to the specified `data_format`.

    Note: This function for storing the checkpoints is only for use inside the job container
          as it writes data to directories and references env variables set in the containers.


    Args:
        checkpoint_data (dict[str, Any]): Dict that specifies the checkpoint data to be persisted.
        checkpoint_file_suffix (str): str that specifies the file suffix to be used for
            the checkpoint filename. The resulting filename
            `f"{job_name}(_{checkpoint_file_suffix}).json"` is used to save the checkpoints.
            Default: ""
        data_format (PersistedJobDataFormat): The data format used to serialize the
            values. Note that for `PICKLED` data formats, the values are base64 encoded
            after serialization. Default: PersistedJobDataFormat.PLAINTEXT

    Raises:
        ValueError: If the supplied `checkpoint_data` is `None` or empty.
    """
    if not checkpoint_data:
        raise ValueError("The checkpoint_data argument cannot be empty.")
    checkpoint_directory = get_checkpoint_dir()
    job_name = get_job_name()
    checkpoint_file_path = (
        f"{checkpoint_directory}/{job_name}_{checkpoint_file_suffix}.json"
        if checkpoint_file_suffix
        else f"{checkpoint_directory}/{job_name}.json"
    )
    with open(checkpoint_file_path, "w", encoding="utf-8") as f:
        serialized_data = serialize_values(checkpoint_data or {}, data_format)
        persisted_data = PersistedJobData(dataDictionary=serialized_data, dataFormat=data_format)
        f.write(persisted_data.json())


def load_job_checkpoint(
    job_name: str | None = None, checkpoint_file_suffix: str = ""
) -> dict[str, Any]:
    """Loads the job checkpoint data stored for the job named 'job_name', with the checkpoint
    file that ends with the `checkpoint_file_suffix`. The `job_name` can refer to any job whose
    checkpoint data you expect to be available in the file path specified by the `CHECKPOINT_DIR`
    container environment variable. If not provided, this function will use the currently running
    job's name.

    Note: This function for loading hybrid job checkpoints is only for use inside the job container
          as it writes data to directories and references env variables set in the containers.


    Args:
        job_name (str | None): str that specifies the name of the job whose checkpoints
            are to be loaded. Default: current job name.

        checkpoint_file_suffix (str): str specifying the file suffix that is used to
            locate the checkpoint file to load. The resulting file name
            `f"{job_name}(_{checkpoint_file_suffix}).json"` is used to locate the
            checkpoint file. Default: ""

    Returns:
        dict[str, Any]: Dict that contains the checkpoint data persisted in the checkpoint file.

    Raises:
        FileNotFoundError: If the file `f"{job_name}(_{checkpoint_file_suffix})"` could not be found
            in the directory specified by the container environment variable `CHECKPOINT_DIR`.
        ValueError: If the data stored in the checkpoint file can't be deserialized (possibly due to
            corruption).
    """
    job_name = job_name or get_job_name()
    checkpoint_directory = get_checkpoint_dir()
    checkpoint_file_path = (
        f"{checkpoint_directory}/{job_name}_{checkpoint_file_suffix}.json"
        if checkpoint_file_suffix
        else f"{checkpoint_directory}/{job_name}.json"
    )
    with open(checkpoint_file_path, encoding="utf-8") as f:
        persisted_data = PersistedJobData.parse_raw(f.read())
        return deserialize_values(persisted_data.dataDictionary, persisted_data.dataFormat)


def _load_persisted_data(filename: str | Path | None = None) -> PersistedJobData:
    filename = filename or Path(get_results_dir()) / "results.json"
    try:
        with open(filename, encoding="utf-8") as f:
            return PersistedJobData.parse_raw(f.read())
    except FileNotFoundError:
        return PersistedJobData(
            dataDictionary={},
            dataFormat=PersistedJobDataFormat.PLAINTEXT,
        )


def load_job_result(filename: str | Path | None = None) -> dict[str, Any]:
    """Loads job result of currently running job.

    Args:
        filename (str | Path | None): Location of job results. Default `results.json` in job
            results directory in a job instance or in working directory locally. This file
            must be in the format used by `save_job_result`.

    Returns:
        dict[str, Any]: Job result data of current job
    """
    persisted_data = _load_persisted_data(filename)
    return deserialize_values(persisted_data.dataDictionary, persisted_data.dataFormat)


def save_job_result(
    result_data: dict[str, Any] | Any,
    data_format: PersistedJobDataFormat | None = None,
) -> None:
    """Saves the `result_data` to the local output directory that is specified by the container
    environment variable `AMZN_BRAKET_JOB_RESULTS_DIR`, with the filename 'results.json'.
    The `result_data` values are serialized to the specified `data_format`.

    Note: This function for storing the results is only for use inside the job container
          as it writes data to directories and references env variables set in the containers.

    Args:
        result_data (dict[str, Any] | Any): Dict that specifies the result data to be
            persisted. If result data is not a dict, then it will be wrapped as
            `{"result": result_data}`.
        data_format (PersistedJobDataFormat | None): The data format used to serialize the
            values. Note that for `PICKLED` data formats, the values are base64 encoded
            after serialization. Default: PersistedJobDataFormat.PLAINTEXT.

    Raises:
        TypeError: Unsupported data format.
    """
    if not isinstance(result_data, dict):
        result_data = {"result": result_data}

    current_persisted_data = _load_persisted_data()

    if current_persisted_data.dataFormat == PersistedJobDataFormat.PICKLED_V4:
        # if results are already pickled, maintain pickled format
        # if user explicitly specifies plaintext, raise error
        if data_format == PersistedJobDataFormat.PLAINTEXT:
            raise TypeError(
                "Cannot update results object serialized with "
                f"{current_persisted_data.dataFormat.value} using data format "
                f"{data_format.value}."
            )

        data_format = PersistedJobDataFormat.PICKLED_V4

    # if not specified or already pickled, default to plaintext
    data_format = data_format or PersistedJobDataFormat.PLAINTEXT

    current_results = deserialize_values(
        current_persisted_data.dataDictionary,
        current_persisted_data.dataFormat,
    )
    updated_results = current_results | result_data

    with open(Path(get_results_dir()) / "results.json", "w", encoding="utf-8") as f:
        serialized_data = serialize_values(updated_results or {}, data_format)
        persisted_data = PersistedJobData(dataDictionary=serialized_data, dataFormat=data_format)
        f.write(persisted_data.json())
