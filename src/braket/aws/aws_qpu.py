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

from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.devices.device import Device


class AwsQpu(Device):
    """
    Amazon Braket implementation of a QPU.
    Use this class to retrieve the latest metadata about the QPU, and run a circuit on the QPU.
    """

    def __init__(self, arn: str, aws_session=None):
        """
        Args:
            arn (str): QPU ARN, e.g. "arn:aws:aqx:::qpu:ionq"
            aws_session (AwsSession, optional) aws_session: AWS session object. Default = None.
        """
        super().__init__(
            name=None, status=None, status_reason=None, supported_quantum_operations=None
        )
        self._arn = arn
        self._aws_session = aws_session or AwsSession()
        self._qubit_count: int = None
        # TODO: convert into graph object of qubits, type TBD
        self._connectivity_graph = None

        self.refresh_metadata()

    def run(self, *aws_quantum_task_args, **aws_quantum_task_kwargs) -> AwsQuantumTask:
        """
        Run a circuit on this AWS quantum device.

        Args:
            *aws_quantum_task_args: Variable length positional arguments for
                `braket.aws.aws_quantum_task.AwsQuantumTask.from_circuit()`.
            **aws_quantum_task_kwargs: Variable length keyword arguments for
                `braket.aws.aws_quantum_task.AwsQuantumTask.from_circuit()`.

        Returns:
            AwsQuantumTask: AwsQuantumTask that is tracking the circuit execution on the device.

        Examples:
            >>> circuit = Circuit().h(0).cnot(0, 1)
            >>> device = AwsQpu("ionq_arn")
            >>> device.run(circuit, ("bucket-foo", "key-bar"))

            >>> circuit = Circuit().h(0).cnot(0, 1)
            >>> device = AwsQpu("ionq_arn")
            >>> device.run(circuit=circuit, s3_destination_folder=("bucket-foo", "key-bar"))

        See Also:
            `braket.aws.aws_quantum_task.AwsQuantumTask.from_circuit()`
        """
        return AwsQuantumTask.from_circuit(
            self._aws_session, self._arn, *aws_quantum_task_args, **aws_quantum_task_kwargs
        )

    def refresh_metadata(self) -> None:
        """
        Refresh AwsQpu object with most up to date QPU metadata.
        """
        qpu_metadata = self._aws_session.get_qpu_metadata(self._arn)
        self._name = qpu_metadata.get("name")
        self._status = qpu_metadata.get("status")
        self._status_reason = qpu_metadata.get("statusReason")
        # TODO: convert string into gate types
        self._supported_quantum_operations = qpu_metadata.get("supportedQuantumOperations")
        self._qubit_count = qpu_metadata.get("qubitCount")
        if "connectivity" in qpu_metadata:
            self._connectivity_graph = qpu_metadata.get("connectivity").get("connectivityGraph")

    @property
    def arn(self) -> str:
        """
        Return arn of QPU

        :rtype: str
        """
        return self._arn

    @property
    def qubit_count(self) -> int:
        """
        Return maximum number of qubits that can be run on QPU

        :rtype: int
        """
        return self._qubit_count

    @property
    def connectivity_graph(self):
        """
        Return connectivity graph of QPU
        """
        return self._connectivity_graph

    def __repr__(self):
        return "QPU('name': {}, 'arn': {})".format(self.name, self.arn)

    def __eq__(self, other):
        if isinstance(other, AwsQpu):
            return self.arn == other.arn
        return NotImplemented
