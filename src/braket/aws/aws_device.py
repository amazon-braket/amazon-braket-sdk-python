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

from enum import Enum
from typing import List, Optional, Set, Union

import boto3
from boltons.dictutils import FrozenDict
from networkx import Graph, complete_graph, from_edgelist

from braket.annealing.problem import Problem
from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.circuits import Circuit
from braket.device_schema import DeviceCapabilities, GateModelQpuParadigmProperties
from braket.device_schema.dwave import DwaveProviderProperties
from braket.devices.device import Device
from braket.schema_common import BraketSchemaBase


class AwsDeviceType(str, Enum):
    """Possible AWS device types"""

    SIMULATOR = "SIMULATOR"
    QPU = "QPU"


class AwsDevice(Device):
    """
    Amazon Braket implementation of a device.
    Use this class to retrieve the latest metadata about the device and to run a quantum task on the
    device.
    """

    DEVICE_REGIONS = FrozenDict(
        {
            "rigetti": ["us-west-1"],
            "ionq": ["us-east-1"],
            "d-wave": ["us-west-2"],
            "amazon": ["us-west-2", "us-west-1", "us-east-1"],
        }
    )

    DEFAULT_SHOTS_QPU = 1000
    DEFAULT_SHOTS_SIMULATOR = 0
    DEFAULT_RESULTS_POLL_TIMEOUT = 432000
    DEFAULT_RESULTS_POLL_INTERVAL = 1

    def __init__(self, arn: str, aws_session: Optional[AwsSession] = None):
        """
        Args:
            arn (str): The ARN of the device
            aws_session (AwsSession, optional) aws_session: An AWS session object. Default = None.

        Note:
            Some devices (QPUs) are physically located in specific AWS Regions. In some cases,
            the current `aws_session` connects to a Region other than the Region in which the QPU is
            physically located. When this occurs, a cloned `aws_session` is created for the Region
            the QPU is located in.

            See `braket.aws.aws_device.AwsDevice.DEVICE_REGIONS` for the AWS Regions provider
            devices are located in.
        """
        super().__init__(name=None, status=None)
        self._arn = arn
        self._aws_session = AwsDevice._aws_session_for_device(arn, aws_session)
        self._properties = None
        self._provider_name = None
        self._type = None
        self.refresh_metadata()

    def run(
        self,
        task_specification: Union[Circuit, Problem],
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: Optional[int] = None,
        poll_timeout_seconds: Optional[int] = DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: Optional[int] = DEFAULT_RESULTS_POLL_INTERVAL,
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
            >>>     device_parameters={
            >>>         "providerLevelParameters": {"postprocessingType": "SAMPLING"}}
            >>> )

        See Also:
            `braket.aws.aws_quantum_task.AwsQuantumTask.create()`
        """
        if shots is None:
            if "qpu" in self.arn:
                shots = AwsDevice.DEFAULT_SHOTS_QPU
            else:
                shots = AwsDevice.DEFAULT_SHOTS_SIMULATOR
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
        Refresh the `AwsDevice` object with the most recent Device metadata.
        """
        metadata = self._aws_session.get_device(self._arn)
        self._name = metadata.get("deviceName")
        self._status = metadata.get("deviceStatus")
        self._type = AwsDeviceType(metadata.get("deviceType"))
        self._provider_name = metadata.get("providerName")
        qpu_properties = metadata.get("deviceCapabilities")
        self._properties = BraketSchemaBase.parse_raw_schema(qpu_properties)
        self._topology_graph = self._construct_topology_graph()

    @property
    def type(self) -> str:
        """str: Return the device type"""
        return self._type

    @property
    def provider_name(self) -> str:
        """str: Return the provider name"""
        return self._provider_name

    @property
    def arn(self) -> str:
        """str: Return the ARN of the device"""
        return self._arn

    @property
    # TODO: Add a link to the boto3 docs
    def properties(self) -> DeviceCapabilities:
        """DeviceCapabilities: Return the device properties

        Please see `braket.device_schema` in amazon-braket-schemas-python_

        .. _amazon-braket-schemas-python: https://github.com/aws/amazon-braket-schemas-python"""
        return self._properties

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
        return self._topology_graph

    def _construct_topology_graph(self) -> Graph:
        """
        Construct topology graph. If no such metadata is available, return None.

        Returns:
            Graph: topology of QPU as a networkx Graph object
        """
        if hasattr(self.properties, "paradigm") and isinstance(
            self.properties.paradigm, GateModelQpuParadigmProperties
        ):
            if self.properties.paradigm.connectivity.fullyConnected:
                return complete_graph(int(self.properties.paradigm.qubitCount))
            adjacency_lists = self.properties.paradigm.connectivity.connectivityGraph
            edges = []
            for item in adjacency_lists.items():
                i = item[0]
                edges.extend([(int(i), int(j)) for j in item[1]])
            return from_edgelist(edges)
        elif hasattr(self.properties, "provider") and isinstance(
            self.properties.provider, DwaveProviderProperties
        ):
            edges = self.properties.provider.couplers
            return from_edgelist(edges)
        else:
            return None

    @staticmethod
    def _aws_session_for_device(device_arn: str, aws_session: Optional[AwsSession]) -> AwsSession:
        """AwsSession: Returns an AwsSession for the device ARN. """
        if "qpu" in device_arn:
            return AwsDevice._aws_session_for_qpu(device_arn, aws_session)
        else:
            return aws_session or AwsSession()

    @staticmethod
    def _aws_session_for_qpu(device_arn: str, aws_session: Optional[AwsSession]) -> AwsSession:
        """
        Get an AwsSession for the device ARN. QPUs are physically located in specific AWS Regions.
        The AWS sessions should connect to the Region that the QPU is located in.

        See `braket.aws.aws_qpu.AwsDevice.DEVICE_REGIONS` for the
        AWS Regions the devices are located in.
        """
        region_key = device_arn.split("/")[-2]
        qpu_regions = AwsDevice.DEVICE_REGIONS.get(region_key, [])
        return AwsDevice._copy_aws_session(aws_session, qpu_regions)

    @staticmethod
    def _copy_aws_session(aws_session: Optional[AwsSession], regions: List[str]) -> AwsSession:
        if aws_session:
            if aws_session.boto_session.region_name in regions:
                return aws_session
            else:
                creds = aws_session.boto_session.get_credentials()
                boto_session = boto3.Session(
                    aws_access_key_id=creds.access_key,
                    aws_secret_access_key=creds.secret_key,
                    aws_session_token=creds.token,
                    region_name=regions[0],
                )
                return AwsSession(boto_session=boto_session)
        else:
            boto_session = boto3.Session(region_name=regions[0])
            return AwsSession(boto_session=boto_session)

    def __repr__(self):
        return "Device('name': {}, 'arn': {})".format(self.name, self.arn)

    def __eq__(self, other):
        if isinstance(other, AwsDevice):
            return self.arn == other.arn
        return NotImplemented

    @staticmethod
    def get_devices(
        arns: Optional[List[str]] = None,
        names: Optional[List[str]] = None,
        types: Optional[List[AwsDeviceType]] = None,
        statuses: Optional[List[str]] = None,
        provider_names: Optional[List[str]] = None,
        order_by: str = "name",
        aws_session: Optional[AwsSession] = None,
    ) -> List[AwsDevice]:
        """
        Get devices based on filters and desired ordering. The result is the AND of
        all the filters `arns`, `names`, `types`, `statuses`, `provider_names`.

        Examples:
            >>> AwsDevice.get_devices(provider_names=['Rigetti'], statuses=['ONLINE'])
            >>> AwsDevice.get_devices(order_by='provider_name')
            >>> AwsDevice.get_devices(types=['SIMULATOR'])

        Args:
            arns (List[str], optional): device ARN list, default is `None`
            names (List[str], optional): device name list, default is `None`
            types (List[AwsDeviceType], optional): device type list, default is `None`
            statuses (List[str], optional): device status list, default is `None`
            provider_names (List[str], optional): provider name list, default is `None`
            order_by (str, optional): field to order result by, default is `name`.
                Accepted values are ['arn', 'name', 'type', 'provider_name', 'status']
            aws_session (AwsSession, optional) aws_session: An AWS session object. Default = None.

        Returns:
            List[AwsDevice]: list of AWS devices
        """
        order_by_list = ["arn", "name", "type", "provider_name", "status"]
        if order_by not in order_by_list:
            raise ValueError(f"order_by '{order_by}' must be in {order_by_list}")
        device_regions_set = AwsDevice._get_devices_regions_set(arns, provider_names, types)
        results = []
        for region in device_regions_set:
            aws_session = AwsDevice._copy_aws_session(aws_session, [region])
            results.extend(
                aws_session.search_devices(
                    arns=arns,
                    names=names,
                    types=types,
                    statuses=statuses,
                    provider_names=provider_names,
                )
            )
        arns = set([result["deviceArn"] for result in results])
        devices = [AwsDevice(arn, aws_session) for arn in arns]
        devices.sort(key=lambda x: getattr(x, order_by))
        return devices

    @staticmethod
    def _get_devices_regions_set(
        arns: Optional[List[str]],
        provider_names: Optional[List[str]],
        types: Optional[List[AwsDeviceType]],
    ) -> Set[str]:
        """Get the set of regions to call `SearchDevices` API given filters"""
        device_regions_set = set(
            AwsDevice.DEVICE_REGIONS[key][0] for key in AwsDevice.DEVICE_REGIONS
        )
        if provider_names:
            provider_region_set = set()
            for provider in provider_names:
                for key in AwsDevice.DEVICE_REGIONS:
                    if key in provider.lower():
                        provider_region_set.add(AwsDevice.DEVICE_REGIONS[key][0])
                        break
            device_regions_set = device_regions_set.intersection(provider_region_set)
        if arns:
            arns_region_set = set([AwsDevice.DEVICE_REGIONS[arn.split("/")[-2]][0] for arn in arns])
            device_regions_set = device_regions_set.intersection(arns_region_set)
        if types and types == [AwsDeviceType.SIMULATOR]:
            device_regions_set = device_regions_set.intersection(
                [AwsDevice.DEVICE_REGIONS["amazon"][0]]
            )
        return device_regions_set
