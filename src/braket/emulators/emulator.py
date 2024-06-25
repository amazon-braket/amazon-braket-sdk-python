from __future__ import annotations
from typing import Iterable, Any, Optional, Union, Optional
from abc import abstractmethod
from braket.simulator import BraketSimulator
from braket.tasks import QuantumTask
from braket.devices.local_simulator import LocalSimulator
from braket.emulators.emulater_interface import EmulatorInterface
from braket.emulators.emulator_passes import EmulatorPass, ProgramType
from braket.devices import Device
from braket.circuits import Circuit
from braket.circuits.noise_model import NoiseModel
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.tasks.quantum_task_batch import QuantumTaskBatch
import logging

class Emulator(Device, EmulatorInterface):
    """An emulator is a simulation device that more closely resembles the capabilities and constraints of a real
    device or of a specific device model."""

    def __init__(self,  backend: Union[str, Device]="default",
                        noise_model: Optional[NoiseModel] = None,
                        emulator_passes: Iterable[EmulatorPass] = None, **kwargs):
        
        EmulatorInterface.__init__(self, emulator_passes)
        self._noise_model = noise_model
        if noise_model and backend == "default": 
            logging.info("Setting LocalSimulator backend to use 'braket_dm' because a NoiseModel was provided.")
            backend = "braket_dm"
        
        self._backend = LocalSimulator(backend=backend, noise_model=noise_model)


    def run(self, 
            task_specification: Union[
            Circuit,
            OpenQasmProgram,
        ], 
            shots: int = 0, 
            inputs: Optional[dict[str, float]] = None,
            dry_run=False,
            *args: Any, 
            **kwargs: Any
    ) -> QuantumTask:
        """
        This method validates the input program against the emulator's passes and applies any provided noise model before
        running the circuit.
        """
        task_specification = self.run_program_passes(task_specification, apply_noise_model=False) #Don't apply noise model as the local simulator will automatically apply it. 
        return self._backend.run(task_specification, shots, inputs, *args, **kwargs)


    def run_batch(  # noqa: C901
        self,
        task_specifications: Union[
            Union[
                Circuit, OpenQasmProgram
            ],
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
    def noise_model(self):
        return self._noise_model
    
    @noise_model.setter
    def noise_model(self, noise_model: NoiseModel):
        self._noise_model = noise_model
        self._backend = LocalSimulator(backend="braket_dm", noise_model=noise_model)
        
    def run_program_passes(self, task_specification: ProgramType, apply_noise_model=True) -> ProgramType:
        program = super().run_program_passes(task_specification)
        if apply_noise_model:
            return self._noise_model.apply(program)
        return program