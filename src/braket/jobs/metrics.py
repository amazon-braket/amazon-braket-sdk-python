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

import time


def log_metric(
    metric_name: str,
    value: float,
    timestamp: float | None = None,
    iteration_number: int | None = None,
) -> None:
    """Records Braket Hybrid Job metrics.

    Args:
        metric_name (str): The name of the metric.

        value (float): The value of the metric.

        timestamp (float | None): The time the metric data was received, expressed
            as the number of seconds since the epoch. Default: Current system time.

        iteration_number (int | None): The iteration number of the metric.
    """
    logged_timestamp = timestamp or time.time()
    metric_list = [f"Metrics - timestamp={logged_timestamp}; {metric_name}={value};"]
    if iteration_number is not None:
        metric_list.append(f" iteration_number={iteration_number};")
    metric_line = "".join(metric_list)
    print(metric_line)
