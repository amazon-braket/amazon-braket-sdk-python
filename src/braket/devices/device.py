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

import warnings
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.circuits import Circuit, Noise
from braket.circuits.noise_model import NoiseModel
from braket.circuits.translations import SUPPORTED_NOISE_PRAGMA_TO_NOISE
from braket.device_schema import DeviceActionType
from braket.ir.openqasm import Program
from braket.tasks.quantum_task import QuantumTask
from braket.tasks.quantum_task_batch import QuantumTaskBatch


class Device(ABC):
    """An abstraction over quantum devices that includes quantum computers and simulators."""

    def __init__(self, name: str, status: str):
        """Initializes a `Device`.

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
        inputs: Optional[dict[str, float]],
        *args,
        **kwargs,
    ) -> QuantumTask:
        """Run a quantum task specification on this quantum device. A quantum task can be a circuit
        or an annealing problem.

        Args:
            task_specification (Union[Circuit, Problem]): Specification of a quantum task
                to run on device.
            shots (Optional[int]): The number of times to run the quantum task on the device.
                Default is `None`.
            inputs (Optional[dict[str, float]]): Inputs to be passed along with the
                IR. If IR is an OpenQASM Program, the inputs will be updated with this value.
                Not all devices and IR formats support inputs. Default: {}.
            *args (Any):  Arbitrary arguments.
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            QuantumTask: The QuantumTask tracking task execution on this device
        """

    @abstractmethod
    def run_batch(
        self,
        task_specifications: Union[
            Union[Circuit, Problem],
            list[Union[Circuit, Problem]],
        ],
        shots: Optional[int],
        max_parallel: Optional[int],
        inputs: Optional[Union[dict[str, float], list[dict[str, float]]]],
        *args: Any,
        **kwargs: Any,
    ) -> QuantumTaskBatch:
        """Executes a batch of quantum tasks in parallel

        Args:
            task_specifications (Union[Union[Circuit, Problem], list[Union[Circuit, Problem]]]):
                Single instance or list of circuits or problems to run on device.
            shots (Optional[int]): The number of times to run the circuit or annealing problem.
            max_parallel (Optional[int]): The maximum number of quantum tasks to run  in parallel.
                Batch creation will fail if this value is greater than the maximum allowed
                concurrent quantum tasks on the device.
            inputs (Optional[Union[dict[str, float], list[dict[str, float]]]]): Inputs to be
                passed along with the IR. If the IR supports inputs, the inputs will be updated
                with this value.
            *args (Any):  Arbitrary arguments.
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            QuantumTaskBatch: A batch containing all of the qauntum tasks run
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

    def _validate_device_noise_model_support(self, noise_model: NoiseModel) -> None:
        supported_noises = {
            SUPPORTED_NOISE_PRAGMA_TO_NOISE[pragma].__name__
            for pragma in self.properties.action[DeviceActionType.OPENQASM].supportedPragmas
            if pragma in SUPPORTED_NOISE_PRAGMA_TO_NOISE
        }
        noise_operators = {noise_instr.noise.name for noise_instr in noise_model._instructions}
        if not noise_operators <= supported_noises:
            raise ValueError(
                f"{self.name} does not support noise simulation or the noise model includes noise "
                f"that is not supported by {self.name}."
            )

    def _apply_noise_model_to_circuit(
        self, task_specification: Union[Circuit, Problem, Program, AnalogHamiltonianSimulation]
    ) -> Union[Circuit, Problem, Program, AnalogHamiltonianSimulation]:
        if isinstance(task_specification, Circuit):
            for instruction in task_specification.instructions:
                if isinstance(instruction.operator, Noise):
                    warnings.warn(
                        "The noise model of the device is applied to a circuit that already has"
                        " noise instructions.",
                        stacklevel=2,
                    )
                    break
            task_specification = self._noise_model.apply(task_specification)
        else:
            warnings.warn(
                "Noise model is only applicable to circuits. The type of the task specification is"
                f" {task_specification.__class__.__name__}. The noise model of the device does not"
                " apply.",
                stacklevel=2,
            )
        return task_specification
