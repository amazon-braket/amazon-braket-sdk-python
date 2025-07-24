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

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from functools import singledispatchmethod
from typing import Any

from braket.tracking.pricing import price_search
from braket.tracking.tracking_context import deregister_tracker, register_tracker
from braket.tracking.tracking_events import (
    _TaskCompletionEvent,
    _TaskCreationEvent,
    _TaskStatusEvent,
)

MIN_SIMULATOR_DURATION = timedelta(milliseconds=3000)


class Tracker:
    """Amazon Braket cost tracker.
    Use this class to track costs incurred from quantum tasks on Amazon Braket.
    """

    def __init__(self):
        self._resources = {}  # Key = quantum_task_arn

    def __enter__(self):
        register_tracker(self)
        return self

    def __exit__(self, *args):
        deregister_tracker(self)

    def start(self) -> Tracker:
        """Start tracking resources with this tracker.

        Returns:
            Tracker: self.
        """
        return self.__enter__()  # noqa: PLC2801

    def stop(self) -> Tracker:
        """Stop tracking resources with this tracker.

        Returns:
            Tracker: self.
        """
        return self.__exit__()

    def receive_event(self, event: _TaskCreationEvent) -> None:
        """Process a Tack Creation Event.

        Args:
            event (_TaskCreationEvent): The event to process.
        """
        self._recieve_internal(event)

    def tracked_resources(self) -> list[str]:
        """Resources tracked by this tracker.

        Returns:
            list[str]: The list of quantum task ids for quantum tasks tracked by this tracker.
        """
        return list(self._resources.keys())

    def qpu_tasks_cost(self) -> Decimal:
        """Estimate cost of all quantum tasks tracked by this tracker that use Braket qpu devices.

        Note: Charges shown are estimates based on your Amazon Braket simulator and quantum
        processing unit (QPU) task usage. Estimated charges shown may differ from your actual
        charges. Estimated charges do not factor in any discounts or credits, and you may
        experience additional charges based on your use of other services such as
        Amazon Elastic Compute Cloud (Amazon EC2).

        Returns:
            Decimal: The estimated total cost in USD
        """
        total_cost = Decimal(0)
        for task_arn, details in self._resources.items():
            if "qpu" in details["device"]:
                total_cost += _get_qpu_task_cost(task_arn, details)
        return total_cost

    def simulator_tasks_cost(self) -> Decimal:
        """Estimate cost of all quantum tasks tracked by this tracker using Braket simulator
         devices.

        Note: The cost of a simulator quantum task is not available until after the results for the
        task have been fetched. Call `result()` on an `AwsQuantumTask` before estimating its cost
        to ensure that the simulator usage is included in the cost estimate.

        Note: Charges shown are estimates based on your Amazon Braket simulator and quantum
        processing unit (QPU) task usage. Estimated charges shown may differ from your actual
        charges. Estimated charges do not factor in any discounts or credits, and you may
        experience additional charges based on your use of other services such as
        Amazon Elastic Compute Cloud (Amazon EC2).

        Returns:
            Decimal: The estimated total cost in USD
        """
        total_cost = Decimal(0)
        for task_arn, details in self._resources.items():
            if "simulator" in details["device"]:
                total_cost += _get_simulator_task_cost(task_arn, details)
        return total_cost

    def quantum_tasks_statistics(self) -> dict[str, dict[str, Any]]:
        """Get a summary of quantum tasks grouped by device.

        Returns:
            dict[str, dict[str, Any]]: A dictionary where each key is a device arn, and maps to
            a dictionary summarizing the quantum tasks run on the device. The summary includes the
            total shots sent to the device and the most recent status of the quantum tasks
            created on this device. For finished quantum tasks on simulator devices, the summary
            also includes the duration of the simulation.

        Example:
            >>> tracker.quantum_tasks_statistics()
            {'qpu_device_foo':
                {'shots' : 1000,
                 'tasks' : { 'COMPLETED' : 4,
                             'QUEUED' : 1 },
                },
             'simulator_device_bar':
                {'shots' : 1000
                 'tasks' : { 'COMPLETED' : 2,
                              'CREATED' : 1},
                 'execution_duration' : datetime.timedelta(seconds=5, microseconds=654321),
                 'billed_execution_duration' : datetime.timedelta(seconds=6, microseconds=123456)}}
        """
        stats = {}
        for details in self._resources.values():
            device_stats = stats.get(details["device"], {})

            shots = device_stats.get("shots", 0) + details["shots"]
            device_stats["shots"] = shots

            task_states = device_stats.get("tasks", {})
            task_states[details["status"]] = task_states.get(details["status"], 0) + 1
            device_stats["tasks"] = task_states

            if "execution_duration" in details:
                duration = (
                    device_stats.get("execution_duration", timedelta(0))
                    + details["execution_duration"]
                )
                billed_duration = (
                    timedelta(0)
                    if details.get("has_reservation_arn")
                    else (
                        device_stats.get("billed_execution_duration", timedelta(0))
                        + details["billed_duration"]
                    )
                )

                device_stats["execution_duration"] = duration
                device_stats["billed_execution_duration"] = billed_duration

            stats.setdefault(details["device"], {}).update(device_stats)

        return stats

    @singledispatchmethod
    def _recieve_internal(self, event: _TaskCreationEvent) -> None:
        raise ValueError(f"Event type {type(event)} is not supported")

    @_recieve_internal.register
    def _(self, event: _TaskCreationEvent) -> None:
        self._resources[event.arn] = {
            "shots": event.shots,
            "device": event.device,
            "status": "CREATED",
            "job_task": event.is_job_task,
        }

    @_recieve_internal.register
    def _(self, event: _TaskStatusEvent) -> None:
        resources = self._resources
        # Update task data corresponding to the arn only if it exists in resources
        if event.arn in resources:
            resources[event.arn]["status"] = event.status

    @_recieve_internal.register
    def _(self, event: _TaskCompletionEvent) -> None:
        resources = self._resources
        # Update task completion data corresponding to the arn only if it exists in resources
        if event.arn in resources:
            resources[event.arn]["status"] = event.status
            has_reservation_arn = event.has_reservation_arn
            resources[event.arn]["has_reservation_arn"] = has_reservation_arn
            if event.execution_duration:
                duration = timedelta(milliseconds=event.execution_duration)
                resources[event.arn]["execution_duration"] = duration
                resources[event.arn]["billed_duration"] = (
                    timedelta(milliseconds=0)
                    if has_reservation_arn
                    else max(duration, MIN_SIMULATOR_DURATION)
                )


