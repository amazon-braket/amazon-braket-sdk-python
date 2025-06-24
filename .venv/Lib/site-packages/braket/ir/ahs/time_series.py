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

from decimal import Decimal

from pydantic.v1 import BaseModel


class TimeSeries(BaseModel):
    """
    Specifies the TimeSeries, real-valued time series

    Attributes:
        values: list[float]
        times: list[float], ascending

    Examples:
       >>> TimeSeries(values=[-1.25664e8,1.25664e8],times=[0.0,3.0e-6])
    """

    values: list[Decimal]
    times: list[Decimal]
