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
from collections import defaultdict
from logging import Logger, getLogger
from typing import Dict, FrozenSet, Iterator


class CwlMetrics(object):

    METRICS_DEFINITIONS = re.compile(r"(\w+)\s*=\s*([^;]+)\s*;")
    TIMESTAMP = "Timestamp"

    def __init__(
        self,
        logger: Logger = getLogger(__name__),
    ):
        self._logger = logger
        self.metric_tables = defaultdict(lambda: defaultdict(list))

    def _add_metrics_to_appropriate_table(
        self,
        columns: FrozenSet[str],
        metrics: Dict[str, float],
    ) -> None:
        """
        Adds the given metrics to the appropriate table.

        Args:
            columns (FrozenSet[str]): The set of column names representing the metrics.
            metrics (Dict[str, float]): A set of metrics in the format {<metric name> : <value>}.
        """
        metrics_table = self.metric_tables[columns]
        for column_name in metrics.keys():
            metrics_table[column_name].append(metrics[column_name])

    def _get_metrics_from_log_line_matches(self, all_matches: Iterator) -> Dict[str, float]:
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
            value = subgroup[1]
            try:
                metrics[subgroup[0]] = float(value)
            except ValueError:
                self._logger.warning(f"Unable to convert value {value} to a float.")
        return metrics

    def add_metrics_from_log_message(self, timestamp: str, message: str) -> None:
        """
        Parses a line from CloudWatch Logs adds all the metrics that have been logged
        on that line. The timestamp is also added to match the corresponding values.

        Args:
            timestamp (str): A formatted string representing the timestamp for any found metrics.
            message (str): A log line from CloudWatch Logs.
        """
        if not message:
            return
        all_matches = self.METRICS_DEFINITIONS.finditer(message)
        parsed_metrics = self._get_metrics_from_log_line_matches(all_matches)
        if not parsed_metrics:
            return
        columns = frozenset(parsed_metrics.keys())
        self._add_metrics_to_appropriate_table(columns, parsed_metrics)
        self.metric_tables[columns][self.TIMESTAMP].append(timestamp or "N/A")

    def get_metric_data_as_list(self):
        """
        Gets all the metrics data for all tables, as a list.

        Returns:
            List[Dict[str, List[Any]]] : The list of all tables. Each table will have a set
            of metrics, indexed by the column name.
        """
        return list(self.metric_tables.values())
