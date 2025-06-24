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

import logging
from collections.abc import Iterable
from typing import Any, Optional, Union

from braket.ir.openqasm import Program as OpenQasmProgram

from braket.circuits import Circuit
from braket.circuits.noise_model import NoiseModel
from braket.devices import Device
from braket.devices.local_simulator import LocalSimulator
from braket.emulation.base_emulator import BaseEmulator
from braket.passes import BasePass, ProgramType
from braket.tasks import QuantumTask
from braket.tasks.quantum_task_batch import QuantumTaskBatch

# Create a module-level logger
logger = logging.getLogger(__name__)


class EmulatorError(Exception):
    """Custom exception for emulator-related errors."""


class Emulator(Device, BaseEmulator):
    _DEFAULT_SIMULATOR_BACKEND = "default"
    _DEFAULT_NOISY_BACKEND = "braket_dm"

    """An emulator is a simulation device that more closely resembles
    the capabilities and constraints of a real device or of a specific device model."""

    def __init__(
        self,
        backend: str = "default",
        noise_model: Optional[NoiseModel] = None,
        emulator_passes: Optional[Iterable[BasePass]] = None,
        **kwargs,
    ):
        Device.__init__(self, name=kwargs.get("name", "DeviceEmulator"), status="AVAILABLE")
        BaseEmulator.__init__(self, emulator_passes)
        self._noise_model = noise_model

        backend_name = self._get_local_simulator_backend(backend, noise_model)
        self._backend = LocalSimulator(backend=backend_name, noise_model=noise_model)

    def _get_local_simulator_backend(
        self, backend: str, noise_model: Optional[NoiseModel] = None
    ) -> str:
        """
        Returns the name of the backend to use with the local simulator.

        Args:
            backend (str): The name of the backend requested by the customer, or default if none
                were provided.
            noise_model (Optional[NoiseModel]): A noise model to use with the emulator, if at all.
                If a noise model is provided, the density matrix simulator is used.

        Returns:
            str: The name of the backend to pass into the LocalSimulator constructor.
        """
        if backend == "default":
            if noise_model:
                logger.info(
                    "Setting LocalSimulator backend to use 'braket_dm' \
                        because a NoiseModel was provided."
                )
                return Emulator._DEFAULT_NOISY_BACKEND
            return Emulator._DEFAULT_SIMULATOR_BACKEND
        return backend

    def run(
        self,
        task_specification: Union[
            Circuit,
            OpenQasmProgram,
        ],
        shots: Optional[int] = 0,
        inputs: Optional[dict[str, float]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> QuantumTask:
        """Emulate a quantum task specification on this quantum device emulator.
        A quantum task can be a circuit or an annealing problem. Emulation
        involves running all emulator passes on the input program before running
        the program on the emulator's backend.

        Args:
            task_specification (Union[Circuit, OpenQasmProgram]): Specification of a quantum task
                to run on device.
            shots (Optional[int]): The number of times to run the quantum task on the device.
                Default is `None`.
            inputs (Optional[dict[str, float]]): Inputs to be passed along with the
                IR. If IR is an OpenQASM Program, the inputs will be updated with this value.
                Not all devices and IR formats support inputs. Default: {}.
            *args (Any):  Arbitrary arguments.
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            QuantumTask: The QuantumTask tracking task execution on this device emulator.
        """
        task_specification = self.transform(task_specification, apply_noise_model=False)
        # Don't apply noise model as the local simulator will automatically apply it.

        # Remove the verbatim box before submitting to the braket density matrix simulator
        task_specification_v2 = self._remove_verbatim_box(task_specification)
        return self._backend.run(task_specification_v2, shots, inputs, *args, **kwargs)

    def run_batch(
        self,
        task_specifications: Union[
            Union[Circuit, OpenQasmProgram],
            list[
                Union[
                    Circuit,
                    OpenQasmProgram,
                ]
            ],
        ],
        shots: Optional[int] = 0,
        max_parallel: Optional[int] = None,
        inputs: Optional[Union[dict[str, float], list[dict[str, float]]]] = None,
        *args,
        **kwargs,
    ) -> QuantumTaskBatch:
        raise NotImplementedError("Emulator.run_batch() is not implemented yet.")

    @property
    def noise_model(self) -> NoiseModel:
        """
        An emulator may be defined with a quantum noise model which mimics the noise
        on a physical device. A quantum noise model can be defined using the
        NoiseModel class. The noise model is applied to Braket Circuits before
        running them on the emulator backend.

        Returns:
            NoiseModel: This emulator's noise model.
        """
        return self._noise_model

    @noise_model.setter
    def noise_model(self, noise_model: NoiseModel) -> None:
        """
        Setter method for the Emulator noise_model property. Re-instantiates
        the backend with the new NoiseModel object.

        Args:
            noise_model (NoiseModel): The new noise model.
        """
        self._noise_model = noise_model
        self._backend = LocalSimulator(backend="braket_dm", noise_model=noise_model)

    def transform(
        self, task_specification: ProgramType, apply_noise_model: bool = True
    ) -> ProgramType:
        """
        Passes the input program through all Pass objects contained in this
        emulator and applies the emulator's noise model, if it exists, before
        returning the compiled program.

        Args:
            task_specification (ProgramType): The input program to validate and
                compile based on this emulator's Passes
            apply_noise_model (bool): If true, apply this emulator's noise model
                to the compiled program before returning the final program.

        Returns:
            ProgramType: A compiled program with a noise model applied, if one
            exists for this emulator and apply_noise_model is true.
        """
        try:
            program = super().transform(task_specification)
            return (
                self._noise_model.apply(program)
                if apply_noise_model and self.noise_model
                else program
            )
            # if apply_noise_model and self.noise_model:
            #     return self._noise_model.apply(program)
            # return program
        except Exception as e:
            self._raise_exception(e)

    def _remove_verbatim_box(self, noisy_verbatim_circ: ProgramType) -> ProgramType:
        """
        Remove the verbatim box in the noisy circuit before simulating on
        local braket density matrix simulator.

        Args:
            noisy_verbatim_circ (ProgramType): The input verbatim noisy circuit

        Returns:
            ProgramType: A verbatim noisy circuit without the verbatim boxes
        """
        noisy_verbatim_circ_2 = [
            instruction
            for instruction in noisy_verbatim_circ.instructions
            if "VerbatimBox" not in instruction.operator.name
        ]
        return Circuit(noisy_verbatim_circ_2)

    def validate(self, task_specification: ProgramType) -> None:
        """
        Runs only Passes that are ValidationPass, i.e. all non-modifying
        validation passes on the input program.

        Args:
            task_specification (ProgramType): The input program to validate.
        """
        try:
            super().validate(task_specification)
        except Exception as e:
            self._raise_exception(e)

    def _raise_exception(self, exception: Exception) -> None:
        """
        Wrapper for exceptions, appends the emulator's name to the exception
        note.

        Args:
            exception (Exception): The exception to modify and raise.
        """
        raise EmulatorError(str(exception) + f" ({self._name})") from exception
