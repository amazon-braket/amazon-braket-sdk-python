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

from decimal import Decimal
from functools import lru_cache, singledispatchmethod
from json import loads

import braket.aws
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
            "is_job_task": event.is_job_task,
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
                self._resources[event.arn]["billed_duration"] = max(event.execution_duration, MIN_SIMULATOR_DURATION)

    # Not making this a property so that it can be extended
    # to include filters if needed.
    def tracked_resources(self):
        return list(self._resources.keys())

    def qpu_tasks_cost(self) -> Decimal:
        # Filter qpu tasks and return sum of all costs.
        total_cost = Decimal(0)
        for task_arn, details in self._resources.items():
            if "qpu" in details["device"]:
                total_cost = total_cost + _get_qpu_task_cost(task_arn, details)
        return total_cost

    def simulator_tasks_cost(self) -> Decimal:
        # Filter simulator tasks and return sum of all costs.
        total_cost = Decimal(0)
        for task_arn, details in self._resources.items():
            if "qpu" not in details["device"]:
                total_cost = total_cost + _get_simulator_task_cost(task_arn, details)
        return total_cost

    def quantum_tasks_statistics(self):
        stats = {}
        for _, details in self._resources.items():

            device_stats = stats.get(details["device"], {})

            shots = device_stats.get("shots", 0) + details["shots"]
            device_stats["shots"] = shots

            task_states = device_stats.get("tasks", {})
            task_states[details["status"]] = task_states.get(details["status"], 0) + 1
            device_stats["tasks"] = task_states

            if "execution_duration" in details:
                duration = device_stats.get("execution_duration", 0) + details["execution_duration"]
                billed_duration = (
                    device_stats.get("billed_execution_duration", 0) + details["billed_duration"]
                )

                device_stats["execution_duration"] = duration
                device_stats["billed_execution_duration"] = billed_duration

            stats.setdefault(details["device"], {}).update(device_stats)

        return stats


def _get_qpu_task_cost(task_arn: str, details: dict) -> Decimal:
    task_region = task_arn.split(":")[3]

    shot_price = _get_qpu_price(task_region, "shot", details["device"], details["is_job_task"])
    task_price = _get_qpu_price(task_region, "task", details["device"], details["is_job_task"])

    shot_cost = Decimal(shot_price["pricePerUnit"]["USD"]) * details["shots"]
    task_cost = Decimal(task_price["pricePerUnit"]["USD"])

    return shot_cost + task_cost


@lru_cache()
def _get_qpu_price(region: str, product: str, device_arn: str, job_task: bool):
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
        return None
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
def _get_simulator_price(region: str, device_arn: str, job_task: bool, status: str):
    device_name = device_arn.split("/")[-1].upper()

    if job_task:
        product_family = "Braket Managed Jobs Simulator Task"
    else:
        product_family = "Simulator Task"

    filters = {"regionCode": region, "productFamily": product_family, "version": device_name}

    if device_name == "TN1":
        if status == "FAILED":
            filters["operation"] = "FailedTask"
        elif status == "COMPLETED":
            filters["operation"] = "CompleteTask"

    return _get_pricing(filters)


def _get_pricing(filters) -> dict:
    client = braket.aws.AwsSession().pricing_client
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
