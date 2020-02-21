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

from __future__ import annotations

import asyncio
import time
from functools import singledispatch
from typing import Any, Callable, Dict, Union

from braket.annealing.problem import Problem
from braket.aws.aws_session import AwsSession
from braket.circuits.circuit import Circuit
from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult, QuantumTask


# TODO: add AnnealingQuantumTaskResult
class AwsQuantumTask(QuantumTask):
    """Amazon Braket implementation of a quantum task. A task can be a circuit or an annealing problem. Cuurently, only circuits are supported in the Private Beta."""

    # TODO: Add API documentation that defines these states. Make it clear this is the contract.
    TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED"}
    RESULTS_READY_STATES = {"COMPLETED"}

    GATE_IR_TYPE = "jaqcd"
    ANNEALING_IR_TYPE = "annealing"
    DEFAULT_SHOTS = 1_000

    @staticmethod
    def create(
        aws_session: AwsSession,
        device_arn: str,
        task_specification: Union[Circuit, Problem],
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: int = DEFAULT_SHOTS,
        backend_parameters: Dict[str, Any] = None,
        *args,
        **kwargs,
    ) -> AwsQuantumTask:
        """
        An `AwsQuantumTask` factory method that serializes a quantum task specification, 
        submits it to Amazon Braket, and then returns an `AwsQuantumTask` that tracks the execution of the task.

        Args:
            aws_session (AwsSession): AwsSession to connect to AWS with.
            device_arn (str): The ARN of the quantum device.
            task_specification (Union[Circuit, Problem]): The specification of the task 
                to run on device.
            s3_destination_folder (AwsSession.S3DestinationFolder): NamedTuple with bucket (index 0)
                and key (index 1) that specifies the Amazon S3 bucket and folder to store task results.
            shots (int): The number of times to run the task on the device.
                If the device is a classical simulator, this implies the state is sampled N times,
                where N = `shots`. Default shots = 1_000.
            backend_parameters (Dict[str, Any]): Additional parameters to send to the device.
                For example, for D-Wave:
                >>> backend_parameters = {"dWaveParameters": {"postprocess": "OPTIMIZATION"}}

        Returns:
            AwsQuantumTask: An AwsQuantumTask that tracks the task execution on the device.

        Note:
            The following arguments are typically defined via clients of Device.
                - `task_specification`
                - `s3_destination_folder`
                - `shots`
        """
        if len(s3_destination_folder) != 2:
            raise ValueError(
                "s3_destination_folder must be of size 2 with a 'bucket' and 'key' respectively."
            )

        create_task_kwargs = _create_common_params(device_arn, s3_destination_folder, shots)
        return _create_internal(
            task_specification,
            aws_session,
            create_task_kwargs,
            backend_parameters or {},
            *args,
            **kwargs,
        )

    def __init__(
        self,
        arn: str,
        aws_session: AwsSession,
        results_formatter: Callable[[str], Any],
        poll_timeout_seconds: int = 120,
        poll_interval_seconds: int = 0.25,
    ):
        """
        Args:
            arn (str): The ARN of the task.
            aws_session (AwsSession): The `AwsSession` for connecting to AWS services.
            results_formatter (Callable[[str], Any]): A function that deserializes a string
                into a results structure (such as `GateModelQuantumTaskResult`)
            poll_timeout_seconds (int): The polling timeout for result(), default is 120 seconds.
            poll_interval_seconds (int): The polling interval for result(), default is 0.25 seconds.
        """
        self._arn: str = arn
        self._aws_session: AwsSession = aws_session
        self._results_formatter = results_formatter
        self._poll_timeout_seconds = poll_timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds

        self._metadata: Dict[str, Any] = {}
        self._result: Union[GateModelQuantumTaskResult, AnnealingQuantumTaskResult] = None
        self._future = asyncio.get_event_loop().run_until_complete(self._create_future())

    @property
    def id(self) -> str:
        """str: The ARN of the task."""
        return self._arn

    def cancel(self) -> None:
        """Cancel the task. This cancels the future object and the task in Amazon Braket."""
        self._future.cancel()
        self._aws_session.cancel_quantum_task(self._arn)

    def metadata(self, use_cached_value: bool = False) -> Dict[str, Any]:
        """
        Get the task metadata defined in Amazon Braket.

        Args:
            use_cached_value (bool, optional): If `True`, uses the value most recently retrieved from
                the Amazon Braket `GetQuantumTask` operation. If `False`, calls the `GetQuantumTask` 
                operation  to retrieve metadata, which also updates the cached value.
                Default = False.

        Returns:
            Dict[str, Any]: The response from the Amazon Braket `GetQuantumTask` operation. 
            If `use_cached_value` is `True`, Amazon Braket is not called and the most recently 
            retrieved value is returned.
        """
        if not use_cached_value:
            self._metadata = self._aws_session.get_quantum_task(self._arn)
        return self._metadata

    def state(self, use_cached_value: bool = False) -> str:
        """
        The state of the quantum task.

        Args:
            use_cached_value (bool, optional): If `True`, uses the value most recently retrieved from
                the Amazon Braket `GetQuantumTask` operation. If `False`, calls the `GetQuantumTask` 
                operation  to retrieve metadata, which also updates the cached value.
                Default = False.

        Returns:
            str: The value of `status` in `metadata()`. This is the value of the `status` key
            in the Amazon Braket `GetQuantumTask` operation. If `use_cached_value` is `True`, 
            the value most recently returned from the `GetQuantumTask` operation is used. 

        See Also:
            `metadata()`
        """
        return self.metadata(use_cached_value).get("status")

    def result(self) -> Union[GateModelQuantumTaskResult, AnnealingQuantumTaskResult]:
        """
        Get the quantum task result by polling Amazon Braket to see if the task is completed. Once
        the task is completed, the result is retrieved from S3 and returned as a `QuantumTaskResult`.

        This method is a blocking thread call and synchronously returns a result. Call
        async_result() if you require an asynchronous invocation.

        Consecutive calls to this method return a cached result from the preceding request.
        """
        try:
            return asyncio.get_event_loop().run_until_complete(self.async_result())
        except asyncio.CancelledError:
            # Future was cancelled, return whatever is in self._result if anything
            return self._result

    def async_result(self) -> asyncio.Task:
        """
        Get the quantum task result asynchronously.

        Consecutive calls to this method return a cached result from the preceding request.
        """
        if (
            self._future.done()
            and self.metadata(use_cached_value=True).get("status")
            not in AwsQuantumTask.TERMINAL_STATES
        ):  # Future timed out
            self._future = asyncio.get_event_loop().run_until_complete(self._create_future())
        return self._future

    async def _create_future(self) -> asyncio.Task:
        """
        Wrap the `_wait_for_completion` coroutine inside a future-like object.
        Invoking this method starts the coroutine and returns back the future-like object
        that contains it. Note that this does not block on the coroutine to finish.

        Returns:
            asyncio.Task: An asyncio task that contains the `_wait_for_completion()` coroutine.
        """
        return asyncio.create_task(self._wait_for_completion())

    async def _wait_for_completion(self) -> GateModelQuantumTaskResult:
        """
        Waits for the quantum task to be completed, then returns the result from the S3 bucket.

        Returns:
            GateModelQuantumTaskResult: If the task is in the `AwsQuantumTask.RESULTS_READY_STATES`
            state within the specified time limit, the result from the S3 bucket is loaded and returned. `None` is
            returned if a timeout occurs or task state is in `AwsQuantumTask.TERMINAL_STATES`
            but not `AwsQuantumTask.RESULTS_READY_STATES`.

        Note:
            Timeout and sleep intervals are defined in the constructor fields
            `poll_timeout_seconds` and `poll_interval_seconds` respectively.
        """
        start_time = time.time()

        while (time.time() - start_time) < self._poll_timeout_seconds:
            current_metadata = self.metadata()
            if current_metadata["status"] in AwsQuantumTask.RESULTS_READY_STATES:
                result_string = self._aws_session.retrieve_s3_object_body(
                    current_metadata["resultsS3Bucket"], current_metadata["resultsS3ObjectKey"]
                )
                self._result = self._results_formatter(result_string)
                return self._result
            elif current_metadata["status"] in AwsQuantumTask.TERMINAL_STATES:
                self._result = None
                return None
            else:
                await asyncio.sleep(self._poll_interval_seconds)

        # Timed out
        self._result = None
        return None

    def __repr__(self) -> str:
        return f"AwsQuantumTask('id':{self.id})"

    def __eq__(self, other) -> bool:
        if isinstance(other, AwsQuantumTask):
            return self.id == other.id
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.id)


