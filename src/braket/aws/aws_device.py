# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
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

import importlib
import json
import os
import urllib.request
import warnings
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Optional

from botocore.errorfactory import ClientError
from networkx import DiGraph, complete_graph, from_edgelist

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.aws.aws_quantum_task_batch import AwsQuantumTaskBatch
from braket.aws.aws_session import AwsSession
from braket.aws.queue_information import QueueDepthInfo, QueueType
from braket.circuits import Circuit, Gate, QubitSet
from braket.circuits.gate_calibrations import GateCalibrations
from braket.circuits.noise_model import NoiseModel
from braket.device_schema import DeviceCapabilities, ExecutionDay, GateModelQpuParadigmProperties
from braket.device_schema.dwave import DwaveProviderProperties

# TODO: Remove device_action module once this is added to init in the schemas repo
from braket.device_schema.pulse.pulse_device_action_properties_v1 import PulseDeviceActionProperties
from braket.devices.device import Device
from braket.ir.blackbird import Program as BlackbirdProgram
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.parametric.free_parameter import FreeParameter
from braket.parametric.free_parameter_expression import _is_float
from braket.pulse import ArbitraryWaveform, Frame, Port, PulseSequence
from braket.pulse.waveforms import _parse_waveform_from_calibration_schema
from braket.schema_common import BraketSchemaBase


class AwsDeviceType(str, Enum):
    """Possible AWS device types"""

    SIMULATOR = "SIMULATOR"
    QPU = "QPU"


