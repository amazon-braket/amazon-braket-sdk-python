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

from abc import ABC, abstractmethod
from typing import Union

from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.tasks.quantum_task import QuantumTask


class Device(ABC):
    """ An abstraction over quantum devices which includes quantum computers and simulators.

    """

    def __init__(self, name: str, status: str, status_reason: str):
        """
        Args:
            name: Name of quantum device
            status: Status of quantum device
            status_reason: Status reason of quantum device
        """
        self._name = name
        self._status = status
        self._status_reason = status_reason

    @abstractmethod
    def run(self, task_specification: Union[Circuit, Problem], shots: int) -> QuantumTask:
        """ Run a quantum task specification (circuit or annealing program) on this quantum device.

        Args:
            task_specification (Union[Circuit, Problem]):  Specification of task
                (circuit or annealing problem) to run on device.
            shots (int): The number of times to run the circuit or annealing task on the device.

        Returns:
            QuantumTask: The QuantumTask tracking task execution on this device
        """
        pass

    @property
    def name(self) -> str:
        """ Return the name of this Device.

        Returns:
            str: The name of this Device
        """
        return self._name

    @property
    def status(self) -> str:
        """ Return the status of this Device.

        Returns:
            str: The status of thi Device
        """
        return self._status

    @property
    def status_reason(self) -> str:
        """ Return the status reason of this Device.

        Returns:
            str: The status reason of this Device
        """
        return self._status_reason