def _get_qpu_task_cost(task_arn: str, details: dict) -> Decimal:
    if details["status"] in {"FAILED", "CANCELLED"} or details.get("has_reservation_arn"):
        return Decimal(0)
    task_region = task_arn.split(":")[3]

    search_dict = {"Region Code": task_region}

    device_name = details["device"].split("/")[-1]
    device_name = device_name[0].upper() + device_name[1:]
    if "2000Q" in device_name:
        device_name = "2000Q"
    elif "Advantage_system" in device_name:
        device_name = "Advantage_system"

    if details["job_task"]:
        search_dict["Device Name"] = device_name
        shot_product_family = "Braket Managed Jobs QPU Task Shot"
        task_product_family = "Braket Managed Jobs QPU Task"
    else:
        search_dict["DeviceName"] = device_name  # The difference in spelling is intentional
        shot_product_family = "Quantum Task-Shot"
        task_product_family = "Quantum Task"

    search_dict["Product Family"] = shot_product_family
    shot_prices = price_search(**search_dict)
    if len(shot_prices) != 1:
        raise ValueError(f"Found {len(shot_prices)} products matching {search_dict}")

    search_dict["Product Family"] = task_product_family
    task_prices = price_search(**search_dict)
    if len(task_prices) != 1:
        raise ValueError(f"Found {len(task_prices)} products matching {search_dict}")

    shot_price = shot_prices[0]
    task_price = task_prices[0]

    for price in [shot_price, task_price]:
        if price["Currency"] != "USD":
            raise ValueError(f"Expected USD, found {price['Currency']}")

    shot_cost = Decimal(shot_price["PricePerUnit"]) * details["shots"]
    task_cost = Decimal(task_price["PricePerUnit"]) * 1

    return shot_cost + task_cost


def _get_simulator_task_cost(task_arn: str, details: dict) -> Decimal:
    if not details.get("billed_duration"):
        return Decimal(0)
    task_region = task_arn.split(":")[3]

    device_name = details["device"].split("/")[-1].upper()

    if details["job_task"]:
        product_family = "Braket Managed Jobs Simulator Task"
        operation = "Managed-Jobs"
    else:
        product_family = "Simulator Task"
        operation = "CompleteTask"
        if details["status"] == "FAILED" and device_name == "TN1":
            # Rehearsal step of TN1 can fail and charges still apply.
            operation = "FailedTask"

    search_dict = {
        "Region Code": task_region,
        "Version": device_name,
        "Product Family": product_family,
        "operation": operation,
    }

    duration_prices = price_search(**search_dict)

    if len(duration_prices) != 1:
        raise ValueError(f"Found {len(duration_prices)} products matching {search_dict}")

    duration_price = duration_prices[0]

    if duration_price["Currency"] != "USD":
        raise ValueError(f"Expected USD, found {duration_price['Currency']}")

    return (
        Decimal(duration_price["PricePerUnit"])
        * Decimal(details["billed_duration"] / timedelta(milliseconds=1))
        / Decimal(timedelta(**{duration_price["Unit"]: 1}) / timedelta(milliseconds=1))
    )
