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

import pytest

from braket.jobs.metrics import CwlMetrics

MALFORMED_METRICS_LOG_LINES = [
    {"timestamp": "Test timestamp 0", "message": ""},
    {"timestamp": "Test timestamp 1", "message": "No metrics prefix metric0=2.0"},
    {"timestamp": "Test timestamp 2", "message": "Metrics - metric0=not_a_number;"},
    {"timestamp": "Test timestamp 3"},
    {"unknown": "Unknown"},
]


SIMPLE_METRICS_LOG_LINES = [
    {
        "timestamp": "Test timestamp 0",
        "message": "Metrics - metric0=0.0; metric1=1.0; metric2=2.0;",
    },
    {
        "timestamp": "Test timestamp 1",
        "message": "Metrics - metric0=0.1; metric1=1.1; metric2=2.1;",
    },
    {
        "timestamp": "Test timestamp 2",
        "message": "Metrics - metric0=0.2; metric1=1.2; metric2=2.2;",
    },
    {
        "timestamp": "Test timestamp 3",
        "message": "Metrics - metric0=-0.4; metric1=3.14e-22; metric2=3.14E22;",
    },
]

SIMPLE_METRICS_RESULT = [
    {
        "Timestamp": [
            "Test timestamp 0",
            "Test timestamp 1",
            "Test timestamp 2",
            "Test timestamp 3",
        ],
        "metric0": [0.0, 0.1, 0.2, -0.4],
        "metric1": [1.0, 1.1, 1.2, 3.14e-22],
        "metric2": [2.0, 2.1, 2.2, 3.14e22],
    }
]

MULTIPLE_TABLES_METRICS_LOG_LINES = [
    {"timestamp": "Test timestamp 0", "message": "Metrics - metric0=0.0;"},
    {"timestamp": "Test timestamp 1", "message": "Metrics - metric0=0.1; metric1=1.1;"},
    {"timestamp": "Test timestamp 2", "message": "Metrics - metric0=0.2; metric2=2.2;"},
    {"timestamp": "Test timestamp 3", "message": "Metrics - metric0=0.3; metric1=1.3;"},
    {"timestamp": "Test timestamp 4", "message": "Metrics - metric1=1.4; metric2=2.4;"},
    {
        "timestamp": "Test timestamp 5",
        "message": "Metrics - metric0=0.5; metric1=1.5; metric2=2.5;",
    },
    {"timestamp": "Test timestamp 6", "message": "Metrics - metric1=0.6; metric0=0.6;"},
    {"message": "Metrics - metric0=0.7; "},
]

MULTIPLE_TABLES_METRICS_RESULT = [
    {"Timestamp": ["Test timestamp 0", "N/A"], "metric0": [0.0, 0.7]},
    {
        "Timestamp": ["Test timestamp 1", "Test timestamp 3", "Test timestamp 6"],
        "metric0": [0.1, 0.3, 0.6],
        "metric1": [1.1, 1.3, 0.6],
    },
    {"Timestamp": ["Test timestamp 2"], "metric0": [0.2], "metric2": [2.2]},
    {"Timestamp": ["Test timestamp 4"], "metric1": [1.4], "metric2": [2.4]},
    {"Timestamp": ["Test timestamp 5"], "metric0": [0.5], "metric1": [1.5], "metric2": [2.5]},
]


@pytest.mark.parametrize(
    "log_events, metrics_results",
    [
        ([], []),
        (MALFORMED_METRICS_LOG_LINES, []),
        (SIMPLE_METRICS_LOG_LINES, SIMPLE_METRICS_RESULT),
        (MULTIPLE_TABLES_METRICS_LOG_LINES, MULTIPLE_TABLES_METRICS_RESULT),
        # TODO: https://app.asana.com/0/1199668788990775/1200502190825620
        #  We should also test some real-world data, once we have it.
    ],
)
def test_get_all_metrics_complete_results(log_events, metrics_results):
    metrics = CwlMetrics()
    for log_event in log_events:
        metrics.add_metrics_from_log_message(log_event.get("timestamp"), log_event.get("message"))
    assert metrics.get_metric_data_as_list() == metrics_results
