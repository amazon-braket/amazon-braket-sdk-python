import asyncio
import uuid
from typing import Union

from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult, QuantumTask


class LocalQuantumTask(QuantumTask):

    def __init__(self, result_str):
        self._id = uuid.uuid4()
        self._result_str = result_str

    @property
    def id(self) -> str:
        return self._id

    def cancel(self) -> None:
        raise NotImplementedError()

    def state(self) -> str:
        raise NotImplementedError()

    def result(self) -> GateModelQuantumTaskResult:
        return GateModelQuantumTaskResult.from_string(self._result_str)

    def async_result(self) -> asyncio.Task:
        raise NotImplementedError()