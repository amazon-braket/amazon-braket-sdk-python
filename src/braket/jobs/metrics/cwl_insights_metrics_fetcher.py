# Copyright 2021-2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from typing import Any, Dict, Iterator, List, Optional

from braket.aws.aws_session import AwsSession


class CwlInsightsMetricsFetcher(object):

    LOG_GROUP_NAME = "/aws/lambda/my-python-test-function"
    METRICS_DEFINITIONS = re.compile(r"(\w+)\s*=\s*(\d*\.?\d*)\s*;")
    TIMESTAMP = "Timestamp"
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

    def _get_metrics_results_sync(self, query_id: str) -> List[Any]:
        """
        Waits for the CloudWatch Insights query to complete and returns all the results.

        Args:
            query_id (str): CloudWatch Insights query ID.

        Returns:
            List[Any]: The results from CloudWatch insights 'GetQueryResults' operation.
        """
        start_time = time.time()
        while (time.time() - start_time) < self._poll_timeout_seconds:
            response = self._logs_client.get_query_results(queryId=query_id)
            query_status = response["status"]
            if query_status in ["Failed", "Cancelled"]:
                raise Exception(f"Query {query_id} failed with status {query_status}")
            elif query_status == "Complete":
                return response["results"]
            else:
                time.sleep(self._poll_interval_seconds)
        self._logger.warning(f"Timed out waiting for query {query_id}.")
        return []

    @staticmethod
    def _metrics_id_from_metrics(metrics: Dict[str, float]) -> int:
        """
        Determines the semi-unique ID for a set of metrics that will represent the table for that
        set of columns. The current implementation doesn't treat a difference in order as unique;
        therefore, the same metrics output in various different orders will map to the same table.

        Args:
            metrics (Dict[str, float]): The set of metrics.

        Returns:
            int : The Metrics ID.
        """
        metrics_id = 0
        for column_name in metrics.keys():
            metrics_id += hash(column_name)
        return metrics_id

    @staticmethod
    def _get_metrics_from_log_line_matches(all_matches: Iterator) -> Dict[str, float]:
        """
        Converts matches from a RegEx to a set of metrics.

        Args:
            all_matches (Iterator): An iterator for RegEx matches on a log line.

        Returns:
            Dict[str, float]: The set of metrics found by the RegEx. The result will be in the
            format {<metric name> : <value>}. This implies that multiple metrics with
            the same name will be deduped to the last instance of that metric.
        """
        metrics = {}
        for match in all_matches:
            subgroup = match.groups()
            metrics[subgroup[0]] = subgroup[1]
        return metrics

    @staticmethod
    def _get_timestamp_from_log_line(log_line: List[Dict[str, Any]]) -> str:
        """
        Finds and returns the timestamp of a log line from CloudWatch Insights results.

        Args:
            log_line (List[Dict[str, Any]]): An iterator for RegEx matches on a log line.

        Returns:
            str : The timestamp of the log line or 'N/A' if no timestamp is found.
        """
        for element in log_line:
            if element["field"] == "@timestamp":
                return element["value"]
        return "N/A"

    def _add_metrics(
        self,
        metrics_id: int,
        metrics: Dict[str, float],
        all_metrics: Dict[int, Dict[str, List[Any]]],
    ) -> None:
        """
        Adds the given metrics to the appropriate table in 'all_metrics'. If 'all_metrics' does not
        currently have a table that represents the metrics, a new entry will be created to
        represent the data. When the table entry is created, a "Timestamp" field is also added by
        default, since all log metrics should have a timestamp.

        Args:
            metrics_id (int): An ID to represent the given set of metrics.
            metrics (Dict[str, float]): A set of metrics in the format {<metric name> : <value>}.
            all_metrics (Dict[int, Dict[str, List[Any]]]) : The list of all metrics.
        """
        if metrics_id not in all_metrics:
            metrics_table = {}
            for column_name in metrics.keys():
                metrics_table[column_name] = []
            metrics_table[self.TIMESTAMP] = []
            all_metrics[metrics_id] = metrics_table
        metrics_table = all_metrics[metrics_id]
        for column_name in metrics.keys():
            metrics_table[column_name].append(metrics[column_name])

    def _parse_metrics_from_message(
        self, message: str, all_metrics: Dict[int, Dict[str, List[Any]]]
    ) -> Optional[int]:
        """
        Parses a line from CloudWatch Logs to find all the metrics that have been logged
        on that line. Any found metrics will be added to 'all_metrics'.

        Args:
            message (str): A log line from CloudWatch Logs.
            all_metrics (Dict[int, Dict[str, List[Any]]]) : The list of all metrics.

        Returns:
            int : The ID to represent the given set of logged metrics, or None if no metrics
                are found in the message.
        """
        all_matches = self.METRICS_DEFINITIONS.finditer(message)
        metrics = self._get_metrics_from_log_line_matches(all_matches)
        if not metrics:
            return None
        metrics_id = self._metrics_id_from_metrics(metrics)
        self._add_metrics(metrics_id, metrics, all_metrics)
        return metrics_id

    def _parse_metrics_from_result_entry(
        self, result_entry: List[Any], timestamp: str, all_metrics: Dict[int, Dict[str, List[Any]]]
    ) -> None:
        """
        Finds the actual log line containing metrics from a given CloudWatch Insights result entry,
        and adds them to 'all_metrics'. The timestamp is added to match the corresponding values in
        'all_metrics'.

        Args:
            result_entry (List[Any]): A structured result from calling CloudWatch Insights to get
                logs that contain metrics. A single entry will contain the message
                (the actual line logged to output), the timestamp (generated by CloudWatch Logs),
                and other metadata that we (currently) do not use.
            timestamp (str): A formatted string representing the timestamp for any found metrics.
            all_metrics (Dict[int, Dict[str, List[Any]]]) : The list of all metrics.
        """
        for element in result_entry:
            if element["field"] == "@message":
                metrics_id = self._parse_metrics_from_message(element["value"], all_metrics)
                if metrics_id is not None:
                    all_metrics[metrics_id][self.TIMESTAMP].append(timestamp)
                break

    def _parse_log_line(
        self, result_entry: List[Any], all_metrics: Dict[int, Dict[str, List[Any]]]
    ) -> None:
        """
        Parses the single entry from CloudWatch Insights results and adds any metrics it finds
        to 'all_metrics', along with the timestamp for the entry.

        Args:
            result_entry (List[Any]): A structured result from calling CloudWatch Insights to get
                logs that contain metrics. A single entry will contain the message
                (the actual line logged to output), the timestamp (generated by CloudWatch Logs),
                and other metadata that we (currently) do not use.
            all_metrics (Dict[int, Dict[str, List[Any]]]) : The list of all metrics.
        """
        timestamp = self._get_timestamp_from_log_line(result_entry)
        self._parse_metrics_from_result_entry(result_entry, timestamp, all_metrics)

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
        all_metrics = {}
        for result in results:
            self._parse_log_line(result, all_metrics)
        return all_metrics

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
        )

        query_id = response["queryId"]

        results = self._get_metrics_results_sync(query_id)

        metric_data = self._parse_log_query_results(results)

        metric_data_list = []
        for metric_graph in metric_data.keys():
            metric_data_list.append(metric_data[metric_graph])

        return metric_data_list
