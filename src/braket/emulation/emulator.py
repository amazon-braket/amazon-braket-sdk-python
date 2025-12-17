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

from collections.abc import Iterable
from typing import Any

from braket.circuits import Circuit
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.circuits.measure import Measure
from braket.circuits.noise_model import NoiseModel
from braket.devices import Device
from braket.emulation.pass_manager import PassManager
from braket.emulation.passes import ValidationPass
from braket.tasks import QuantumTask
from braket.tasks.quantum_task import TaskSpecification
from braket.tasks.quantum_task_batch import QuantumTaskBatch


class Emulator(Device):
    """
    An emulator is a simulation device that more closely resembles the capabilities and constraints
    of a real device or of a specific device model.

    Args:
        backend (Device): The backend device to use for emulation.
        noise_model (NoiseModel | None): A noise model to apply to the emulated circuits.
            Defaults to None.
        passes (Iterable[ValidationPass] | None): A list of validation passes to apply to the
            emulated circuits. Defaults to None.
    """

    def __init__(
        self,
        backend: Device,
        noise_model: NoiseModel | None = None,
        passes: Iterable[ValidationPass] | None = None,
        **kwargs,
    ):
        Device.__init__(self, name=kwargs.get("name", "DeviceEmulator"), status="AVAILABLE")
        self._pass_manager = PassManager(passes)
        self._noise_model = noise_model
        self._backend = backend

    def run(
        self,
        task_specification: TaskSpecification,
        shots: int | None = 0,
        inputs: dict[str, float] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> QuantumTask:
        """Emulate a quantum task specification on this quantum device emulator.
        A quantum task can be a circuit or an annealing problem. Emulation
        involves running all emulator passes on the input program before running
        the program on the emulator's backend.

        Args:
            task_specification (TaskSpecification): Specification of a quantum task
                to run on device.
            shots (int | None): The number of times to run the quantum task on the device.
                Default is `None`.
            inputs (dict[str, float] | None): Inputs to be passed along with the
                IR. If IR is an OpenQASM Program, the inputs will be updated with this value.
                Not all devices and IR formats support inputs. Default: {}.

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
        task_specifications: TaskSpecification | list[TaskSpecification],
        shots: int | None,
        max_parallel: int | None,
        inputs: dict[str, float] | list[dict[str, float]] | None,
        *args: Any,
        **kwargs: Any,
    ) -> QuantumTaskBatch:
        raise NotImplementedError("Emulator does not support run_batch.")

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

    def transform(
        self, task_specification: TaskSpecification, apply_noise_model: bool = True
    ) -> TaskSpecification:
        """
        Passes the input program through all Pass objects contained in this
        emulator and applies the emulator's noise model, if it exists, before
        returning the compiled program.

        Args:
            task_specification (TaskSpecification): The input program to validate and
                compile based on this emulator's Passes
            apply_noise_model (bool): If true, apply this emulator's noise model
                to the compiled program before returning the final program.

        Returns:
            TaskSpecification: A compiled program with a noise model applied, if one
            exists for this emulator and apply_noise_model is true.
        """

        program = self._pass_manager.transform(task_specification)

        # Apply measurement manually if the circuit has no measurement and no result type.
        # This ensures that the noise model can apply readout error to the circuit, since
        # the readout error is applied if and only if there is measurement or result type
        # in the circuit. The measurement operations should be added even if apply_noise_model
        # is False.
        has_measurement = any(
            isinstance(instr.operator, Measure) for instr in task_specification.instructions
        )
        if (not has_measurement) and len(task_specification.result_types) == 0:
            task_specification.measure(target_qubits=task_specification.qubits)

        return (
            self._noise_model.apply(program) if apply_noise_model and self.noise_model else program
        )

    def _remove_verbatim_box(self, noisy_verbatim_circ: Circuit) -> Circuit:
        """
        Remove the verbatim box in the noisy circuit before simulating on
        local braket density matrix simulator.

        Args:
            noisy_verbatim_circ (Circuit): The input verbatim noisy program

        Returns:
            Circuit: A verbatim noisy program without the verbatim boxes
        """
        noisy_verbatim_circ_2 = [
            instruction
            for instruction in noisy_verbatim_circ.instructions
            if not isinstance(instruction.operator, StartVerbatimBox)
            and not isinstance(instruction.operator, EndVerbatimBox)
        ]
        noisy_verbatim_circ_3 = Circuit(noisy_verbatim_circ_2)
        for result_type in noisy_verbatim_circ.result_types:
            noisy_verbatim_circ_3.add(result_type)

        return noisy_verbatim_circ_3

    def validate(self, task_specification: TaskSpecification) -> None:
        """
        This method passes the input program through Passes that perform
        only validation, without modifying the input program.

        Args:
            task_specification (TaskSpecification): The program to validate with this
                emulator's validation passes.
        """
        self._pass_manager.validate(task_specification)
