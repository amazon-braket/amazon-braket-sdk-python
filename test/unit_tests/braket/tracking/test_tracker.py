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

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest

from braket.tracking.tracker import Tracker
from braket.tracking.tracking_context import active_trackers
from braket.tracking.tracking_events import (
    _TaskCompletionEvent,
    _TaskCreationEvent,
    _TaskStatusEvent,
)


@pytest.fixture()
def empty_tracker():
    with Tracker() as _tracker:
        yield _tracker


def test_tracker_enter_exit():
    x = len(active_trackers())
    with Tracker() as t:
        assert len(active_trackers()) == 1 + x
        with Tracker() as s:
            assert len(active_trackers()) == 2 + x
            assert s in active_trackers()
            assert t in active_trackers()
    assert len(active_trackers()) == x


def test_tracker_start_stop():
    t = Tracker()
    assert t not in active_trackers()
    t.start()
    assert t in active_trackers()
    t.stop()
    assert t not in active_trackers()


def test_receive_fake_event(empty_tracker):
    event = "NOT AN EVENT"
    with pytest.raises(ValueError):
        empty_tracker.receive_event(event)


CREATE_EVENTS = [
    _TaskCreationEvent(arn="task1:::region", shots=100, is_job_task=True, device="qpu/foo"),
    _TaskCreationEvent(arn="task2:::region", shots=100, is_job_task=False, device="qpu/foo"),
    _TaskCreationEvent(
        arn="job_sim_task:::region", shots=0, is_job_task=True, device="simulator/bar"
    ),
    _TaskCreationEvent(
        arn="notjob_sim_task:::region", shots=0, is_job_task=False, device="simulator/bar"
    ),
    _TaskCreationEvent(
        arn="task_fail:::region", shots=0, is_job_task=False, device="simulator/tn1"
    ),
    _TaskCreationEvent(
        arn="task_cancel:::region", shots=0, is_job_task=False, device="simulator/baz"
    ),
    _TaskCreationEvent(
        arn="2000qtask:::region", shots=100, is_job_task=False, device="qpu/2000Qxyz"
    ),
    _TaskCreationEvent(
        arn="adv_task:::region", shots=100, is_job_task=False, device="qpu/Advantage_system123"
    ),
    _TaskCreationEvent(
        arn="unfinished_sim_task:::region", shots=1000, is_job_task=False, device="simulator/bar"
    ),
    _TaskCreationEvent(
        arn="no_price:::region", shots=1000, is_job_task=False, device="something_else"
    ),
    _TaskCreationEvent(
        arn="unbilled_task0:::region",
        shots=100,
        is_job_task=True,
        device="qpu/foo",
    ),
    _TaskCreationEvent(
        arn="unbilled_task1:::region",
        shots=100,
        is_job_task=True,
        device="qpu/foo",
    ),
]

GET_EVENTS = [
    _TaskStatusEvent(arn="untracked_task:::region", status="FOO"),
    _TaskStatusEvent(arn="task1:::region", status="BAR"),
    _TaskStatusEvent(arn="task2:::region", status="FAILED"),
]
COMPLETE_EVENTS = [
    _TaskCompletionEvent(arn="untracked_task:::region", execution_duration=999999, status="BAR"),
    _TaskCompletionEvent(arn="task1:::region", execution_duration=None, status="COMPLETED"),
    _TaskCompletionEvent(arn="job_sim_task:::region", execution_duration=123, status="COMPLETED"),
    _TaskCompletionEvent(
        arn="notjob_sim_task:::region", execution_duration=1729, status="COMPLETED"
    ),
    _TaskCompletionEvent(arn="task_fail:::region", execution_duration=12345, status="FAILED"),
    _TaskCompletionEvent(arn="task_cancel:::region", execution_duration=None, status="CANCELLED"),
    _TaskCompletionEvent(
        arn="unbilled_task0:::region",
        execution_duration=123,
        status="COMPLETED",
        has_reservation_arn=True,
    ),
    _TaskCompletionEvent(
        arn="unbilled_task1:::region",
        execution_duration=123,
        status="COMPLETED",
        has_reservation_arn=True,
    ),
]


