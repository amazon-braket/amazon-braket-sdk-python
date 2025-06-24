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

from typing import Optional

from pydantic.v1 import Field, confloat, constr

from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


class IonQMetadata(BraketSchemaBase):
    """
    Metadata for results of IonQ tasks.

    Attributes:
        braketSchemaHeader (BraketSchemaHeader): Schema header.
            Users do not need to set this value. Only default is allowed.
        sharpenedProbabilities (Optional[dict[str, float]]): The histogram of results after
            postprocessing with sharpening. Default: None.
    """

    _IONQ_METADATA_HEADER = BraketSchemaHeader(name="braket.task_result.ionq_metadata", version="1")
    braketSchemaHeader: BraketSchemaHeader = Field(
        default=_IONQ_METADATA_HEADER, const=_IONQ_METADATA_HEADER
    )
    sharpenedProbabilities: Optional[
        dict[constr(regex="^[01]+$", min_length=1), confloat(ge=0, le=1)]
    ] = None