class AwsDevice(Device):
    """Amazon Braket implementation of a device.
    Use this class to retrieve the latest metadata about the device and to run a quantum task on the
    device.
    """

    REGIONS = ("us-east-1", "us-west-1", "us-west-2", "eu-west-2", "eu-north-1")

    DEFAULT_SHOTS_QPU = 1000
    DEFAULT_SHOTS_SIMULATOR = 0
    DEFAULT_MAX_PARALLEL = 10

    _GET_DEVICES_ORDER_BY_KEYS = frozenset({"arn", "name", "type", "provider_name", "status"})

    _RIGETTI_GATES_TO_BRAKET: ClassVar[Optional[dict[str, str]]] = {
        # Rx_12 does not exist in the Braket SDK, it is a gate between |1> and |2>.
        "Rx_12": None,
        "Cz": "CZ",
        "Cphaseshift": "CPhaseShift",
        "Xy": "XY",
        "Iswap": "ISwap",
    }

    def __init__(
        self,
        arn: str,
        aws_session: Optional[AwsSession] = None,
        noise_model: Optional[NoiseModel] = None,
    ):
        """Initializes an `AwsDevice`.

        Args:
            arn (str): The ARN of the device
            aws_session (Optional[AwsSession]): An AWS session object. Default is `None`.
            noise_model (Optional[NoiseModel]): The Braket noise model to apply to the circuit
                before execution. Noise model can only be added to the devices that support
                noise simulation.

        Note:
            Some devices (QPUs) are physically located in specific AWS Regions. In some cases,
            the current `aws_session` connects to a Region other than the Region in which the QPU is
            physically located. When this occurs, a cloned `aws_session` is created for the Region
            the QPU is located in.

            See `braket.aws.aws_device.AwsDevice.REGIONS` for the AWS regions provider
            devices are located in across the AWS Braket service.
            This is not a device specific tuple.
        """
        super().__init__(name=None, status=None)
        self._arn = arn
        self._gate_calibrations = None
        self._properties = None
        self._provider_name = None
        self._poll_interval_seconds = None
        self._type = None
        self._aws_session = self._get_session_and_initialize(aws_session or AwsSession())
        self._ports = None
        self._frames = None
        if noise_model:
            self._validate_device_noise_model_support(noise_model)
        self._noise_model = noise_model

    def run(
        self,
        task_specification: Circuit
        | Problem
        | OpenQasmProgram
        | BlackbirdProgram
        | PulseSequence
        | AnalogHamiltonianSimulation,
        s3_destination_folder: Optional[AwsSession.S3DestinationFolder] = None,
        shots: Optional[int] = None,
        poll_timeout_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: Optional[float] = None,
        inputs: Optional[dict[str, float]] = None,
        gate_definitions: Optional[dict[tuple[Gate, QubitSet], PulseSequence]] = None,
        reservation_arn: Optional[str] = None,
        *aws_quantum_task_args: Any,
        **aws_quantum_task_kwargs: Any,
    ) -> AwsQuantumTask:
        """Run a quantum task specification on this device. A quantum task can be a circuit or an
        annealing problem.

        Args:
            task_specification (Union[Circuit, Problem, OpenQasmProgram, BlackbirdProgram, PulseSequence, AnalogHamiltonianSimulation]):
                Specification of quantum task (circuit, OpenQASM program or AHS program)
                to run on device.
            s3_destination_folder (Optional[S3DestinationFolder]): The S3 location to
                save the quantum task's results to. Default is `<default_bucket>/tasks` if evoked outside a
                Braket Hybrid Job, `<Job Bucket>/jobs/<job name>/tasks` if evoked inside a Braket Hybrid Job.
            shots (Optional[int]): The number of times to run the circuit or annealing problem.
                Default is 1000 for QPUs and 0 for simulators.
            poll_timeout_seconds (float): The polling timeout for `AwsQuantumTask.result()`,
                in seconds. Default: 5 days.
            poll_interval_seconds (Optional[float]): The polling interval for `AwsQuantumTask.result()`,
                in seconds. Defaults to the ``getTaskPollIntervalMillis`` value specified in
                ``self.properties.service`` (divided by 1000) if provided, otherwise 1 second.
            inputs (Optional[dict[str, float]]): Inputs to be passed along with the
                IR. If the IR supports inputs, the inputs will be updated with this value.
                Default: {}.
            gate_definitions (Optional[dict[tuple[Gate, QubitSet], PulseSequence]]): A
                `dict[tuple[Gate, QubitSet], PulseSequence]]` for a user defined gate calibration.
                The calibration is defined for a particular `Gate` on a particular `QubitSet`
                and is represented by a `PulseSequence`.
                Default: None.
            reservation_arn (str | None): The reservation ARN provided by Braket Direct
                to reserve exclusive usage for the device to run the quantum task on.
                Note: If you are creating tasks in a job that itself was created reservation ARN,
                those tasks do not need to be created with the reservation ARN.
                Default: None.
            *aws_quantum_task_args (Any): Arbitrary arguments.
            **aws_quantum_task_kwargs (Any): Arbitrary keyword arguments.

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

            >>> circuit = Circuit().h(0).cnot(0, 1)
            >>> device = AwsDevice("arn3")
            >>> device.run(task_specification=circuit,
            >>>     s3_destination_folder=("bucket-foo", "key-bar"), disable_qubit_rewiring=True)

            >>> problem = Problem(
            >>>     ProblemType.ISING,
            >>>     linear={1: 3.14},
            >>>     quadratic={(1, 2): 10.08},
            >>> )
            >>> device = AwsDevice("arn4")
            >>> device.run(problem, ("bucket-foo", "key-bar"),
            >>>     device_parameters={
            >>>         "providerLevelParameters": {"postprocessingType": "SAMPLING"}}
            >>> )

        See Also:
            `braket.aws.aws_quantum_task.AwsQuantumTask.create()`
        """  # noqa: E501
        if self._noise_model:
            task_specification = self._apply_noise_model_to_circuit(task_specification)
        return AwsQuantumTask.create(
            self._aws_session,
            self._arn,
            task_specification,
            s3_destination_folder
            or (
                AwsSession.parse_s3_uri(os.environ.get("AMZN_BRAKET_TASK_RESULTS_S3_URI"))
                if "AMZN_BRAKET_TASK_RESULTS_S3_URI" in os.environ
                else None
            )
            or (self._aws_session.default_bucket(), "tasks"),
            shots if shots is not None else self._default_shots,
            poll_timeout_seconds=poll_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds or self._poll_interval_seconds,
            inputs=inputs,
            gate_definitions=gate_definitions,
            reservation_arn=reservation_arn,
            *aws_quantum_task_args,
            **aws_quantum_task_kwargs,
        )

    def run_batch(
        self,
        task_specifications: Circuit
        | Problem
        | OpenQasmProgram
        | BlackbirdProgram
        | PulseSequence
        | AnalogHamiltonianSimulation
        | list[
            Circuit
            | Problem
            | OpenQasmProgram
            | BlackbirdProgram
            | PulseSequence
            | AnalogHamiltonianSimulation
        ],
        s3_destination_folder: Optional[AwsSession.S3DestinationFolder] = None,
        shots: Optional[int] = None,
        max_parallel: Optional[int] = None,
        max_connections: int = AwsQuantumTaskBatch.MAX_CONNECTIONS_DEFAULT,
        poll_timeout_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        inputs: Optional[dict[str, float] | list[dict[str, float]]] = None,
        gate_definitions: Optional[dict[tuple[Gate, QubitSet], PulseSequence]] = None,
        reservation_arn: Optional[str] = None,
        *aws_quantum_task_args,
        **aws_quantum_task_kwargs,
    ) -> AwsQuantumTaskBatch:
        """Executes a batch of quantum tasks in parallel

        Args:
            task_specifications (Union[Union[Circuit, Problem, OpenQasmProgram, BlackbirdProgram, PulseSequence, AnalogHamiltonianSimulation], list[Union[ Circuit, Problem, OpenQasmProgram, BlackbirdProgram, PulseSequence, AnalogHamiltonianSimulation]]]): # noqa
                Single instance or list of circuits, annealing problems, pulse sequences,
                or photonics program to run on device.
            s3_destination_folder (Optional[S3DestinationFolder]): The S3 location to
                save the quantum tasks' results to. Default is `<default_bucket>/tasks` if evoked outside a
                Braket Job, `<Job Bucket>/jobs/<job name>/tasks` if evoked inside a Braket Job.
            shots (Optional[int]): The number of times to run the circuit or annealing problem.
                Default is 1000 for QPUs and 0 for simulators.
            max_parallel (Optional[int]): The maximum number of quantum tasks to run on AWS in parallel.
                Batch creation will fail if this value is greater than the maximum allowed
                concurrent quantum tasks on the device. Default: 10
            max_connections (int): The maximum number of connections in the Boto3 connection pool.
                Also the maximum number of thread pool workers for the batch. Default: 100
            poll_timeout_seconds (float): The polling timeout for `AwsQuantumTask.result()`,
                in seconds. Default: 5 days.
            poll_interval_seconds (float): The polling interval for `AwsQuantumTask.result()`,
                in seconds. Defaults to the ``getTaskPollIntervalMillis`` value specified in
                ``self.properties.service`` (divided by 1000) if provided, otherwise 1 second.
            inputs (Optional[Union[dict[str, float], list[dict[str, float]]]]): Inputs to be
                passed along with the IR. If the IR supports inputs, the inputs will be updated
                with this value. Default: {}.
            gate_definitions (Optional[dict[tuple[Gate, QubitSet], PulseSequence]]): A
                `dict[tuple[Gate, QubitSet], PulseSequence]]` for a user defined gate calibration.
                The calibration is defined for a particular `Gate` on a particular `QubitSet`
                and is represented by a `PulseSequence`. Default: None.
            reservation_arn (Optional[str]): The reservation ARN provided by Braket Direct
                to reserve exclusive usage for the device to run the quantum task on.
                Note: If you are creating tasks in a job that itself was created reservation ARN,
                those tasks do not need to be created with the reservation ARN.
                Default: None.

        Returns:
            AwsQuantumTaskBatch: A batch containing all of the quantum tasks run

        See Also:
            `braket.aws.aws_quantum_task_batch.AwsQuantumTaskBatch`
        """  # noqa: E501
        if self._noise_model:
            task_specifications = [
                self._apply_noise_model_to_circuit(task_specification)
                for task_specification in task_specifications
            ]
        return AwsQuantumTaskBatch(
            AwsSession.copy_session(self._aws_session, max_connections=max_connections),
            self._arn,
            task_specifications,
            s3_destination_folder
            or (
                AwsSession.parse_s3_uri(os.environ.get("AMZN_BRAKET_TASK_RESULTS_S3_URI"))
                if "AMZN_BRAKET_TASK_RESULTS_S3_URI" in os.environ
                else None
            )
            or (self._aws_session.default_bucket(), "tasks"),
            shots if shots is not None else self._default_shots,
            max_parallel=max_parallel if max_parallel is not None else self._default_max_parallel,
            max_workers=max_connections,
            poll_timeout_seconds=poll_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds or self._poll_interval_seconds,
            inputs=inputs,
            gate_definitions=gate_definitions,
            reservation_arn=reservation_arn,
            *aws_quantum_task_args,
            **aws_quantum_task_kwargs,
        )

    def refresh_metadata(self) -> None:
        """Refresh the `AwsDevice` object with the most recent Device metadata."""
        self._populate_properties(self._aws_session)

    def _get_session_and_initialize(self, session: AwsSession) -> AwsSession:
        device_region = AwsDevice.get_device_region(self._arn)
        return (
            self._get_regional_device_session(session)
            if device_region
            else self._get_non_regional_device_session(session)
        )

    def _get_regional_device_session(self, session: AwsSession) -> AwsSession:
        device_region = AwsDevice.get_device_region(self._arn)
        region_session = (
            session
            if session.region == device_region
            else AwsSession.copy_session(session, device_region)
        )
        try:
            self._populate_properties(region_session)
        except ClientError as e:
            raise (
                ValueError(f"'{self._arn}' not found")
                if e.response["Error"]["Code"] == "ResourceNotFoundException"
                else e
            ) from e
        else:
            return region_session

    def _get_non_regional_device_session(self, session: AwsSession) -> AwsSession:
        current_region = session.region
        try:
            self._populate_properties(session)
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceNotFoundException":
                raise
            if "qpu" not in self._arn:
                raise ValueError(f"Simulator '{self._arn}' not found in '{current_region}'") from e
        else:
            return session
        # Search remaining regions for QPU
        for region in frozenset(AwsDevice.REGIONS) - {current_region}:
            region_session = AwsSession.copy_session(session, region)
            try:
                self._populate_properties(region_session)
            except ClientError as e:
                if e.response["Error"]["Code"] != "ResourceNotFoundException":
                    raise
            else:
                return region_session
        raise ValueError(f"QPU '{self._arn}' not found")

    def _populate_properties(self, session: AwsSession) -> None:
        metadata = session.get_device(self._arn)
        self._name = metadata.get("deviceName")
        self._status = metadata.get("deviceStatus")
        self._type = AwsDeviceType(metadata.get("deviceType"))
        self._provider_name = metadata.get("providerName")
        self._properties = BraketSchemaBase.parse_raw_schema(metadata.get("deviceCapabilities"))
        device_poll_interval = self._properties.service.getTaskPollIntervalMillis
        self._poll_interval_seconds = (
            device_poll_interval / 1000.0
            if device_poll_interval
            else AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL
        )
        self._topology_graph = None
        self._frames = None
        self._ports = None

    @property
    def type(self) -> str:
        """str: Return the device type"""
        return self._type

    @property
    def provider_name(self) -> str:
        """str: Return the provider name"""
        return self._provider_name

    @property
    def aws_session(self) -> AwsSession:
        return self._aws_session

    @property
    def arn(self) -> str:
        """str: Return the ARN of the device"""
        return self._arn

    @property
    def gate_calibrations(self) -> Optional[GateCalibrations]:
        """Calibration data for a QPU. Calibration data is shown for gates on particular gubits.
        If a QPU does not expose these calibrations, None is returned.

        Returns:
            Optional[GateCalibrations]: The calibration object. Returns `None` if the data
            is not present.
        """
        if not self._gate_calibrations:
            self._gate_calibrations = self.refresh_gate_calibrations()
        return self._gate_calibrations

    @property
    def is_available(self) -> bool:
        """Returns true if the device is currently available.

        Returns:
            bool: Return if the device is currently available.
        """
        if self.status != "ONLINE":
            return False

        is_available_result = False

        current_datetime_utc = datetime.now(tz=timezone.utc)
        for execution_window in self.properties.service.executionWindows:
            weekday = current_datetime_utc.weekday()
            current_time_utc = current_datetime_utc.time().replace(microsecond=0)

            if current_time_utc < execution_window.windowEndHour < execution_window.windowStartHour:
                weekday = (weekday - 1) % 7

            matched_day = execution_window.executionDay == ExecutionDay.EVERYDAY
            matched_day = matched_day or (
                execution_window.executionDay == ExecutionDay.WEEKDAYS and weekday < 5
            )
            matched_day = matched_day or (
                execution_window.executionDay == ExecutionDay.WEEKENDS and weekday > 4
            )
            ordered_days = (
                ExecutionDay.MONDAY,
                ExecutionDay.TUESDAY,
                ExecutionDay.WEDNESDAY,
                ExecutionDay.THURSDAY,
                ExecutionDay.FRIDAY,
                ExecutionDay.SATURDAY,
                ExecutionDay.SUNDAY,
            )
            matched_day = matched_day or (
                execution_window.executionDay in ordered_days
                and ordered_days.index(execution_window.executionDay) == weekday
            )

            matched_time = (
                execution_window.windowStartHour < execution_window.windowEndHour
                and execution_window.windowStartHour
                <= current_time_utc
                <= execution_window.windowEndHour
            ) or (
                execution_window.windowEndHour < execution_window.windowStartHour
                and (
                    current_time_utc >= execution_window.windowStartHour
                    or current_time_utc <= execution_window.windowEndHour
                )
            )

            is_available_result = is_available_result or (matched_day and matched_time)

        return is_available_result

    @property
    # TODO: Add a link to the boto3 docs
    def properties(self) -> DeviceCapabilities:
        """DeviceCapabilities: Return the device properties

        Please see `braket.device_schema` in amazon-braket-schemas-python_

        .. _amazon-braket-schemas-python: https://github.com/aws/amazon-braket-schemas-python
        """
        return self._properties

    @property
    def topology_graph(self) -> DiGraph:
        """DiGraph: topology of device as a networkx `DiGraph` object.

        Examples:
            >>> import networkx as nx
            >>> device = AwsDevice("arn1")
            >>> nx.draw_kamada_kawai(device.topology_graph, with_labels=True, font_weight="bold")

            >>> topology_subgraph = device.topology_graph.subgraph(range(8))
            >>> nx.draw_kamada_kawai(topology_subgraph, with_labels=True, font_weight="bold")

            >>> print(device.topology_graph.edges)

        Returns:
            DiGraph: topology of QPU as a networkx `DiGraph` object. `None` if the topology
            is not available for the device.
        """
        if not self._topology_graph:
            self._topology_graph = self._construct_topology_graph()
        return self._topology_graph

    def _construct_topology_graph(self) -> DiGraph:
        """Construct topology graph. If no such metadata is available, return `None`.

        Returns:
            DiGraph: topology of QPU as a networkx `DiGraph` object.
        """
        if hasattr(self.properties, "paradigm") and isinstance(
            self.properties.paradigm, GateModelQpuParadigmProperties
        ):
            if self.properties.paradigm.connectivity.fullyConnected:
                return complete_graph(
                    int(self.properties.paradigm.qubitCount), create_using=DiGraph()
                )
            adjacency_lists = self.properties.paradigm.connectivity.connectivityGraph
            edges = []
            for item in adjacency_lists.items():
                i = item[0]
                edges.extend([(int(i), int(j)) for j in item[1]])
            return from_edgelist(edges, create_using=DiGraph())
        if hasattr(self.properties, "provider") and isinstance(
            self.properties.provider, DwaveProviderProperties
        ):
            edges = self.properties.provider.couplers
            return from_edgelist(edges, create_using=DiGraph())
        return None

    @property
    def _default_shots(self) -> int:
        return (
            AwsDevice.DEFAULT_SHOTS_QPU if "qpu" in self.arn else AwsDevice.DEFAULT_SHOTS_SIMULATOR
        )

    @property
    def _default_max_parallel(self) -> int:
        return AwsDevice.DEFAULT_MAX_PARALLEL

    def __repr__(self):
        return f"Device('name': {self.name}, 'arn': {self.arn})"

    def __eq__(self, other: AwsDevice):
        if isinstance(other, AwsDevice):
            return self.arn == other.arn
        return NotImplemented

    @property
    def frames(self) -> dict[str, Frame]:
        """Returns a dict mapping frame ids to the frame objects for predefined frames
        for this device.
        """
        self._update_pulse_properties()
        return self._frames or {}

    @property
    def ports(self) -> dict[str, Port]:
        """Returns a dict mapping port ids to the port objects for predefined ports
        for this device.
        """
        self._update_pulse_properties()
        return self._ports or {}

    @staticmethod
    def get_devices(
        arns: Optional[list[str]] = None,
        names: Optional[list[str]] = None,
        types: Optional[list[AwsDeviceType]] = None,
        statuses: Optional[list[str]] = None,
        provider_names: Optional[list[str]] = None,
        order_by: str = "name",
        aws_session: Optional[AwsSession] = None,
    ) -> list[AwsDevice]:
        """Get devices based on filters and desired ordering. The result is the AND of
        all the filters `arns`, `names`, `types`, `statuses`, `provider_names`.

        Examples:
            >>> AwsDevice.get_devices(provider_names=["Rigetti"], statuses=["ONLINE"])
            >>> AwsDevice.get_devices(order_by="provider_name")
            >>> AwsDevice.get_devices(types=["SIMULATOR"])

        Args:
            arns (Optional[list[str]]): device ARN filter, default is `None`
            names (Optional[list[str]]): device name filter, default is `None`
            types (Optional[list[AwsDeviceType]]): device type filter, default is `None`
                QPUs will be searched for all regions and simulators will only be
                searched for the region of the current session.
            statuses (Optional[list[str]]): device status filter, default is `None`. When `None`
                is used, RETIRED devices will not be returned. To include RETIRED devices in
                the results, use a filter that includes "RETIRED" for this parameter.
            provider_names (Optional[list[str]]): provider name filter, default is `None`
            order_by (str): field to order result by, default is `name`.
                Accepted values are ['arn', 'name', 'type', 'provider_name', 'status']
            aws_session (Optional[AwsSession]): An AWS session object.
                Default is `None`.

        Raises:
            ValueError: order_by not in ['arn', 'name', 'type', 'provider_name', 'status']

        Returns:
            list[AwsDevice]: list of AWS devices
        """
        if order_by not in AwsDevice._GET_DEVICES_ORDER_BY_KEYS:
            raise ValueError(
                f"order_by '{order_by}' must be in {AwsDevice._GET_DEVICES_ORDER_BY_KEYS}"
            )
        types = frozenset(types or AwsDeviceType)
        aws_session = aws_session or AwsSession()
        device_map = {}
        session_region = aws_session.boto_session.region_name
        search_regions = (
            (session_region,) if types == {AwsDeviceType.SIMULATOR} else AwsDevice.REGIONS
        )
        for region in search_regions:
            session_for_region = (
                aws_session
                if region == session_region
                else AwsSession.copy_session(aws_session, region)
            )
            # Simulators are only instantiated in the same region as the AWS session
            types_for_region = sorted(
                types if region == session_region else types - {AwsDeviceType.SIMULATOR}
            )
            try:
                region_device_arns = [
                    result["deviceArn"]
                    for result in session_for_region.search_devices(
                        arns=arns,
                        names=names,
                        types=types_for_region,
                        statuses=statuses,
                        provider_names=provider_names,
                    )
                ]
                device_map |= {
                    arn: AwsDevice(arn, session_for_region)
                    for arn in region_device_arns
                    if arn not in device_map
                }
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                warnings.warn(
                    f"{error_code}: Unable to search region '{region}' for devices."
                    " Please check your settings or try again later."
                    f" Continuing without devices in '{region}'.",
                    stacklevel=1,
                )

        devices = list(device_map.values())
        devices.sort(key=lambda x: getattr(x, order_by))
        return devices

    def _update_pulse_properties(self) -> None:
        if not hasattr(self.properties, "pulse") or not isinstance(
            self.properties.pulse, PulseDeviceActionProperties
        ):
            return
        if self._ports is None:
            self._ports = {}
            port_data = self.properties.pulse.ports
            for port_id, port in port_data.items():
                self._ports[port_id] = Port(
                    port_id=port_id, dt=port.dt, properties=json.loads(port.json())
                )
        if self._frames is None:
            self._frames = {}
            if frame_data := self.properties.pulse.frames:
                for frame_id, frame in frame_data.items():
                    self._frames[frame_id] = Frame(
                        frame_id=frame_id,
                        port=self._ports[frame.portId],
                        frequency=frame.frequency,
                        phase=frame.phase,
                        is_predefined=True,
                        properties=json.loads(frame.json()),
                    )

    @staticmethod
    def get_device_region(device_arn: str) -> str:
        """Gets the region from a device arn.

        Args:
            device_arn (str): The device ARN.

        Raises:
            ValueError: Raised if the ARN is not properly formatted

        Returns:
            str: the region of the ARN.
        """
        try:
            return device_arn.split(":")[3]
        except IndexError as e:
            raise ValueError(
                f"Device ARN is not a valid format: {device_arn}. For valid Braket ARNs, "
                "see 'https://docs.aws.amazon.com/braket/latest/developerguide/braket-devices.html'"
            ) from e

    def queue_depth(self) -> QueueDepthInfo:
        """Task queue depth refers to the total number of quantum tasks currently waiting
        to run on a particular device.

        Returns:
            QueueDepthInfo: Instance of the QueueDepth class representing queue depth
            information for quantum tasks and hybrid jobs.
            Queue depth refers to the number of quantum tasks and hybrid jobs queued on a particular
            device. The normal tasks refers to the quantum tasks not submitted via Hybrid Jobs.
            Whereas, the priority tasks refers to the total number of quantum tasks waiting to run
            submitted through Amazon Braket Hybrid Jobs. These tasks run before the normal tasks.
            If the queue depth for normal or priority quantum tasks is greater than 4000, we display
            their respective queue depth as '>4000'. Similarly, for hybrid jobs if there are more
            than 1000 jobs queued on a device, display the hybrid jobs queue depth as '>1000'.
            Additionally, for QPUs if hybrid jobs queue depth is 0, we display information about
            priority and count of the running hybrid job.

        Example:
            Queue depth information for a running job.
            >>> device = AwsDevice(Device.Amazon.SV1)
            >>> print(device.queue_depth())
            QueueDepthInfo(quantum_tasks={<QueueType.NORMAL: 'Normal'>: '0',
            <QueueType.PRIORITY: 'Priority'>: '1'}, jobs='0 (1 prioritized job(s) running)')

            If more than 4000 quantum tasks queued on a device.
            >>> device = AwsDevice(Device.Amazon.DM1)
            >>> print(device.queue_depth())
            QueueDepthInfo(quantum_tasks={<QueueType.NORMAL: 'Normal'>: '>4000',
            <QueueType.PRIORITY: 'Priority'>: '2000'}, jobs='100')
        """
        metadata = self.aws_session.get_device(arn=self.arn)
        queue_metadata = metadata.get("deviceQueueInfo")
        queue_info = {}

        for response in queue_metadata:
            queue_name = response.get("queue")
            queue_priority = response.get("queuePriority")
            queue_size = response.get("queueSize")

            if queue_name == "QUANTUM_TASKS_QUEUE":
                priority_enum = QueueType(queue_priority)
                queue_info.setdefault("quantum_tasks", {})[priority_enum] = queue_size
            else:
                queue_info["jobs"] = queue_size

        return QueueDepthInfo(**queue_info)

    def refresh_gate_calibrations(self) -> Optional[GateCalibrations]:
        """Refreshes the gate calibration data upon request.

        If the device does not have calibration data, None is returned.

        Raises:
            URLError: If the URL provided returns a non 2xx response.

        Returns:
            Optional[GateCalibrations]: the calibration data for the device. None
            is returned if the device does not have a gate calibrations URL associated.
        """
        if (
            hasattr(self.properties, "pulse")
            and hasattr(self.properties.pulse, "nativeGateCalibrationsRef")
            and self.properties.pulse.nativeGateCalibrationsRef
        ):
            try:
                with urllib.request.urlopen(  # noqa: S310
                    self.properties.pulse.nativeGateCalibrationsRef.split("?")[0]
                ) as f:
                    json_calibration_data = self._parse_calibration_json(
                        json.loads(f.read().decode("utf-8"))
                    )
                    return GateCalibrations(json_calibration_data)
            except urllib.error.URLError as e:
                raise urllib.error.URLError(
                    f"Unable to reach {self.properties.pulse.nativeGateCalibrationsRef}"
                ) from e
        else:
            return None

    def _parse_waveforms(self, waveforms_json: dict) -> dict:
        waveforms = {}
        for waveform in waveforms_json.values():
            parsed_waveform = _parse_waveform_from_calibration_schema(waveform)
            waveforms[parsed_waveform.id] = parsed_waveform
        return waveforms

    def _parse_pulse_sequence(
        self, calibration: dict, waveforms: dict[ArbitraryWaveform]
    ) -> PulseSequence:
        return PulseSequence._parse_from_calibration_schema(calibration, waveforms, self.frames)

    def _parse_calibration_json(
        self, calibration_data: dict
    ) -> dict[tuple[Gate, QubitSet], PulseSequence]:
        """Takes the json string from the device calibration URL and returns a structured dictionary of
        corresponding `dict[tuple[Gate, QubitSet], PulseSequence]` to represent the calibration data.

        Args:
            calibration_data (dict): The data to be parsed. Based on
                https://github.com/aws/amazon-braket-schemas-python/blob/main/src/braket/device_schema/pulse/native_gate_calibrations_v1.py.

        Returns:
            dict[tuple[Gate, QubitSet], PulseSequence]: The
            structured data based on a mapping of `tuple[Gate, Qubit]` to its calibration represented as a
            `PulseSequence`.

        """  # noqa: E501
        waveforms = self._parse_waveforms(calibration_data["waveforms"])
        parsed_calibration_data = {}
        for qubit_node in calibration_data["gates"]:
            qubit = calibration_data["gates"][qubit_node]
            for gate_node in qubit:
                for gate in qubit[gate_node]:
                    gate_capitalized = getattr(
                        self,
                        f"_{self.provider_name.upper()}_GATES_TO_BRAKET",
                        {},
                    ).get(gate_node.capitalize(), gate_node.capitalize())
                    gate_obj = (
                        getattr(importlib.import_module("braket.circuits.gates"), gate_capitalized)
                        if gate_capitalized is not None
                        else None
                    )
                    qubits = QubitSet([int(x) for x in gate["qubits"]])
                    if gate_obj is None:
                        # We drop out gates that are not implemented in the BDK
                        continue

                    argument = None
                    if gate["arguments"]:
                        argument = (
                            float(gate["arguments"][0])
                            if _is_float(gate["arguments"][0])
                            else FreeParameter(gate["arguments"][0])
                        )
                    gate_qubit_key = (
                        (gate_obj(argument), qubits) if argument else (gate_obj(), qubits)
                    )
                    gate_qubit_pulse = self._parse_pulse_sequence(gate["calibrations"], waveforms)
                    parsed_calibration_data[gate_qubit_key] = gate_qubit_pulse

        return parsed_calibration_data
