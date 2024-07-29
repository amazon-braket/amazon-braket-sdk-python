from __future__ import annotations

import logging
from typing import Any, Iterable, Optional, Union

from braket.circuits import Circuit
from braket.circuits.noise_model import NoiseModel
from braket.devices import Device
from braket.devices.local_simulator import LocalSimulator
from braket.emulation.base_emulator import BaseEmulator
from braket.emulation.emulator_passes import EmulationPass, ProgramType
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.tasks import QuantumTask
from braket.tasks.quantum_task_batch import QuantumTaskBatch


class Emulator(Device, BaseEmulator):

    _DEFAULT_SIMULATOR_BACKEND = "default"
    _DEFAULT_NOISY_BACKEND = "braket_dm"

    """An emulator is a simulation device that more closely resembles
    the capabilities and constraints of a real device or of a specific device model."""

    def __init__(
        self,
        backend: str = "default",
        noise_model: Optional[NoiseModel] = None,
        emulator_passes: Iterable[EmulationPass] = None,
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
        if noise_model:
            if backend == "default":
                logging.info(
                    "Setting LocalSimulator backend to use 'braket_dm' \
                        because a NoiseModel was provided."
                )
            return Emulator._DEFAULT_NOISY_BACKEND
        return Emulator._DEFAULT_SIMULATOR_BACKEND

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
        task_specification = self.run_passes(task_specification, apply_noise_model=False)
        # Don't apply noise model as the local simulator will automatically apply it.
        return self._backend.run(task_specification, shots, inputs, *args, **kwargs)

    def run_batch(  # noqa: C901
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

    def run_passes(
        self, task_specification: ProgramType, apply_noise_model: bool = True
    ) -> ProgramType:
        """
        Passes the input program through all EmulationPass objects contained in this
        emulator and applies the emulator's noise model, if it exists, before
        returning the compiled program.

        Args:
            task_specification (ProgramType): The input program to validate and
                compile based on this emulator's EmulationPasses
            apply_noise_model (bool): If true, apply this emulator's noise model
                to the compiled program before returning the final program.

        Returns:
            ProgramType: A compiled program with a noise model applied, if one
            exists for this emulator and apply_noise_model is true.
        """
        try:
            program = super().run_passes(task_specification)
            if apply_noise_model and self.noise_model:
                return self._noise_model.apply(program)
            return program
        except Exception as e:
            self._raise_exception(e)

    def validate(self, task_specification: ProgramType) -> None:
        """
        Runs only EmulationPasses that are ValidationPass, i.e. all non-modifying
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
        raise type(exception)(str(exception) + f" ({self._name})")
