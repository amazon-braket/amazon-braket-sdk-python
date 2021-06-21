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

from unittest.mock import Mock

import pytest

from braket.jobs.metrics import CwlInsightsMetricsFetcher, MetricsTimeoutError


@pytest.fixture
def aws_session():
    _aws_session = Mock()
    return _aws_session


MALFORMED_METRICS_LOG_LINES = [
    [
        {"field": "@timestamp", "value": "Test timestamp 0"},
        {"field": "@message", "value": ""},
    ],
    [
        {"field": "@timestamp", "value": "Test timestamp 1"},
        {"field": "@message", "value": "Test Test"},
    ],
    [
        {"field": "@timestamp", "value": "Test timestamp 2"},
        {"field": "@message", "value": "metric0=not_a_number;"},
    ],
    [{"field": "@timestamp", "value": "Test timestamp 0"}],
    [
        {"field": "@unknown", "value": "Unknown"},
    ],
]


SIMPLE_METRICS_LOG_LINES = [
    [
        {"field": "@timestamp", "value": "Test timestamp 0"},
        {"field": "@message", "value": "metric0=0.0; metric1=1.0; metric2=2.0"},
    ],
    [
        {"field": "@timestamp", "value": "Test timestamp 1"},
        {"field": "@message", "value": "metric0=0.1; metric1=1.1; metric2=2.1"},
    ],
    [
        {"field": "@timestamp", "value": "Test timestamp 2"},
        {"field": "@message", "value": "metric0=0.2; metric1=1.2; metric2=2.2"},
    ],
]

SIMPLE_METRICS_RESULT = [
    {
        "Timestamp": ["Test timestamp 0", "Test timestamp 1", "Test timestamp 2"],
        "metric0": ["0.0", "0.1", "0.2"],
        "metric1": ["1.0", "1.1", "1.2"],
    }
]


MULTIPLE_TABLES_METRICS_LOG_LINES = [
    [
        {"field": "@timestamp", "value": "Test timestamp 0"},
        {"field": "@message", "value": "metric0=0.0;"},
    ],
    [
        {"field": "@timestamp", "value": "Test timestamp 1"},
        {"field": "@message", "value": "metric0=0.1; metric1=1.1;"},
    ],
    [
        {"field": "@timestamp", "value": "Test timestamp 2"},
        {"field": "@message", "value": "metric0=0.2; metric2=2.2;"},
    ],
    [
        {"field": "@timestamp", "value": "Test timestamp 3"},
        {"field": "@message", "value": "metric0=0.3; metric1=1.3;"},
    ],
    [
        {"field": "@timestamp", "value": "Test timestamp 4"},
        {"field": "@message", "value": "metric1=1.4; metric2=2.4;"},
    ],
    [
        {"field": "@timestamp", "value": "Test timestamp 5"},
        {"field": "@message", "value": "metric0=0.5; metric1=1.5; metric2=2.5;"},
    ],
    [
        {"field": "@timestamp", "value": "Test timestamp 6"},
        {"field": "@message", "value": "metric1=0.6; metric0=0.6;"},
    ],
    [
        {"field": "@message", "value": "metric0=0.7; "},
    ],
]


MULTIPLE_TABLES_METRICS_RESULT = [
    {"Timestamp": ["Test timestamp 0", "N/A"], "metric0": ["0.0", "0.7"]},
    {
        "Timestamp": ["Test timestamp 1", "Test timestamp 3", "Test timestamp 6"],
        "metric0": ["0.1", "0.3", "0.6"],
        "metric1": ["1.1", "1.3", "0.6"],
    },
    {"Timestamp": ["Test timestamp 2"], "metric0": ["0.2"], "metric2": ["2.2"]},
    {"Timestamp": ["Test timestamp 4"], "metric1": ["1.4"], "metric2": ["2.4"]},
    {"Timestamp": ["Test timestamp 5"], "metric0": ["0.5"], "metric1": ["1.5"], "metric2": ["2.5"]},
]


@pytest.mark.parametrize(
    "log_insights_results, metrics_results",
    [
        ([], []),
        (MALFORMED_METRICS_LOG_LINES, []),
        (SIMPLE_METRICS_LOG_LINES, SIMPLE_METRICS_RESULT),
        (MULTIPLE_TABLES_METRICS_LOG_LINES, MULTIPLE_TABLES_METRICS_RESULT),
        # TODO: https://app.asana.com/0/1199668788990775/1200502190825620
        #  We should also test some real-world data, once we have it.
    ],
)
def test_get_all_metrics_complete_results(aws_session, log_insights_results, metrics_results):
    logs_client_mock = Mock()
    aws_session.create_logs_client.return_value = logs_client_mock

    logs_client_mock.start_query.return_value = {"queryId": "test"}
    logs_client_mock.get_query_results.return_value = {
        "status": "Complete",
        "results": log_insights_results,
    }

    fetcher = CwlInsightsMetricsFetcher(aws_session)
    result = fetcher.get_all_metrics_for_job("test_job")
    assert result == metrics_results


def test_get_all_metrics_timeout(aws_session):
    logs_client_mock = Mock()
    aws_session.create_logs_client.return_value = logs_client_mock

    logs_client_mock.start_query.return_value = {"queryId": "test"}
    logs_client_mock.get_query_results.return_value = {"status": "Queued"}

    fetcher = CwlInsightsMetricsFetcher(aws_session, 0.25, 0.5)
    result = fetcher.get_all_metrics_for_job("test_job")
    assert result == []


@pytest.mark.xfail(raises=MetricsTimeoutError)
def test_get_all_metrics_failed(aws_session):
    logs_client_mock = Mock()
    aws_session.create_logs_client.return_value = logs_client_mock

    logs_client_mock.start_query.return_value = {"queryId": "test"}
    logs_client_mock.get_query_results.return_value = {"status": "Failed"}

    fetcher = CwlInsightsMetricsFetcher(aws_session)
    fetcher.get_all_metrics_for_job("test_job")
