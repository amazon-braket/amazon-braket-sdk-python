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

import re
import time
from logging import Logger, getLogger
from typing import Any, Dict, List, Optional

from braket.aws.aws_session import AwsSession
from braket.jobs.metrics.cwl_metrics import CwlMetrics
from braket.jobs.metrics.exceptions import MetricsRetrievalError


class CwlInsightsMetricsFetcher(object):

    LOG_GROUP_NAME = "/aws/braket/jobs"
    QUERY_DEFAULT_JOB_DURATION = 3 * 60 * 60

    def __init__(
        self,
        aws_session: AwsSession,
        poll_timeout_seconds: float = 10,
        poll_interval_seconds: float = 1,
        logger: Logger = getLogger(__name__),
    ):
        """
        Args:
            aws_session (AwsSession): AwsSession to connect to AWS with.
            poll_timeout_seconds (float): The polling timeout for retrieving the metrics,
                in seconds. Default: 10 seconds.
            poll_interval_seconds (float): The polling interval for results in seconds.
                Default: 1 second.
            logger (Logger): Logger object with which to write logs, such as task statuses
                while waiting for task to be in a terminal state. Default is `getLogger(__name__)`
        """
        self._poll_timeout_seconds = poll_timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._logger = logger
        self._logs_client = aws_session.create_logs_client()

    @staticmethod
    def _get_element_from_log_line(
        element_name: str, log_line: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Finds and returns an element of a log line from CloudWatch Insights results.

        Args:
            element_name (str): The element to find.
            log_line (List[Dict[str, Any]]): An iterator for RegEx matches on a log line.

        Returns:
            Optional[str] : The value of the element with the element name, or None if no such
            element is found.
        """
        return next(
            (element["value"] for element in log_line if element["field"] == element_name), None
        )

    def _get_metrics_results_sync(self, query_id: str) -> List[Any]:
        """
        Waits for the CloudWatch Insights query to complete and returns all the results.

        Args:
            query_id (str): CloudWatch Insights query ID.

        Returns:
            List[Any]: The results from CloudWatch insights 'GetQueryResults' operation.
        """
        timeout_time = time.time() + self._poll_timeout_seconds
        while time.time() < timeout_time:
            response = self._logs_client.get_query_results(queryId=query_id)
            query_status = response["status"]
            if query_status in ["Failed", "Cancelled"]:
                raise MetricsRetrievalError(f"Query {query_id} failed with status {query_status}")
            elif query_status == "Complete":
                return response["results"]
            else:
                time.sleep(self._poll_interval_seconds)
        self._logger.warning(f"Timed out waiting for query {query_id}.")
        return []

    def _parse_log_line(self, result_entry: List[Dict[str, Any]], metrics: CwlMetrics) -> None:
        """
        Parses the single entry from CloudWatch Insights results and adds any metrics it finds
        to 'all_metrics', along with the timestamp for the entry.

        Args:
            result_entry (List[Dict[str, Any]]): A structured result from calling CloudWatch
                Insights to get logs that contain metrics. A single entry will contain the message
                (the actual line logged to output), the timestamp (generated by CloudWatch Logs),
                and other metadata that we (currently) do not use.
            all_metrics (Dict[int, Dict[str, List[Any]]]) : The list of all metrics.
        """
        message = self._get_element_from_log_line("@message", result_entry)
        if message:
            timestamp = self._get_element_from_log_line("@timestamp", result_entry)
            metrics.add_metrics_from_log_message(timestamp, message)

    def _parse_log_query_results(self, results: List[Any]) -> Dict[int, Dict[str, List[Any]]]:
        """
        Parses CloudWatch Insights results and returns all found metrics.

        Args:
            results (List[Any]): A structured result from calling CloudWatch Insights to get
                logs that contain metrics.

        Returns:
            Dict[int, Dict[str, List[Any]]] : The list of all metrics that can be found in the
                CloudWatch Logs results. Each unique set of metrics will be represented by a key
                in the topmost dictionary. We can think of this set of metrics as a single table.
                Each table will have a set of metrics, indexed by the column name. The
                entries are not sorted.
        """
        metrics = CwlMetrics()
        for result in results:
            self._parse_log_line(result, metrics)
        return metrics.get_metric_data_as_list()

    def get_all_metrics_for_job(
        self, job_name: str, job_start_time: int = None, job_end_time: int = None
    ) -> List[Dict[str, List[Any]]]:
        """
        Synchronously retrieves all the algorithm metrics logged by a given Job.

        Args:
            job_name (str): The name of the Job. The name must be exact to ensure only the relevant
                metrics are retrieved.
            job_start_time (int): The time at which the job started.
                Default: 3 hours before job_end_time.
            job_end_time (int): If the job is complete, this should be the time at which the
                job finished. Default: current time.

        Returns:
            List[Dict[str, List[Any]]] : The list of all metrics that can be found in the
                CloudWatch Logs results. Each item in the list can be thought of as a separate
                table. Each table will have a set of metrics, indexed by the column name. The
                entries are not sorted.
        """
        query_end_time = job_end_time or int(time.time())
        query_start_time = job_start_time or query_end_time - self.QUERY_DEFAULT_JOB_DURATION

        # job name needs to be specific to prevent jobs with similar names from being conflated
        query = (
            f"fields @timestamp, @message "
            f"| filter @logStream like /^{re.escape(job_name)}$/ "
            f"| filter @message like /^Metrics - /"
        )

        response = self._logs_client.start_query(
            logGroupName=self.LOG_GROUP_NAME,
            startTime=query_start_time,
            endTime=query_end_time,
            queryString=query,
            limit=10000,
        )

        query_id = response["queryId"]

        results = self._get_metrics_results_sync(query_id)

        return self._parse_log_query_results(results)
