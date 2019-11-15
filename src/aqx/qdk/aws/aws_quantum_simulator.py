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

from aqx.qdk.aws.aws_quantum_task import AwsQuantumTask
from aqx.qdk.aws.aws_session import AwsSession
from aqx.qdk.devices.device import Device


class AwsQuantumSimulator(Device):
    """
    AWS Qx implementation of a quantum simulator.
    Use this class to retrieve the latest metadata about the simulator,
    and run a circuit on the simulator.
    """

    def __init__(self, arn: str, aws_session=None):
        """
        Args:
            arn (str): Simulator type ARN e.g. "QUEST_ARN".
            aws_session (AwsSession, optional) aws_session: AWS session object. Default = None.
        """
        super().__init__(
            name=None, status=None, status_reason=None, supported_quantum_operations=None
        )
        self._arn = arn
        self._aws_session = aws_session or AwsSession()
        self._qubit_count: int = None

        self.refresh_metadata()

    def run(self, *aws_quantum_task_args, **aws_quantum_task_kwargs) -> AwsQuantumTask:
        """
        Run a circuit on this AWS quantum device.

        Args:
            *aws_quantum_task_args: Variable length positional arguments for
                `aqx.qdk.aws.aws_quantum_task.AwsQuantumTask.from_circuit()`.
            **aws_quantum_task_kwargs: Variable length keyword arguments for
                `aqx.qdk.aws.aws_quantum_task.AwsQuantumTask.from_circuit()`.

        Returns:
            AwsQuantumTask: AwsQuantumTask that is tracking the circuit execution on the device.

        Examples:
            >>> circuit = Circuit().h(0).cno(0, 1)
            >>> device = AwsQuantumSimulator("quest_arn")
            >>> device.run(circuit, ("bucket-foo", "key-bar"))

            >>> circuit = Circuit().h(0).cno(0, 1)
            >>> device = AwsQuantumSimulator("quest_arn")
            >>> device.run(circuit=circuit, s3_destination_folder=("bucket-foo", "key-bar"))

        See Also:
            `aqx.qdk.aws.aws_quantum_task.AwsQuantumTask.from_circuit()`
        """
        return AwsQuantumTask.from_circuit(
            self._aws_session, self._arn, *aws_quantum_task_args, **aws_quantum_task_kwargs
        )

    def refresh_metadata(self) -> None:
        """Refresh AwsQuantumSimulator object with most up to date simulator metadata."""
        simulator_metadata = self._aws_session.get_simulator_metadata(self._arn)
        self._name = simulator_metadata.get("name")
        self._status = simulator_metadata.get("status")
        self._status_reason = simulator_metadata.get("statusReason")
        # TODO: convert string into gate types
        self._supported_quantum_operations = simulator_metadata.get("supportedQuantumOperations")
        self._qubit_count = simulator_metadata.get("qubitCount")

    @property
    def arn(self) -> str:
        """str: Return arn of simulator."""
        return self._arn

    @property
    def qubit_count(self) -> int:
        """int: Return maximum number of qubits that can be run on simulator."""
        return self._qubit_count

    def __repr__(self):
        return f"QuantumSimulator('name': {self.name}, 'arn': {self.arn})"

    def __eq__(self, other):
        if isinstance(other, AwsQuantumSimulator):
            return self.arn == other.arn
        return NotImplemented
