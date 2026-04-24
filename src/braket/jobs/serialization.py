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
import pickle
from typing import Any

from braket.jobs_data import PersistedJobDataFormat


def serialize_values(
    data_dictionary: dict[str, Any], data_format: PersistedJobDataFormat
) -> dict[str, Any]:
    """Serializes the `data_dictionary` values to the format specified by `data_format`.

    Args:
        data_dictionary (dict[str, Any]): Dict whose values are to be serialized.
        data_format (PersistedJobDataFormat): The data format used to serialize the
            values. Note that for `PICKLED` data formats, the values are base64 encoded
            after serialization, so that they represent valid UTF-8 text and are compatible
            with `PersistedJobData.json()`.

    Returns:
        dict[str, Any]: Dict with same keys as `data_dictionary` and values serialized to
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


def deserialize_values(
    data_dictionary: dict[str, Any],
    data_format: PersistedJobDataFormat,
    allow_pickle: bool = False,
) -> dict[str, Any]:
    """Deserializes the `data_dictionary` values from the format specified by `data_format`.

    Args:
        data_dictionary (dict[str, Any]): Dict whose values are to be deserialized.
        data_format (PersistedJobDataFormat): The data format that the `data_dictionary` values
            are currently serialized with.
        allow_pickle (bool): Whether to allow deserialization of pickled data. Pickle
            deserialization can execute arbitrary code and is unsafe on untrusted data.
            Default: False.

    Returns:
        dict[str, Any]: Dict with same keys as `data_dictionary` and values deserialized from
        the specified `data_format` to plaintext.

    Raises:
        RuntimeError: If data format is PICKLED_V4 and allow_pickle is False.
    """
    if data_format == PersistedJobDataFormat.PICKLED_V4:
        if not allow_pickle:
            raise RuntimeError(
                "Data is in PICKLED_V4 format, but pickle deserialization is disabled by "
                "default due to security concerns. Pickle deserialization can execute arbitrary "
                "code and is unsafe on untrusted data. To enable pickle deserialization, pass "
                "allow_pickle=True to the calling function (e.g. job.result(allow_pickle=True), "
                "load_job_result(allow_pickle=True), or load_job_checkpoint(allow_pickle=True)). "
                "Only do this if you trust the source of the data."
            )
        return {
            k: pickle.loads(codecs.decode(v.encode(), "base64"))  # noqa: S301
            for k, v in data_dictionary.items()
        }
    return data_dictionary
