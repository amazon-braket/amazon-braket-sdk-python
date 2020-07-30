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

import boto3
from networkx import Graph, complete_graph, from_edgelist

from braket.annealing.problem import Problem
from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.circuits import Circuit
from braket.devices.device import Device


# TODO: deprecate
class AwsQpu(Device):
    """
    Amazon Braket implementation of a Quantum Processing Unit (QPU).
    Use this class to retrieve the latest metadata about the QPU, and to run a quantum task on the
    QPU.
    """

    QPU_REGIONS = {
        "rigetti": ["us-west-1"],
        "ionq": ["us-east-1"],
        "d-wave": ["us-west-2"],
    }

    DEFAULT_SHOTS_QPU = 1000
    DEFAULT_RESULTS_POLL_TIMEOUT_QPU = 432000
    DEFAULT_RESULTS_POLL_INTERVAL_QPU = 1

    def __init__(self, arn: str, aws_session=None):
        """
        Args:
            arn (str): The ARN of the QPU, for example, "arn:aws:aqx:::qpu:ionq"
            aws_session (AwsSession, optional) aws_session: An AWS session object. Default = None.

        Raises:
            ValueError: If an unknown `arn` is specified.

        Note:
            QPUs are physically located in specific AWS Regions. In some cases, the current
            `aws_session` connects to a Region other than the Region in which the QPU is
            physically located. When this occurs, a cloned `aws_session` is created for the Region
            the QPU is located in.

            See `braket.aws.aws_qpu.AwsQpu.QPU_REGIONS` for the AWS Regions the QPUs are located
            in.
        """
        super().__init__(name=None, status=None, status_reason=None)
        self._arn = arn
        self._aws_session = self._aws_session_for_qpu(arn, aws_session)
        self._properties = None
        self.refresh_metadata()

    def run(
        self,
        task_specification: Union[Circuit, Problem],
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: int = DEFAULT_SHOTS_QPU,
        poll_timeout_seconds: int = DEFAULT_RESULTS_POLL_TIMEOUT_QPU,
        poll_interval_seconds: int = DEFAULT_RESULTS_POLL_INTERVAL_QPU,
        *aws_quantum_task_args,
        **aws_quantum_task_kwargs,
    ) -> AwsQuantumTask:
        """
        Run a quantum task specification on this quantum device. A task can be a circuit or an
        annealing problem.

        Args:
            task_specification (Union[Circuit, Problem]):  Specification of task
                (circuit or annealing problem) to run on device.
            s3_destination_folder: The S3 location to save the task's results
            shots (int, optional): The number of times to run the circuit or annealing problem.
                Default is 1000.
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
            >>> device = AwsQpu("arn:aws:aqx:::qpu:rigetti")
            >>> device.run(circuit, ("bucket-foo", "key-bar"))

            >>> circuit = Circuit().h(0).cnot(0, 1)
            >>> device = AwsQpu("arn:aws:aqx:::qpu:rigetti")
            >>> device.run(task_specification=circuit,
            >>>     s3_destination_folder=("bucket-foo", "key-bar"))

            >>> problem = Problem(
            >>>     ProblemType.ISING,
            >>>     linear={1: 3.14},
            >>>     quadratic={(1, 2): 10.08},
            >>> )
            >>> device = AwsQpu("arn:aws:aqx:::qpu:d-wave")
            >>> device.run(problem, ("bucket-foo", "key-bar"),
            >>>     device_parameters = {"dWaveParameters": {"postprocessingType": "SAMPLING"}})

        See Also:
            `braket.aws.aws_quantum_task.AwsQuantumTask.create()`
        """

        # TODO: Restrict execution to compatible task types
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
        """
        Refresh the `AwsQpu` object with the most recent QPU metadata.
        """
        qpu_metadata = self._aws_session.get_qpu_metadata(self._arn)
        self._name = qpu_metadata.get("name")
        self._status = qpu_metadata.get("status")
        self._status_reason = qpu_metadata.get("statusReason")
        qpu_properties = qpu_metadata.get("properties")
        self._properties = (
            qpu_properties.get("annealingModelProperties", {}).get("dWaveProperties")
            if "annealingModelProperties" in qpu_properties
            else qpu_properties.get("gateModelProperties")
        )
        self._topology_graph = self._construct_topology_graph()

    @property
    def arn(self) -> str:
        """str: Return the ARN of the QPU"""
        return self._arn

    @property
    # TODO: Add a link to the boto3 docs
    def properties(self) -> Dict[str, Any]:
        """Dict[str, Any]: Return the QPU properties"""
        return self._properties

    @property
    def topology_graph(self) -> Graph:
        """Graph: topology of QPU as a networkx Graph object

        Examples:
            >>> import networkx as nx
            >>> device = AwsQpu("arn:aws:aqx:::qpu:rigetti")
            >>> nx.draw_kamada_kawai(device.topology_graph, with_labels=True, font_weight="bold")

            >>> topology_subgraph = device.topology_graph.subgraph(range(8))
            >>> nx.draw_kamada_kawai(topology_subgraph, with_labels=True, font_weight="bold")

            >>> print(device.topology_graph.edges)
        """
        return self._topology_graph

    def _construct_topology_graph(self) -> Graph:
        """
        Construct topology graph. If no such metadata is available, return None.

        Returns:
            Graph: topology of QPU as a networkx Graph object
        """
        if "connectivity" in self.properties:
            adjacency_lists = self.properties["connectivity"]["connectivityGraph"]
            edges = []
            for item in adjacency_lists.items():
                i = item[0]
                edges.extend([(int(i), int(j)) for j in item[1]])
            if len(edges) == 0:  # empty connectivity graph means fully connected
                return complete_graph(int(self.properties["qubitCount"]))
            else:
                return from_edgelist(edges)
        elif "couplers" in self.properties:
            edges = self.properties["couplers"]
            return from_edgelist(edges)
        else:
            return None

    def _aws_session_for_qpu(self, qpu_arn: str, aws_session: AwsSession) -> AwsSession:
        """
        Get an AwsSession for the QPU ARN. QPUs are physically located in specific AWS Regions.
        The AWS sessions should connect to the Region that the QPU is located in.

        See `braket.aws.aws_qpu.AwsQpu.QPU_REGIONS` for the AWS Regions the QPUs are located in.
        """
        region_key = qpu_arn.split("/")[-2]
        qpu_regions = AwsQpu.QPU_REGIONS.get(region_key, [])

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
