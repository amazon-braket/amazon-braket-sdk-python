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

# from functools import singledispatch

from __future__ import annotations

from functools import singledispatchmethod

from braket.tracking.tracking_context import deregister_tracker, register_tracker
from braket.tracking.tracking_events import _TaskCompletionEvent, _TaskCreationEvent, _TaskGetEvent

MIN_SIMULATOR_DURATION = 3000


class Tracker:
    def __init__(self):
        self._resources = {}  # Key = quantum_task_arn

    def __enter__(self):
        register_tracker(self)
        return self

    def __exit__(self, *args):
        deregister_tracker(self)

    def start(self):
        return self.__enter__()

    def stop(self):
        return self.__exit__()

    @singledispatchmethod
    def receive_event(self, event):
        raise ValueError(f"Event type {type(event)} is not supported")

    @receive_event.register
    def _receive_task_creation_event(self, event: _TaskCreationEvent):
        self._resources[event.arn] = {
            "shots": event.shots,
            "device": event.device,
            "status": "CREATED",
        }

    @receive_event.register
    def _receive_task_get_event(self, event: _TaskGetEvent):
        # Update task data corresponding to the arn only if it exists in self._resources
        if event.arn in self._resources:
            self._resources[event.arn]["status"] = event.status

    @receive_event.register
    def _receive_task_completion_event(self, event: _TaskCompletionEvent):
        # Update task completion data corresponding to the arn only if it exists in self._resources
        if event.arn in self._resources:
            self._resources[event.arn]["status"] = event.status
            if event.execution_duration:
                self._resources[event.arn]["execution_duration"] = event.execution_duration

    # Not making this a property so that it can be extended
    # to include filters if needed.
    def tracked_resources(self):
        return list(self._resources.keys())

    def qpu_tasks_cost(self) -> float:
        # Filter qpu tasks and return sum of all costs.
        # TODO
        return 0

    def simulator_tasks_cost(self) -> float:
        # Filter simulator tasks and return sum of all costs.
        # TODO
        return 0

    def quantum_tasks_statistics(self):
        stats = {}
        for _, details in self._resources.items():

            device_stats = {}

            shots = device_stats.get("shots", 0) + details["shots"]
            device_stats["shots"] = shots

            task_states = device_stats.get("tasks", {})
            task_states[details["status"]] = task_states.get(details["status"], 0) + 1
            device_stats["tasks"] = task_states

            if "execution_duration" in details:
                duration = device_stats.get("execution_duration", 0) + details["execution_duration"]
                billed_duration = device_stats.get("billed_execution_duration", 0) + max(
                    details["execution_duration"], MIN_SIMULATOR_DURATION
                )

                device_stats["execution_duration"] = duration
                device_stats["billed_execution_duration"] = billed_duration

            stats.setdefault(details["device"], {}).update(device_stats)

        return stats
