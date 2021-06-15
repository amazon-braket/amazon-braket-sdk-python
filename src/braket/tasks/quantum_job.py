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

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from braket.utils.metric_period import MetricPeriod
from braket.utils.metric_statistic import MetricStatistic


class QuantumJob(ABC):
    """An abstraction over a quantum task on a quantum device."""

    @property
    @abstractmethod
    def id(self) -> str:
        """str: The task ID."""

    @property
    @abstractmethod
    def arn(self) -> str:
        """Returns the job arn corresponding to the job"""

    @property
    @abstractmethod
    def state(self) -> str:
        """Returns the status for the job"""

    @abstractmethod
    def logs(self) -> None:
        """Prints the logs from cloudwatch to stdout"""

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Returns the job metadata defined in Amazon Braket (uses the GetJob API call)"""

    @abstractmethod
    def metrics(self,
                metric_names: List[str] = None,
                period: MetricPeriod = MetricPeriod.ONE_MINUTE,
                statistic: MetricStatistic = MetricStatistic.AVG,
                ) -> Dict[str, Any]:
        """
        Note: The function definition here is subject to change depending on our metric
        strategy for the console.

        Queries cloudwatch to retrieve the metric values for the specified metric_names
        for the job.

        Args:
        metric_names(List[str]): Metric names to retrieve for the job.
            (default: All custom metrics + host metrics)
        period(MetricPeriod): Period over which the cloudwatch metric is aggregated.
            (default: MetricPeriod.ONE_MINUTE)
        statistic(MetricStatistic): Metric data aggregation to use over the specified
            period. (default: MetricStatistic.AVG)

        Returns:
            Dict[str, Any]: Dict containing the metric information represented with the keys
            "timestamp", "metric_name" and "value"
        """

    @abstractmethod
    def cancel(self) -> str:
        """Cancels the job

        Returns:
            str: Representing the status of the job.
        """

    @abstractmethod
    def result(self) -> Dict[str, Any]:
        """
        Retrieves the job result persisted using save_job_result() function.

        Returns:
            Dict[str, Any]: Dict specifying the job results.
        """

    @abstractmethod
    def download_results(self, extract_to=None) -> None:
        """Downloads the results from the job output S3 bucket and extracts the tar.gz
        bundle to the location specified by 'extract_to'. If no location is specified,
        the results are extracted to the current directory."""