@pytest.fixture
def create_tracker(empty_tracker):
    for e in CREATE_EVENTS:
        empty_tracker.receive_event(e)
    return empty_tracker


@pytest.fixture
def get_tracker(create_tracker):
    for e in GET_EVENTS:
        create_tracker.receive_event(e)
    return create_tracker


@pytest.fixture
def completed_tracker(get_tracker):
    for e in COMPLETE_EVENTS:
        get_tracker.receive_event(e)
    return get_tracker


def test_tracked_resources(create_tracker):
    assert len(CREATE_EVENTS) == len(create_tracker.tracked_resources())


def mock_qpu_price(**kwargs):
    if "Shot" in kwargs["Product Family"]:
        return [{"PricePerUnit": "0.001", "Currency": "USD"}]
    else:
        return [{"PricePerUnit": "1.0", "Currency": "USD"}]


@patch("braket.tracking.tracker.price_search")
def test_qpu_task_cost(price_mock, completed_tracker):
    price_mock.side_effect = mock_qpu_price
    cost = completed_tracker.qpu_tasks_cost()
    assert cost == Decimal("3.3")

    price_mock.side_effect = [[]]
    with pytest.raises(ValueError, match="Found 0 products"):
        completed_tracker.qpu_tasks_cost()

    price_mock.side_effect = [[{}], [{}, {}]]
    with pytest.raises(ValueError, match="Found 2 products"):
        completed_tracker.qpu_tasks_cost()

    price_mock.side_effect = [[{"Currency": "BAD"}], [{"Currency": "BAD"}]]
    with pytest.raises(ValueError, match="Expected USD"):
        completed_tracker.qpu_tasks_cost()


@patch("braket.tracking.tracker.price_search")
def test_simulator_task_cost(price_mock, completed_tracker):
    price_mock.return_value = [{"PricePerUnit": "6.0", "Currency": "USD", "Unit": "minutes"}]
    cost = completed_tracker.simulator_tasks_cost()
    expected = Decimal("0.0001") * (3000 + 3000 + 12345)
    assert cost == expected

    price_mock.return_value = []
    with pytest.raises(ValueError, match="Found 0 products"):
        completed_tracker.simulator_tasks_cost()

    price_mock.return_value = [{"Currency": "BAD"}]
    with pytest.raises(ValueError, match="Expected USD"):
        completed_tracker.simulator_tasks_cost()


def test_quantum_task_statistics(completed_tracker):
    stats = completed_tracker.quantum_tasks_statistics()
    expected = {
        "qpu/foo": {
            "shots": 400,
            "tasks": {"COMPLETED": 3, "FAILED": 1},
            "execution_duration": timedelta(microseconds=246000),
            "billed_execution_duration": timedelta(0),
        },
        "simulator/bar": {
            "shots": 1000,
            "tasks": {"COMPLETED": 2, "CREATED": 1},
            "execution_duration": timedelta(seconds=1, microseconds=852000),
            "billed_execution_duration": timedelta(seconds=6),
        },
        "simulator/tn1": {
            "shots": 0,
            "tasks": {"FAILED": 1},
            "execution_duration": timedelta(seconds=12, microseconds=345000),
            "billed_execution_duration": timedelta(seconds=12, microseconds=345000),
        },
        "simulator/baz": {"shots": 0, "tasks": {"CANCELLED": 1}},
        "qpu/2000Qxyz": {"shots": 100, "tasks": {"CREATED": 1}},
        "qpu/Advantage_system123": {"shots": 100, "tasks": {"CREATED": 1}},
        "something_else": {"shots": 1000, "tasks": {"CREATED": 1}},
    }
    assert stats == expected
