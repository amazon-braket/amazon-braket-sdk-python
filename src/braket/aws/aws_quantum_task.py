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

import asyncio
import time
from typing import Any, Dict

from braket.aws.aws_quantum_task_result import AwsQuantumTaskResult
from braket.aws.aws_session import AwsSession
from braket.circuits.circuit import Circuit
from braket.tasks import QuantumTask


class AwsQuantumTask(QuantumTask):
    """Amazon Braket implementation of a quantum task."""

    # TODO: Add API documentation that defines these states. Make it clear this is the contract.
    TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED"}
    RESULTS_READY_STATES = {"COMPLETED"}

    GATE_IR_TYPE = "jaqcd"
    DEFAULT_SHOTS = 1_000

    @staticmethod
    def from_circuit(
        aws_session: AwsSession,
        device_arn: str,
        circuit: Circuit,
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: int = DEFAULT_SHOTS,
    ):
        """
        AwsQuantumTask factory method that serializes the circuit, submits to Amazon Braket, and
        returns back a AwsQuantumTask tracking the execution.

        Args:
            aws_session (AwsSession): AwsSession to call AWS with.
            device_arn (str): AWS quantum device arn.
            circuit (Circuit): Circuit to run on device.
            s3_destination_folder (AwsSession.S3DestinationFolder): NamedTuple with bucket (index 0)
                and key (index 1) that is the results destination folder in S3.
            shots (int): The number of times to run the circuit on the quantum device. If the
                device is a classical simulator then this implies sampling the state N times,
                where N = `shots`. Default = 1_000.

        Returns:
            AwsQuantumTask: AwsQuantumTask that is tracking the circuit execution on the device.

        Note:
            The following arguments are typically defined via clients of Device.
                - `circuit`
                - `s3_destination_folder`
                - `shots`
        """
        if len(s3_destination_folder) != 2:
            raise ValueError(
                "s3_destination_folder must be of size 2 with a 'bucket' and 'key' respectively."
            )

        create_task_kwargs = {
            "backendArn": device_arn,
            "resultsS3Bucket": s3_destination_folder[0],
            "resultsS3Prefix": s3_destination_folder[1],
            "ir": circuit.to_ir().json(),
            "irType": AwsQuantumTask.GATE_IR_TYPE,
            "gateModelConfig": {"qubitCount": circuit.qubit_count},
            "shots": shots,
        }
        task_arn = aws_session.create_quantum_task(**create_task_kwargs)
        return AwsQuantumTask(task_arn, aws_session)

    def __init__(
        self,
        arn: str,
        aws_session: AwsSession,
        poll_timeout_seconds: int = 120,
        poll_interval_seconds: int = 0.25,
    ):
        """
        Args:
            arn (str): The AWS quantum task ARN.
            aws_session (AwsSession): The AwsSession for communicating with AWS.
            poll_timeout_seconds (int): The polling timeout for result(), default 120 seconds.
            poll_internal_seconds (int): The polling interval for result(), default 0.25 seconds.
        """
        self._arn: str = arn
        self._aws_session: AwsSession = aws_session
        self._poll_timeout_seconds = poll_timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds

        self._metadata: Dict[str, Any] = {}
        self._result: AwsQuantumTaskResult = None
        self._future = asyncio.get_event_loop().run_until_complete(self._create_future())

    @property
    def id(self) -> str:
        """str: The AWS quantum task ARN."""
        return self._arn

    def cancel(self) -> None:
        """Cancel the quantum task. This cancels the future and the task in Amazon Braket."""
        self._future.cancel()
        self._aws_session.cancel_quantum_task(self._arn)

    def metadata(self, use_cached_value: bool = False) -> Dict[str, Any]:
        """
        Get task metadata defined in Amazon Braket.

        Args:
            use_cached_value (bool, optional): If true returns the last value retrieved from
                Amazon Braket GetQuantumTask API else the API is called and the cache is updated.
                Default = False.

        Returns:
            Dict[str, Any]: The Amazon Braket GetQuantumTask API response. TODO: INSERT BOTO3 LINK.
            If `use_cached_value` is True then Amazon Braket is not called and the last value
            retrieved is returned.
        """
        if not use_cached_value:
            self._metadata = self._aws_session.get_quantum_task(self._arn)
        return self._metadata

    def state(self, use_cached_value: bool = False) -> str:
        """
        State of the quantum task.

        Args:
            use_cached_value (bool, optional): If true returns the last state value retrieved from
                Amazon Braket GetQuantumTask API else the API is called and the cache is updated.
                Default = False.

        Returns:
            str: The value of "status" in `metadata()`. This is the value of the "status" key
            in the Amazon Braket GetQuantumTask API call. TODO: INSERT BOTO3 DOC LINK. If
            `use_cached_value` is True then Amazon Braket is not called and the last value retrieved
            is returned.

        See Also:
            `metadata()`
        """
        return self.metadata(use_cached_value).get("status")

    def result(self) -> AwsQuantumTaskResult:
        """
        Get the quantum task result by polling Amazon Braket to see if the task is completed. Once
        the task is completed the result is retrieved from S3 and returned as a QuantumTaskResult.

        This method is a blocking thread call and will synchronously return back a result. Call
        async_result() if you require an asynchronous invocation.

        Consecutive calls to this method will return back a cached result.
        """
        try:
            return asyncio.get_event_loop().run_until_complete(self.async_result())
        except asyncio.CancelledError:
            # Future was cancelled, return whatever is in self._result if anything
            return self._result

    def async_result(self) -> asyncio.Task:
        """
        Get the quantum task result asynchronously.

        Consecutive calls to this method will return back a cached result.
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
        Wrap the _wait_for_completion coroutine inside a future-like object.
        Invoking this method will start the coroutine and return back the future-like object
        that contains it. Note that this does not block on the coroutine to finish.

        Returns:
            asyncio.Task: An asyncio Task that contains the _wait_for_completion() coroutine.
        """
        return asyncio.create_task(self._wait_for_completion())

    async def _wait_for_completion(self) -> AwsQuantumTaskResult:
        """
        Waits for the quantum task to be completed and returns back result from S3.

        Returns:
            AwsQuantumTaskResult: If the task ends up in the `AwsQuantumTask.RESULTS_READY_STATES`
            state within the time limit then the result from S3 is loaded and returned. None is
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
                self._result = AwsQuantumTaskResult.from_string(result_string)
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
        return "AwsQuantumTask('id':{})".format(self.id)

    def __eq__(self, other) -> bool:
        if isinstance(other, AwsQuantumTask):
            return self.id == other.id
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.id)
