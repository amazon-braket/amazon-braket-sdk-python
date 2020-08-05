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

from networkx import Graph

from braket.annealing.problem import Problem
from braket.aws.aws_qpu import AwsQpu
from braket.aws.aws_quantum_simulator import AwsQuantumSimulator
from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.circuits import Circuit
from braket.devices.device import Device


class AwsDevice(Device):
    """
    Amazon Braket implementation of a device.
    Use this class to retrieve the latest metadata about the device and to run a quantum task on the
    device.
    """

    _DUMMY_SHOTS = -1
    DEFAULT_SHOTS_QPU = 1000
    DEFAULT_SHOTS_SIMULATOR = 0
    DEFAULT_RESULTS_POLL_TIMEOUT = 432000
    DEFAULT_RESULTS_POLL_INTERVAL = 1

    def __init__(self, arn: str, aws_session=None):
        """
        Args:
            arn (str): The ARN of the device
            aws_session (AwsSession, optional) aws_session: An AWS session object. Default = None.

        Raises:
            ValueError: If an unknown `arn` is specified.

        Note:
            Some devices (QPUs) are physically located in specific AWS Regions. In some cases,
            the current `aws_session` connects to a Region other than the Region in which the QPU is
            physically located. When this occurs, a cloned `aws_session` is created for the Region
            the QPU is located in.
        """
        super().__init__(name=None, status=None, status_reason=None)
        if "qpu" in arn:
            self._device = AwsQpu(arn, aws_session)
        else:
            self._device = AwsQuantumSimulator(arn, aws_session)
        self._name = self._device.name
        self._status = self._device.status

    def run(
        self,
        task_specification: Union[Circuit, Problem],
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: int = _DUMMY_SHOTS,
        poll_timeout_seconds: int = DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: int = DEFAULT_RESULTS_POLL_INTERVAL,
        *aws_quantum_task_args,
        **aws_quantum_task_kwargs,
    ) -> AwsQuantumTask:
        """
        Run a quantum task specification on this device. A task can be a circuit or an
        annealing problem.

        Args:
            task_specification (Union[Circuit, Problem]):  Specification of task
                (circuit or annealing problem) to run on device.
            s3_destination_folder: The S3 location to save the task's results
            shots (int, optional): The number of times to run the circuit or annealing problem.
                Default is 1000 for QPUs and 0 for simulators.
            poll_timeout_seconds (int): The polling timeout for AwsQuantumTask.result(), in seconds.
                Default: 5 days.
            poll_interval_seconds (int): The polling interval for AwsQuantumTask.result(),
                in seconds. Default: 1 second.
            *aws_quantum_task_args: Variable length positional arguments for
                `braket.aws.aws_quantum_task.AwsQuantumTask.create()`.
            **aws_quantum_task_kwargs: Variable length keyword arguments for
                `braket.aws.aws_quantum_task.AwsQuantumTask.create()`.

        Returns:
            AwsQuantumTask: An AwsQuantumTask that tracks the execution on the device.

        Examples:
            >>> circuit = Circuit().h(0).cnot(0, 1)
            >>> device = AwsDevice("arn1")
            >>> device.run(circuit, ("bucket-foo", "key-bar"))

            >>> circuit = Circuit().h(0).cnot(0, 1)
            >>> device = AwsDevice("arn2")
            >>> device.run(task_specification=circuit,
            >>>     s3_destination_folder=("bucket-foo", "key-bar"))

            >>> problem = Problem(
            >>>     ProblemType.ISING,
            >>>     linear={1: 3.14},
            >>>     quadratic={(1, 2): 10.08},
            >>> )
            >>> device = AwsDevice("arn3")
            >>> device.run(problem, ("bucket-foo", "key-bar"),
            >>>     device_parameters = {"dWaveParameters": {"postprocessingType": "SAMPLING"}})

        See Also:
            `braket.aws.aws_quantum_task.AwsQuantumTask.create()`
        """
        if shots == AwsDevice._DUMMY_SHOTS:
            if "qpu" in self.arn:
                shots = AwsDevice.DEFAULT_SHOTS_QPU
            else:
                shots = AwsDevice.DEFAULT_SHOTS_SIMULATOR
        return self._device.run(
            task_specification,
            s3_destination_folder,
            shots,
            poll_timeout_seconds=poll_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            *aws_quantum_task_args,
            **aws_quantum_task_kwargs,
        )

    def refresh_metadata(self) -> None:
        """
        Refresh the `AwsDevice` object with the most recent Device metadata.
        """
        self._device.refresh_metadata()

    @property
    def arn(self) -> str:
        """str: Return the ARN of the device"""
        return self._device.arn

    @property
    # TODO: Add a link to the boto3 docs
    def properties(self) -> Dict[str, Any]:
        """Dict[str, Any]: Return the device properties"""
        return self._device.properties

    @property
    def topology_graph(self) -> Graph:
        """Graph: topology of device as a networkx Graph object.
        Returns None if the topology is not available for the device.

        Examples:
            >>> import networkx as nx
            >>> device = AwsDevice("arn1")
            >>> nx.draw_kamada_kawai(device.topology_graph, with_labels=True, font_weight="bold")

            >>> topology_subgraph = device.topology_graph.subgraph(range(8))
            >>> nx.draw_kamada_kawai(topology_subgraph, with_labels=True, font_weight="bold")

            >>> print(device.topology_graph.edges)
        """
        if hasattr(self._device, "topology_graph"):
            return self._device.topology_graph
        else:
            return None

    def __repr__(self):
        return "Device('name': {}, 'arn': {})".format(self.name, self.arn)

    def __eq__(self, other):
        if isinstance(other, AwsDevice):
            return self.arn == other.arn
        return NotImplemented
