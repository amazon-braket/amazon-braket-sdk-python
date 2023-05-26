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

from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.tasks.quantum_task import QuantumTask


class Device(ABC):
    """An abstraction over quantum devices that includes quantum computers and simulators."""

    def __init__(self, name: str, status: str):
        """
        Args:
            name (str): Name of quantum device
            status (str): Status of quantum device
        """
        self._name = name
        self._status = status

    @abstractmethod
    def run(
        self,
        task_specification: Union[Circuit, Problem],
        shots: Optional[int],
        inputs: Optional[Dict[str, float]],
        *args,
        **kwargs
    ) -> QuantumTask:
        """Run a quantum task specification on this quantum device. A task can be a circuit
        or an annealing problem.

        Args:
            task_specification (Union[Circuit, Problem]):  Specification of a task
                to run on device.
            shots (Optional[int]): The number of times to run the task on the device.
                Default is `None`.
            inputs (Optional[Dict[str, float]]): Inputs to be passed along with the
                IR. If IR is an OpenQASM Program, the inputs will be updated with this value.
                Not all devices and IR formats support inputs. Default: {}.

        Returns:
            QuantumTask: The QuantumTask tracking task execution on this device
        """

    @abstractmethod
    def run_batch(
        self,
        task_specifications: Union[
            Union[Circuit, Problem],
            List[Union[Circuit, Problem]],
        ],
        shots: Optional[int],
        max_parallel: Optional[int],
        inputs: Optional[Union[Dict[str, float], List[Dict[str, float]]]],
        *args,
        **kwargs
    ) -> QuantumTaskBatch: 
    # TODO: create a QuantumTaskBatch and make LocalQuantumTaskBatch and AWSQuantumTaskBatch inherits from it
        """Executes a batch of tasks in parallel

        Args:
            task_specifications (Union[Union[Circuit, Problem], List[Union[ Circuit,
                Problem,]]]): Single instance or list of circuits or problems to run on device.
            shots (Optional[int]): The number of times to run the circuit or annealing problem.                
            max_parallel (Optional[int]): The maximum number of tasks to run  in parallel.
                Batch creation will fail if this value is greater than the maximum allowed
                concurrent tasks on the device.
            inputs (Optional[Dict[str, float]]): Inputs to be passed along with the
                IR. If the IR supports inputs, the inputs will be updated with this value.

        Returns:
            QuantumTaskBatch: A batch containing all of the tasks run
        """

    @property
    def name(self) -> str:
        """Return the name of this Device.

        Returns:
            str: The name of this Device
        """
        return self._name

    @property
    def status(self) -> str:
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        return self._status
