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

from decimal import Decimal
from functools import lru_cache, singledispatch
from json import loads
from typing import Any, Dict, List

import braket.aws
from braket.tracking.tracking_context import deregister_tracker, register_tracker
from braket.tracking.tracking_events import _TaskCompletionEvent, _TaskCreationEvent, _TaskGetEvent

MIN_SIMULATOR_DURATION = 3000


class Tracker:
    """
    Amazon Braket cost tracker.
    Use this class to track costs incurred from quantum tasks on Amazon Braket.
    """

    def __init__(self):
        self._resources = {}  # Key = quantum_task_arn

    def __enter__(self):
        register_tracker(self)
        return self

    def __exit__(self, *args):
        deregister_tracker(self)

    def start(self):
        """
        Start tracking resources with this tracker.
        """
        return self.__enter__()

    def stop(self):
        """
        Stop tracking resources with this tracker.
        """
        return self.__exit__()

    def receive_event(self, event):
        _recieve_internal(event, self._resources)

    def tracked_resources(self) -> List[str]:
        """
        Resources tracked by this tracker.

        Returns:
            List[str]: The list of task ids for tasks tracked by this tracker.
        """
        return list(self._resources.keys())

    def qpu_tasks_cost(self) -> Decimal:
        """
        Estimate cost of all quantum tasks tracked by this tracker that use Braket qpu devices.

        Returns:
            Decimal: The estimated total cost in USD
        """
        total_cost = Decimal(0)
        for task_arn, details in self._resources.items():
            if "qpu" in details["device"]:
                total_cost = total_cost + _get_qpu_task_cost(task_arn, details)
        return total_cost

    def simulator_tasks_cost(self) -> Decimal:
        """
        Estimate cost of all quantum tasks tracked by this tracker using Braket simulator devices.

        Returns:
            Decimal: The estimated total cost in USD
        """
        total_cost = Decimal(0)
        for task_arn, details in self._resources.items():
            if "simulator" in details["device"]:
                total_cost = total_cost + _get_simulator_task_cost(task_arn, details)
        return total_cost

    def quantum_tasks_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a summary of quantum tasks grouped by device.

        Returns:
            Dict[str,Dict[str,Any]] : A dictionary where each key is a device arn, and maps to
                a dictionary sumarizing the tasks run on the device. The summary includes the
                total shots sent to the device and the most recent status of the quantum tasks
                created on this device. For finished tasks on simulator devices, the summary
                also includes the duration of the simulation in seconds.

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
                 'execution_duration' : 5.432,
                 'billed_execution_duration' : 6.543}}
        """
        stats = {}
        for _, details in self._resources.items():

            device_stats = stats.get(details["device"], {})

            shots = device_stats.get("shots", 0) + details["shots"]
            device_stats["shots"] = shots

            task_states = device_stats.get("tasks", {})
            task_states[details["status"]] = task_states.get(details["status"], 0) + 1
            device_stats["tasks"] = task_states

            if "execution_duration" in details:
                duration = (
                    device_stats.get("execution_duration", 0) + details["execution_duration"] / 1000
                )
                billed_duration = (
                    device_stats.get("billed_execution_duration", 0)
                    + details["billed_duration"] / 1000
                )

                device_stats["execution_duration"] = duration
                device_stats["billed_execution_duration"] = billed_duration

            stats.setdefault(details["device"], {}).update(device_stats)

        return stats


def _get_qpu_task_cost(task_arn: str, details: dict) -> Decimal:
    if details["status"] in ["FAILED", "CANCELLED"]:
        return Decimal(0)
    task_region = task_arn.split(":")[3]

    shot_price = _get_qpu_price(task_region, "shot", details["device"], details["is_job_task"])
    task_price = _get_qpu_price(task_region, "task", details["device"], details["is_job_task"])

    shot_cost = Decimal(shot_price["pricePerUnit"]["USD"]) * details["shots"]
    task_cost = Decimal(task_price["pricePerUnit"]["USD"])

    return shot_cost + task_cost


@lru_cache()
def _get_qpu_price(region: str, product: str, device_arn: str, job_task: bool) -> Dict[str, Any]:
    device_name = device_arn.split("/")[-1]
    if "2000Q" in device_name:
        device_name = "2000Q"
    elif "Advantage_system" in device_name:
        device_name = "Advantage_system"

    if job_task:
        if product == "shot":
            product_family = "Braket Managed Jobs QPU Task Shot"
        elif product == "task":
            product_family = "Braket Managed Jobs QPU Task"
    else:
        if product == "shot":
            product_family = "Quantum Task-Shot"
        elif product == "task":
            product_family = "Quantum Task"

    filters = {"regionCode": region, "productFamily": product_family, "devicename": device_name}
    return _get_pricing(filters)


def _get_simulator_task_cost(task_arn: str, details: dict) -> Decimal:
    if details["status"] not in braket.aws.AwsQuantumTask.TERMINAL_STATES:
        return Decimal(0)
    task_region = task_arn.split(":")[3]

    duration_price = _get_simulator_price(
        task_region, details["device"], details["is_job_task"], details["status"]
    )

    if duration_price["unit"] != "minutes":
        raise ValueError(f"Expected price per minute. Found price per f{duration_price['unit']}.")
    duration_cost = (
        Decimal(duration_price["pricePerUnit"]["USD"]) * details["billed_duration"] / (60 * 1000)
    )

    return duration_cost


@lru_cache()
def _get_simulator_price(
    region: str, device_arn: str, job_task: bool, status: str
) -> Dict[str, Any]:
    device_name = device_arn.split("/")[-1].upper()

    if job_task:
        product_family = "Braket Managed Jobs Simulator Task"
    else:
        product_family = "Simulator Task"

    filters = {"regionCode": region, "productFamily": product_family, "version": device_name}

    # Rehersal step of TN1 can fail and charges still apply
    if device_name == "TN1":
        if status == "FAILED":
            filters["operation"] = "FailedTask"
        elif status == "COMPLETED":
            filters["operation"] = "CompleteTask"
        else:
            return Decimal(0)
    else:
        if status != "COMPLETED":
            return Decimal(0)

    return _get_pricing(filters)


@lru_cache()
def _get_client():
    return braket.aws.AwsSession().pricing_client


def _get_pricing(filters) -> Dict[str, Any]:
    client = _get_client
    response = client.get_products(
        ServiceCode="AmazonBraket",
        Filters=[{"Field": k, "Type": "TERM_MATCH", "Value": v} for k, v in filters.items()],
    )
    price_list = response["PriceList"]
    if len(price_list) != 1:
        raise ValueError(f"Found {len(price_list)} products matching {filters}")
    price_list = loads(price_list[0])
    price = _recursive_dict_search("pricePerUnit", price_list)
    unit = _recursive_dict_search("unit", price_list)
    return {"unit": unit, "pricePerUnit": price}


def _recursive_dict_search(key, dictionary):
    if key in dictionary:
        return dictionary[key]
    for x in dictionary.values():
        if isinstance(x, dict):
            result = _recursive_dict_search(key, x)
            if result is not None:
                return result


@singledispatch
def _recieve_internal(event, resources):
    raise ValueError(f"Event type {type(event)} is not supported")


@_recieve_internal.register
def _(event: _TaskCreationEvent, resources: dict):
    resources[event.arn] = {
        "shots": event.shots,
        "device": event.device,
        "status": "CREATED",
        "is_job_task": event.is_job_task,
    }


@_recieve_internal.register
def _(event: _TaskGetEvent, resources: dict):
    # Update task data corresponding to the arn only if it exists in self._resources
    if event.arn in resources:
        resources[event.arn]["status"] = event.status


@_recieve_internal.register
def _(event: _TaskCompletionEvent, resources: dict):
    # Update task completion data corresponding to the arn only if it exists in self._resources
    if event.arn in resources:
        resources[event.arn]["status"] = event.status
        if event.execution_duration:
            resources[event.arn]["execution_duration"] = event.execution_duration
            resources[event.arn]["billed_duration"] = max(
                event.execution_duration, MIN_SIMULATOR_DURATION
            )
