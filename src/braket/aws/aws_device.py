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
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from botocore.errorfactory import ClientError
from networkx import DiGraph, complete_graph, from_edgelist

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.aws.aws_quantum_task import AwsQuantumTask
from braket.aws.aws_quantum_task_batch import AwsQuantumTaskBatch
from braket.aws.aws_session import AwsSession
from braket.circuits import Circuit, Gate, QubitSet
from braket.device_schema import DeviceCapabilities, ExecutionDay, GateModelQpuParadigmProperties
from braket.device_schema.dwave import DwaveProviderProperties
from braket.device_schema.pulse.pulse_device_action_properties_v1 import (  # noqa TODO: Remove device_action module once this is added to init in the schemas repo
    PulseDeviceActionProperties,
)
from braket.devices.device import Device
from braket.ir.blackbird import Program as BlackbirdProgram
from braket.ir.openqasm import Program as OpenQasmProgram
from braket.native_gates.native_gate_calibration import NativeGateCalibration
from braket.parametric.free_parameter import FreeParameter
from braket.pulse import (
    ArbitraryWaveform,
    ConstantWaveform,
    DragGaussianWaveform,
    Frame,
    GaussianWaveform,
    Port,
    PulseSequence,
)
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

    REGIONS = ("us-east-1", "us-west-1", "us-west-2", "eu-west-2")

    DEFAULT_SHOTS_QPU = 1000
    DEFAULT_SHOTS_SIMULATOR = 0
    DEFAULT_MAX_PARALLEL = 10

    _GET_DEVICES_ORDER_BY_KEYS = frozenset({"arn", "name", "type", "provider_name", "status"})

    def __init__(self, arn: str, aws_session: Optional[AwsSession] = None):
        """
        Args:
            arn (str): The ARN of the device
            aws_session (Optional[AwsSession]): An AWS session object. Default is `None`.

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
        self._native_gate_calibration = None
        self._native_gate_calibration_timestamp = None
        self._properties = None
        self._provider_name = None
        self._poll_interval_seconds = None
        self._type = None
        self._aws_session = self._get_session_and_initialize(aws_session or AwsSession())
        self._ports = None
        self._frames = None

    def run(
        self,
        task_specification: Union[
            Circuit,
            Problem,
            OpenQasmProgram,
            BlackbirdProgram,
            PulseSequence,
            AnalogHamiltonianSimulation,
        ],
        s3_destination_folder: Optional[AwsSession.S3DestinationFolder] = None,
        shots: Optional[int] = None,
        poll_timeout_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: Optional[float] = None,
        inputs: Optional[Dict[str, float]] = None,
        native_gate_calibration: Optional[NativeGateCalibration] = None,
        *aws_quantum_task_args,
        **aws_quantum_task_kwargs,
    ) -> AwsQuantumTask:
        """
        Run a quantum task specification on this device. A task can be a circuit or an
        annealing problem.

        Args:
            task_specification (Union[Circuit, Problem, OpenQasmProgram, BlackbirdProgram, PulseSequence, AnalogHamiltonianSimulation]): # noqa
                Specification of task (circuit or annealing problem or program) to run on device.
            s3_destination_folder (Optional[S3DestinationFolder]): The S3 location to
                save the task's results to. Default is `<default_bucket>/tasks` if evoked outside a
                Braket Job, `<Job Bucket>/jobs/<job name>/tasks` if evoked inside a Braket Job.
            shots (Optional[int]): The number of times to run the circuit or annealing problem.
                Default is 1000 for QPUs and 0 for simulators.
            poll_timeout_seconds (float): The polling timeout for `AwsQuantumTask.result()`,
                in seconds. Default: 5 days.
            poll_interval_seconds (Optional[float]): The polling interval for `AwsQuantumTask.result()`,
                in seconds. Defaults to the ``getTaskPollIntervalMillis`` value specified in
                ``self.properties.service`` (divided by 1000) if provided, otherwise 1 second.
            inputs (Optional[Dict[str, float]]): Inputs to be passed along with the
                IR. If the IR supports inputs, the inputs will be updated with this value.
                Default: {}.
            native_gate_calibration (Optional[NativeGateCalibration]): A `NativeGateCalibration` for user defined gate
                calibration.

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
        """
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
            native_gate_calibration=native_gate_calibration,
            *aws_quantum_task_args,
            **aws_quantum_task_kwargs,
        )

    def run_batch(
        self,
        task_specifications: Union[
            Union[
                Circuit,
                Problem,
                OpenQasmProgram,
                BlackbirdProgram,
                PulseSequence,
                AnalogHamiltonianSimulation,
            ],
            List[
                Union[
                    Circuit,
                    Problem,
                    OpenQasmProgram,
                    BlackbirdProgram,
                    PulseSequence,
                    AnalogHamiltonianSimulation,
                ]
            ],
        ],
        s3_destination_folder: Optional[AwsSession.S3DestinationFolder] = None,
        shots: Optional[int] = None,
        max_parallel: Optional[int] = None,
        max_connections: int = AwsQuantumTaskBatch.MAX_CONNECTIONS_DEFAULT,
        poll_timeout_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
        poll_interval_seconds: float = AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
        inputs: Optional[Union[Dict[str, float], List[Dict[str, float]]]] = None,
        native_gate_calibration: Optional[NativeGateCalibration] = None,
        *aws_quantum_task_args,
        **aws_quantum_task_kwargs,
    ) -> AwsQuantumTaskBatch:
        """Executes a batch of tasks in parallel

        Args:
            task_specifications (Union[Union[Circuit, Problem, OpenQasmProgram, BlackbirdProgram, PulseSequence, AnalogHamiltonianSimulation], List[Union[ Circuit, Problem, OpenQasmProgram, BlackbirdProgram, PulseSequence, AnalogHamiltonianSimulation]]]): # noqa
                Single instance or list of circuits, annealing problems, pulse sequences,
                or photonics program to run on device.
            s3_destination_folder (Optional[S3DestinationFolder]): The S3 location to
                save the tasks' results to. Default is `<default_bucket>/tasks` if evoked outside a
                Braket Job, `<Job Bucket>/jobs/<job name>/tasks` if evoked inside a Braket Job.
            shots (Optional[int]): The number of times to run the circuit or annealing problem.
                Default is 1000 for QPUs and 0 for simulators.
            max_parallel (Optional[int]): The maximum number of tasks to run on AWS in parallel.
                Batch creation will fail if this value is greater than the maximum allowed
                concurrent tasks on the device. Default: 10
            max_connections (int): The maximum number of connections in the Boto3 connection pool.
                Also the maximum number of thread pool workers for the batch. Default: 100
            poll_timeout_seconds (float): The polling timeout for `AwsQuantumTask.result()`,
                in seconds. Default: 5 days.
            poll_interval_seconds (float): The polling interval for `AwsQuantumTask.result()`,
                in seconds. Defaults to the ``getTaskPollIntervalMillis`` value specified in
                ``self.properties.service`` (divided by 1000) if provided, otherwise 1 second.
            inputs (Optional[Union[Dict[str, float], List[Dict[str, float]]]]): Inputs to be
                passed along with the IR. If the IR supports inputs, the inputs will be updated
                with this value. Default: {}.
            native_gate_calibration (Optional[NativeGateCalibration]): A `NativeGateCalibration` for user defined gate
                calibration.

        Returns:
            AwsQuantumTaskBatch: A batch containing all of the tasks run

        See Also:
            `braket.aws.aws_quantum_task_batch.AwsQuantumTaskBatch`
        """
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
            native_gate_calibration=native_gate_calibration,
            *aws_quantum_task_args,
            **aws_quantum_task_kwargs,
        )

    def refresh_metadata(self) -> None:
        """
        Refresh the `AwsDevice` object with the most recent Device metadata.
        """
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
            return region_session
        except ClientError as e:
            raise ValueError(f"'{self._arn}' not found") if e.response["Error"][
                "Code"
            ] == "ResourceNotFoundException" else e

    def _get_non_regional_device_session(self, session: AwsSession) -> AwsSession:
        current_region = session.region
        try:
            self._populate_properties(session)
            return session
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                if "qpu" not in self._arn:
                    raise ValueError(f"Simulator '{self._arn}' not found in '{current_region}'")
            else:
                raise e
        # Search remaining regions for QPU
        for region in frozenset(AwsDevice.REGIONS) - {current_region}:
            region_session = AwsSession.copy_session(session, region)
            try:
                self._populate_properties(region_session)
                return region_session
            except ClientError as e:
                if e.response["Error"]["Code"] != "ResourceNotFoundException":
                    raise e
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
    def native_gate_calibration(self) -> NativeGateCalibration:
        """
        Fetches the native gate calibration data if not already present.

        Returns:
            NativeGateCalibration: The calibration object.
        """
        if not self._native_gate_calibration:
            self._native_gate_calibration = self.refresh_native_gate_calibrations()
        return self._native_gate_calibration

    @property
    def native_gate_calibration_timestamp(self) -> datetime:
        """
        This returns the timestamp of the last time the calibration data was fetched.

        Returns:
            datetime: The timestamp for the last time the calibration was fetched.
        """
        return self.native_gate_calibration_timestamp

    @property
    def native_gate_calibration_href(self) -> str:
        """
        Returns the href for the native gate calibration data is the device has it.
        """
        if hasattr(self.properties, "nativeGateCalibrationsRef"):
            return self.properties.nativeGateCalibrationsRef
        else:
            return None

    @property
    def is_available(self) -> bool:
        """Returns true if the device is currently available.
        Returns:
            bool: Return if the device is currently available.
        """
        if self.status != "ONLINE":
            return False

        is_available_result = False

        current_datetime_utc = datetime.utcnow()
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

        .. _amazon-braket-schemas-python: https://github.com/aws/amazon-braket-schemas-python"""
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
        """
        Construct topology graph. If no such metadata is available, return `None`.

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
        elif hasattr(self.properties, "provider") and isinstance(
            self.properties.provider, DwaveProviderProperties
        ):
            edges = self.properties.provider.couplers
            return from_edgelist(edges, create_using=DiGraph())
        else:
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
        return "Device('name': {}, 'arn': {})".format(self.name, self.arn)

    def __eq__(self, other):
        if isinstance(other, AwsDevice):
            return self.arn == other.arn
        return NotImplemented

    @property
    def frames(self) -> Dict[str, Frame]:
        """Returns a Dict mapping frame ids to the frame objects for predefined frames
        for this device."""
        self._update_pulse_properties()
        return self._frames or dict()

    @property
    def ports(self) -> Dict[str, Port]:
        """Returns a Dict mapping port ids to the port objects for predefined ports
        for this device."""
        self._update_pulse_properties()
        return self._ports or dict()

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
            arns (Optional[List[str]]): device ARN list, default is `None`
            names (Optional[List[str]]): device name list, default is `None`
            types (Optional[List[AwsDeviceType]]): device type list, default is `None`
                QPUs will be searched for all regions and simulators will only be
                searched for the region of the current session.
            statuses (Optional[List[str]]): device status list, default is `None`
            provider_names (Optional[List[str]]): provider name list, default is `None`
            order_by (str): field to order result by, default is `name`.
                Accepted values are ['arn', 'name', 'type', 'provider_name', 'status']
            aws_session (Optional[AwsSession]): An AWS session object.
                Default is `None`.

        Returns:
            List[AwsDevice]: list of AWS devices
        """

        if order_by not in AwsDevice._GET_DEVICES_ORDER_BY_KEYS:
            raise ValueError(
                f"order_by '{order_by}' must be in {AwsDevice._GET_DEVICES_ORDER_BY_KEYS}"
            )
        types = (
            frozenset(types) if types else frozenset({device_type for device_type in AwsDeviceType})
        )
        aws_session = aws_session if aws_session else AwsSession()
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
            device_map.update(
                {
                    arn: AwsDevice(arn, session_for_region)
                    for arn in region_device_arns
                    if arn not in device_map
                }
            )
        devices = list(device_map.values())
        devices.sort(key=lambda x: getattr(x, order_by))
        return devices

    def _update_pulse_properties(self) -> None:
        if hasattr(self.properties, "pulse") and isinstance(
            self.properties.pulse, PulseDeviceActionProperties
        ):
            if self._ports is None:
                self._ports = dict()
                port_data = self.properties.pulse.ports
                for port_id, port in port_data.items():
                    self._ports[port_id] = Port(
                        port_id=port_id, dt=port.dt, properties=json.loads(port.json())
                    )
            if self._frames is None:
                self._frames = dict()
                frame_data = self.properties.pulse.frames
                if frame_data:
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

        Returns:
            str: the region of the ARN.
        """
        try:
            return device_arn.split(":")[3]
        except IndexError:
            raise ValueError(
                f"Device ARN is not a valid format: {device_arn}. For valid Braket ARNs, "
                "see 'https://docs.aws.amazon.com/braket/latest/developerguide/braket-devices.html'"
            )

    def refresh_native_gate_calibrations(self) -> PulseSequence:
        """
        Refreshes the native gate calibration data upon request.

        If the device does not have calibration data, None is returned.

        Returns:
            PulseSequence: the calibration data for the device from the specific time.
        """
        if hasattr(self.properties, "nativeGateCalibrationsRef"):
            try:
                with urllib.request.urlopen(self.properties.nativeGateCalibrationsRef) as f:
                    json_calibration_data, fidelities = self._parse_calibration_json(
                        json.loads(f.read().decode("utf-8"))
                    )
                    self._native_gate_calibration_timestamp = datetime.now()
                    return NativeGateCalibration(json_calibration_data, fidelities)
            except urllib.error.URLError as e:
                print(e.reason)
        else:
            return None

    def _parse_waveforms(self, waveforms_json: str) -> Dict:
        waveforms = dict()
        for waveform in waveforms_json:
            w = waveforms_json[waveform]
            wave_id = w["waveformId"]
            waveform_parameters = {"id": wave_id}
            if "amplitudes" in w.keys():
                complex_amplitudes = [complex(i[0], i[1]) for i in w["amplitudes"]]
                waveforms[wave_id] = ArbitraryWaveform(complex_amplitudes, wave_id)
            elif w["name"] == "drag_gaussian":
                waveform_parameters |= {
                    val["name"]: float(val["value"])
                    if is_float(val["value"])
                    else FreeParameter(val["value"])
                    for val in w["arguments"]
                }
                waveforms[wave_id] = DragGaussianWaveform(**waveform_parameters)
            elif w["name"] == "gaussian":
                waveform_parameters |= {
                    val["name"]: float(val["value"])
                    if is_float(val["value"])
                    else FreeParameter(val["value"])
                    for val in w["arguments"]
                }
                waveforms[wave_id] = GaussianWaveform(**waveform_parameters)
            elif w["name"] == "constant":
                length = iq = None
                for val in arguments:
                    if val["name"] == "length":
                        length = (
                            float(val["value"])
                            if is_float(val["value"])
                            else FreeParameter(val["value"])
                        )
                    if val["name"] == "iq":
                        iq = (
                            complex(val["value"])
                            if is_float(val["value"])
                            else FreeParameter(val["value"])
                        )
                waveforms[wave_id] = ConstantWaveform(length, iq)
            else:
                raise ValueError(f"The waveform {wave_id} of cannot be constructed")
            waveforms[wave_id]._autodeclare(False)
        return waveforms

    def _get_pulse_sequence(
        self, calibration: str, waveforms: Dict[ArbitraryWaveform]
    ) -> PulseSequence:
        calibration_sequence = PulseSequence()
        for instruction in range(len(calibration)):
            instr = calibration[instruction]
            if instr["name"] == "barrier":
                if instr["arguments"] is not None:
                    if instr["arguments"][0]["name"] == "qubit":
                        qubits_or_frames = QubitSet(
                            [int(arg["value"]) for arg in instr["arguments"]]
                        )
                    else:
                        qubits_or_frames = [
                            self.frames.get(arg["value"]) for arg in instr["arguments"]
                        ]
                else:
                    qubits_or_frames = []
                calibration_sequence = calibration_sequence.barrier(qubits_or_frames)
            elif instr["name"] == "play":
                frame = waveform = None
                for argument in instr["arguments"]:
                    if argument["name"] == "frame":
                        frame = self.frames[argument["value"]]
                    elif argument["name"] == "waveform":
                        waveform = waveforms[argument["value"]]
                calibration_sequence = calibration_sequence.play(frame, waveform)
            elif instr["name"] == "delay":
                frames = list()
                duration = None
                for i in range(len(instr["arguments"])):
                    if instr["arguments"][i]["name"] == "frame":
                        f = "_".join(instr["arguments"][i]["value"].split("_")[:-1]) + "_frame"
                        frames.append(self.frames[f])
                    elif instr["arguments"][i]["name"] == "duration":
                        duration = (
                            float(instr["arguments"][i]["value"])
                            if is_float(instr["arguments"][i]["value"])
                            else FreeParameter(instr["arguments"][i]["value"])
                        )
                calibration_sequence = calibration_sequence.delay(frames, duration)
            elif instr["name"] == "shift_phase":
                frame = phase = None
                for argument in instr["arguments"]:
                    if argument["name"] == "frame":
                        f = "_".join(argument["value"].split("_")[:-1]) + "_frame"
                        frame = self.frames[f]
                    elif argument["name"] == "phase":
                        phase = (
                            float(argument["value"])
                            if is_float(argument["value"])
                            else FreeParameter(argument["value"])
                        )
                calibration_sequence = calibration_sequence.shift_phase(frame, phase)
            elif instr["name"] == "shift_frequency":
                frame = frequency = None
                for argument in instr["arguments"]:
                    if argument["name"] == "frame":
                        f = "_".join(argument["value"].split("_")[:-1]) + "_frame"
                        frame = self.frames[f]
                    elif argument["name"] == "frequency":
                        frequency = (
                            float(argument["value"])
                            if is_float(argument["value"])
                            else FreeParameter(argument["value"])
                        )
                calibration_sequence = calibration_sequence.shift_frequency(frame, frequency)
            else:
                raise ValueError(f"The {instr['name']} instruction has not been implemented")
        return calibration_sequence

    def _parse_calibration_json(
        self, calibration_data: Dict
    ) -> Dict[Tuple[Gate, QubitSet], PulseSequence]:
        """
        Takes the json string from the device calibration URL and returns a structured dictionary of corresponding
        BDK objects.

        Args:
            calibration_json (Dict): The data to be parsed.

        Returns:
            Dict[Tuple[Gate, QubitSet], PulseSequence]: The structured data in BDK native objects.

        """
        waveforms = self._parse_waveforms(calibration_data["waveforms"])
        fidelities = {}
        for qubit in calibration_data["gates"]:
            q = calibration_data["gates"][qubit]
            for gate in q:
                for i in range(len(q[gate])):
                    g = q[gate][i]
                    qubits = (
                        QubitSet([int(x) for x in g["qubits"]])
                        if is_float(g["qubits"][0])
                        else QubitSet()
                    )
                    if (gate_obj := str_to_gate(gate.capitalize())) is None:
                        # We drop out gate that are not implemented in the BDK
                        continue
                    argument = None
                    if len(g["arguments"]):
                        argument = (
                            float(g["arguments"][0])
                            if is_float(g["arguments"][0])
                            else FreeParameter(g["arguments"][0])
                        )
                    gate_qubit_key = (
                        (gate_obj(argument), qubits) if argument else (gate_obj(), qubits)
                    )
                    gate_qubit_pulse = self._get_pulse_sequence(g["calibrations"], waveforms)
                    calibration_data[gate_qubit_key] = gate_qubit_pulse

                    k1 = f"{len(qubits)}Q"
                    k2 = "-".join([str(int(qubit)) for qubit in sorted(qubits)])
                    k3 = f"f{gate_qubit_key[0].name}" if len(qubits) == 2 else "f1QRB"
                    if k3 == "fCPhaseShift":
                        k3 = "fCPHASE"
                    if len(qubits) > 0:
                        fidelities[gate_qubit_key] = self.properties.provider.specs[k1][k2][k3]
        return calibration_data, fidelities


def str_to_gate(class_name: str) -> Gate:
    """
    Returns the class of Gate corresponding to the string assigned.

    Args:
        class_name (str): The name of the gate to convert.

    Returns:
        Gate: A Gate of type corresponding to `class_name`.
    """
    if class_name == "Rx_12":
        # FIXME: Rx_12 does not exist in the Braket, it is a gate between |1> and |2>
        return None
    elif class_name == "Cz":
        class_name = "CZ"
    elif class_name == "Cphase":
        class_name = "CPhaseShift"
    elif class_name == "Xy":
        class_name = "XY"
    class_ = getattr(importlib.import_module("braket.circuits.gates"), class_name)
    return class_


def is_float(argument: str) -> bool:
    """
    Checks if a string can be cast into a float.

    Args:
        argument (str): String to check.

    Returns:
        bool: Returns true if the string can be cast as a float. False, otherwise.

    """
    if argument is None:
        return False
    try:
        float(argument)
        return True
    except ValueError:
        return False
