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

import time
from logging import Logger, getLogger
from typing import Any, Dict, List

from braket.aws.aws_session import AwsSession
from braket.jobs.metrics.cwl_metrics import CwlMetrics


class CwlMetricsFetcher(object):

    LOG_GROUP_NAME = "/aws/braket/jobs"

    def __init__(
        self,
        aws_session: AwsSession,
        poll_timeout_seconds: float = 10,
        logger: Logger = getLogger(__name__),
    ):
        """
        Args:
            aws_session (AwsSession): AwsSession to connect to AWS with.
            poll_timeout_seconds (float): The polling timeout for retrieving the metrics,
                in seconds. Default: 10 seconds.
            logger (Logger): Logger object with which to write logs, such as task statuses
                while waiting for task to be in a terminal state. Default is `getLogger(__name__)`
        """
        self._poll_timeout_seconds = poll_timeout_seconds
        self._logger = logger
        self._logs_client = aws_session.create_logs_client()

    @staticmethod
    def _is_metrics_message(message):
        """
        Returns true if a given message is designated as containing Metrics.

        Args:
            message (str): The message to check.

        Returns:
            True if the given message is designated as containing Metrics, False otherwise.
        """
        if message:
            return "Metrics -" in message
        return False

    def _get_metrics_from_log_stream(
        self,
        stream_name: str,
        timeout_time: float,
        metrics: CwlMetrics,
    ) -> None:
        """
        Synchronously retrieves the algorithm metrics logged in a given job log stream.

        Args:
            stream_name (str): The name of the log stream.
            timeout_time (float) : We stop getting metrics if the current time is beyond
                the timeout time.
            metrics (CwlMetrics) : The metrics object to add the metrics to.

        Returns:
            None
        """
        kwargs = {
            "logGroupName": self.LOG_GROUP_NAME,
            "logStreamName": stream_name,
            "startFromHead": True,
            "limit": 10000,
        }

        previous_token = None
        while time.time() < timeout_time:
            response = self._logs_client.get_log_events(**kwargs)
            for event in response.get("events"):
                message = event.get("message")
                if self._is_metrics_message(message):
                    metrics.add_metrics_from_log_message(event.get("timestamp"), message)
            next_token = response.get("nextForwardToken")
            if not next_token or next_token == previous_token:
                return
            previous_token = next_token
            kwargs["nextToken"] = next_token
        self._logger.warning("Timed out waiting for all metrics. Data may be incomplete.")

    def _get_log_streams_for_job(self, job_name: str, timeout_time: float) -> List[str]:
        """
        Retrieves the list of log streams relevant to a job.

        Args:
            job_name (str): The name of the job.
            timeout_time (float) : We stop getting metrics if the current time is beyond
                the timeout time.
        Returns:
            List[str] : a list of log stream names for the given job.
        """
        kwargs = {
            "logGroupName": self.LOG_GROUP_NAME,
            "logStreamNamePrefix": job_name + "/algo-",
        }
        log_streams = []
        while time.time() < timeout_time:
            response = self._logs_client.describe_log_streams(**kwargs)
            streams = response.get("logStreams")
            if streams:
                for stream in streams:
                    name = stream.get("logStreamName")
                    if name:
                        log_streams.append(name)
            next_token = response.get("nextToken")
            if not next_token:
                return log_streams
            kwargs["nextToken"] = next_token
        self._logger.warning("Timed out waiting for all metrics. Data may be incomplete.")
        return log_streams

    def get_all_metrics_for_job(self, job_name: str) -> List[Dict[str, List[Any]]]:
        """
        Synchronously retrieves all the algorithm metrics logged by a given Job.

        Args:
            job_name (str): The name of the Job. The name must be exact to ensure only the relevant
                metrics are retrieved.

        Returns:
            List[Dict[str, List[Any]]] : The list of all metrics that can be found in the
                CloudWatch Logs results. Each item in the list can be thought of as a separate
                table. Each table will have a set of metrics, indexed by the column name.
        """
        timeout_time = time.time() + self._poll_timeout_seconds

        metrics = CwlMetrics()

        log_streams = self._get_log_streams_for_job(job_name, timeout_time)
        for log_stream in log_streams:
            self._get_metrics_from_log_stream(log_stream, timeout_time, metrics)

        return metrics.get_metric_data_as_list()