@singledispatch
def _create_internal(
    task_specification: Union[Circuit, Problem],
    aws_session: AwsSession,
    create_task_kwargs: Dict[str, Any],
    backend_parameters: Dict[str, Any],
    *args,
    **kwargs,
) -> AwsQuantumTask:
    raise TypeError("Invalid task specification type")


@_create_internal.register
def _(
    circuit: Circuit, aws_session: AwsSession, create_task_kwargs: Dict[str, Any], *args, **kwargs,
) -> AwsQuantumTask:
    create_task_kwargs.update(
        {
            "ir": circuit.to_ir().json(),
            "irType": AwsQuantumTask.GATE_IR_TYPE,
            "backendParameters": {"gateModelParameters": {"qubitCount": circuit.qubit_count}},
        }
    )

    task_arn = aws_session.create_quantum_task(**create_task_kwargs)
    return AwsQuantumTask(task_arn, aws_session, GateModelQuantumTaskResult.from_string)


@_create_internal.register
def _(
    problem: Problem,
    aws_session: AwsSession,
    create_task_kwargs: Dict[str, Any],
    backend_parameters: Dict[str, Any],
    *args,
    **kwargs,
) -> AwsQuantumTask:
    create_task_kwargs.update(
        {
            "ir": problem.to_ir().json(),
            "irType": AwsQuantumTask.ANNEALING_IR_TYPE,
            "backendParameters": {"annealingModelParameters": backend_parameters},
        }
    )

    task_arn = aws_session.create_quantum_task(**create_task_kwargs)
    return AwsQuantumTask(task_arn, aws_session, AnnealingQuantumTaskResult.from_string)


def _create_common_params(
    device_arn: str, s3_destination_folder: AwsSession.S3DestinationFolder, shots: int
) -> Dict[str, Any]:
    return {
        "backendArn": device_arn,
        "resultsS3Bucket": s3_destination_folder[0],
        "resultsS3Prefix": s3_destination_folder[1],
        "shots": shots,
    }
