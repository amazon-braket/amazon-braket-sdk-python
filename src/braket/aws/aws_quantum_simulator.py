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

from typing import Any, Dict, Union

from braket.annealing.problem import Problem
from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.circuits import Circuit
from braket.devices.device import Device


class AwsQuantumSimulator(Device):
    """
    Amazon Braket implementation of a quantum simulator.
    Use this class to retrieve the latest metadata about the simulator,
    and to run a task on the simulator.
    """

    DEFAULT_SHOTS_SIMULATOR = 0
    DEFAULT_RESULTS_POLL_TIMEOUT_SIMULATOR = 432000
    DEFAULT_RESULTS_POLL_INTERVAL_SIMULATOR = 1

    def __init__(self, arn: str, aws_session=None):
        """
        Args:
            arn (str): The ARN of the simulator, for example,
                "arn:aws:aqx:::quantum-simulator:aqx:qs1".
            aws_session (AwsSession, optional) aws_session: An AWS session object. Default = None.
        """
        super().__init__(name=None, status=None, status_reason=None)
        self._arn = arn
        self._aws_session = aws_session or AwsSession()
        self._properties: Dict[str, Any] = None
        self.refresh_metadata()

    def run(
        self,
        task_specification: Union[Circuit, Problem],
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: int = DEFAULT_SHOTS_SIMULATOR,
        poll_timeout_seconds: int = DEFAULT_RESULTS_POLL_TIMEOUT_SIMULATOR,
        poll_interval_seconds: int = DEFAULT_RESULTS_POLL_INTERVAL_SIMULATOR,
        *aws_quantum_task_args,
        **aws_quantum_task_kwargs,
    ) -> AwsQuantumTask:
        """
        Run a task on the simulator device.

        Args:
            task_specification (Union[Circuit, Problem]):  Specification of task
                (circuit or annealing problem) to run on device.
            s3_destination_folder: The S3 location to save the task's results
            shots (int, optional): The number of times to run the circuit or annealing problem.
                Default is 0.
                For circuits, when `shots=0`, the simulator will support simulator-only
                result types, compute the exact results based on the task specification,
                and sampling is not supported.
                `shots>0` means that the simulator will be treated like a QPU and
                only support result types available for a QPU.
            poll_timeout_seconds (int): The polling timeout for AwsQuantumTask.result(), in seconds.
                Default: 432000 (5 days).
            poll_interval_seconds (int): The polling interval for AwsQuantumTask.result(),
                in seconds. Default: 1.
            *aws_quantum_task_args: Variable length positional arguments for
                `braket.aws.aws_quantum_task.AwsQuantumTask.create()`.
            **aws_quantum_task_kwargs: Variable length keyword arguments for
                `braket.aws.aws_quantum_task.AwsQuantumTask.create()`.

        Returns:
            AwsQuantumTask: An AwsQuantumTask that tracks the task execution on the device.

        Examples:
            >>> circuit = Circuit().h(0).cnot(0, 1)
            >>> device = AwsQuantumSimulator("arn:aws:aqx:::quantum-simulator:aqx:qs1")
            >>> device.run(circuit, ("bucket", "key"), shots=1000)

            >>> circuit = Circuit().h(0).cnot(0, 1)
            >>> device = AwsQuantumSimulator("arn:aws:aqx:::quantum-simulator:aqx:qs1")
            >>> device.run(circuit=circuit, s3_destination_folder=("bucket", "key"), shots=1000)

        See Also:
            `braket.aws.aws_quantum_task.AwsQuantumTask.create()`
        """
        return AwsQuantumTask.create(
            self._aws_session,
            self._arn,
            task_specification,
            s3_destination_folder,
            shots,
            poll_timeout_seconds=poll_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            *aws_quantum_task_args,
            **aws_quantum_task_kwargs,
        )

    def refresh_metadata(self) -> None:
        """Refresh the AwsQuantumSimulator object with the most recent simulator metadata."""
        simulator_metadata = self._aws_session.get_simulator_metadata(self._arn)
        self._name = simulator_metadata.get("name")
        self._status = simulator_metadata.get("status")
        self._status_reason = simulator_metadata.get("statusReason")
        self._properties = {
            k: simulator_metadata.get(k)
            for k in ["supportedQuantumOperations", "qubitCount", "supportedResultTypes"]
        }

    @property
    def arn(self) -> str:
        """str: Returns the ARN of the simulator."""
        return self._arn

    @property
    # TODO: Add a link to the boto3 docs
    def properties(self) -> Dict[str, Any]:
        """Dict[str, Any]: Return the simulator properties"""
        return self._properties

    def __repr__(self):
        return f"QuantumSimulator('name': {self.name}, 'arn': {self.arn})"

    def __eq__(self, other):
        if isinstance(other, AwsQuantumSimulator):
            return self.arn == other.arn
        return NotImplemented
