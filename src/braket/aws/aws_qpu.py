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
import boto3
from braket.aws.aws_qpu_arns import AwsQpuArns
from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.devices.device import Device


class AwsQpu(Device):
    """
    Amazon Braket implementation of a QPU.
    Use this class to retrieve the latest metadata about the QPU, and run a circuit on the QPU.
    """

    QPU_REGIONS = {AwsQpuArns.RIGETTI: ["us-west-1"], AwsQpuArns.IONQ: ["us-east-1"]}

    def __init__(self, arn: str, aws_session=None):
        """
        Args:
            arn (str): QPU ARN, e.g. "arn:aws:aqx:::qpu:ionq"
            aws_session (AwsSession, optional) aws_session: AWS session object. Default = None.

        Raises:
            ValueError: If unknown `arn` is supplied.

        Note:
            QPUs are physically located in specific AWS regions. If the supplied `aws_session`
            is connected to a region that the QPU is not in then a cloned `aws_session`
            will be created for the QPU region.

            See `braket.aws.aws_qpu.AwsQpu.QPU_REGIONS` for the regions the QPUs are located in.
        """
        super().__init__(
            name=None, status=None, status_reason=None, supported_quantum_operations=None
        )
        self._arn = arn
        self._aws_session = self._aws_session_for_qpu(arn, aws_session)
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
            >>> device = AwsQpu("arn:aws:aqx:::qpu:rigetti")
            >>> device.run(circuit, ("bucket-foo", "key-bar"))

            >>> circuit = Circuit().h(0).cnot(0, 1)
            >>> device = AwsQpu("arn:aws:aqx:::qpu:rigetti")
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
        """str: Return arn of QPU."""
        return self._arn

    @property
    def qubit_count(self) -> int:
        """int: Return maximum number of qubits that can be run on QPU."""
        return self._qubit_count

    @property
    def connectivity_graph(self):
        """Return connectivity graph of QPU."""
        return self._connectivity_graph

    def _aws_session_for_qpu(self, qpu_arn: str, aws_session: AwsSession) -> AwsSession:
        """
        Get an AwsSession for the QPU ARN. QPUs are only available in certain regions so any
        supplied AwsSession in a region the QPU doesn't support will need to be adjusted.
        """

        qpu_regions = AwsQpu.QPU_REGIONS.get(qpu_arn, [])
        if not qpu_regions:
            raise ValueError(f"Unknown QPU {qpu_arn} was supplied.")

        if aws_session:
            if aws_session.boto_session.region_name in qpu_regions:
                return aws_session
            else:
                creds = aws_session.boto_session.get_credentials()
                boto_session = boto3.Session(
                    aws_access_key_id=creds.access_key,
                    aws_secret_access_key=creds.secret_key,
                    aws_session_token=creds.token,
                    region_name=qpu_regions[0],
                )
                return AwsSession(boto_session=boto_session)
        else:
            boto_session = boto3.Session(region_name=qpu_regions[0])
            return AwsSession(boto_session=boto_session)

    def __repr__(self):
        return "QPU('name': {}, 'arn': {})".format(self.name, self.arn)

    def __eq__(self, other):
        if isinstance(other, AwsQpu):
            return self.arn == other.arn
        return NotImplemented
