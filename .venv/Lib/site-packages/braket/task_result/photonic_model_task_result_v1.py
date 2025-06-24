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
# language governing permissions and limitations under the License

from typing import Optional

from pydantic.v1 import Field, conint, conlist

from braket.schema_common import BraketSchemaBase, BraketSchemaHeader
from braket.task_result.additional_metadata import AdditionalMetadata
from braket.task_result.task_metadata_v1 import TaskMetadata


class PhotonicModelTaskResult(BraketSchemaBase):
    """
    The photonic model task result schema

    Attributes:
        braketSchemaHeader (BraketSchemaHeader): Schema header. Users do not need
            to set this value. Only default is allowed.
        measurements (List[List[List[int]]]: List of lists of lists of int, where each
            int is bound between 0-255. Default is `None`.
        taskMetadata (TaskMetadata): The task metadata
        additionalMetadata (AdditionalMetadata): Additional metadata of the task
    """

    _PHOTONIC_MODEL_TASK_RESULT_HEADER = BraketSchemaHeader(
        name="braket.task_result.photonic_model_task_result", version="1"
    )

    braketSchemaHeader: BraketSchemaHeader = Field(
        default=_PHOTONIC_MODEL_TASK_RESULT_HEADER, const=_PHOTONIC_MODEL_TASK_RESULT_HEADER
    )
    measurements: Optional[
        conlist(conlist(conlist(conint(ge=0, le=256), min_items=1), min_items=1), min_items=1)
    ]
    taskMetadata: TaskMetadata
    additionalMetadata: AdditionalMetadata
