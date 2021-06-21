# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from dataclasses import dataclass
from enum import Enum


@dataclass
class MetricDefinition:
    """'name' specifies the name to use for the metric, 'regex' is the regular
    expression used to extract the metric from the logs.
    """

    name: str
    regex: str


class MetricPeriod(Enum):
    """Period over which the cloudwatch metric is aggregated."""

    ONE_MINUTE: int = 60


class MetricStatistic(Enum):
    """Metric data aggregation to use over the specified period."""

    # TODO: Check if we can extract this value directly from CloudWatch from statistics.
    AVG: str = "Average"
