import pkg_resources

from typing import Union, Optional

from braket.annealing.problem import Problem
from braket.circuits import Circuit
from braket.devices.device import Device
from braket.tasks import QuantumTask
from braket.tasks.local_quantum_task import LocalQuantumTask

simulator_devices = {entry.name: entry for entry in pkg_resources.iter_entry_points("braket.simulators")}

class LocalSimulator(Device):

    def __init__(self, backend: str, *args, **kwargs):
        if backend in simulator_devices:
            device_class = simulator_devices[backend].load()
            self._delegate = device_class()
        else:
            raise RuntimeError(f"Only the following devices are available {simulator_devices.keys()}")

    def run(self,
            task_specification: Union[Circuit, Problem],
            shots: Optional[int],
            *args,
            **kwargs) -> QuantumTask:
        instructions = task_specification.to_ir().json()
        qubits = task_specification.qubit_count
        result = self._delegate.run(instructions, qubits, shots)
        return LocalQuantumTask(result)