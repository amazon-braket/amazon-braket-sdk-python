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
from typing import List

from braket.tasks.quantum_task import QuantumTask


class Device(ABC):
    """
    An abstraction over quantum devices which includes quantum computers and simulators.

    :param str name: name of quantum device
    :param str status: status of quantum device
    :param str status_reason: status reason of quantum device
    :param List[str] supported_quantum_operations: supported quantum operations of quantum device
    """

    def __init__(
        self, name: str, status: str, status_reason: str, supported_quantum_operations: List[str]
    ):
        self._name = name
        self._status = status
        self._status_reason = status_reason
        self._supported_quantum_operations = supported_quantum_operations

    @abstractmethod
    def run(self, circuit, shots: int) -> QuantumTask:
        """
        Run a circuit on this quantum device.

        :param Circuit circuit: circuit to run on device
        :param int shots: Number of shots to run circuit
        :return: the created quantum task
        :rtype: QuantumTask
        """

    @property
    def name(self) -> str:
        """
        Return name of Device

        :rtype: str
        """
        return self._name

    @property
    def status(self) -> str:
        """
        Return status of Device

        :rtype: str
        """
        return self._status

    @property
    def status_reason(self) -> str:
        """
        Return status reason of Device

        :rtype: str
        """
        return self._status_reason

    @property
    def supported_quantum_operations(self) -> List[str]:
        """
        Return supported quantum operations of Device

        :rtype: List[str]
        """
        return self._supported_quantum_operations
