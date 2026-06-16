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

import warnings
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace

import boto3
import numpy as np
from botocore.client import BaseClient
from braket.ir.openqasm import Program
from braket.schema_common import BraketSchemaBase
from braket.task_result import (
    AdditionalMetadata,
    ProgramResult,
    ProgramSetExecutableFailure,
    ProgramSetExecutableResult,
    ProgramSetTaskMetadata,
    ProgramSetTaskResult,
)
from braket.task_result.program_set_executable_result_v1 import (
    ProgramSetExecutableResultMetadata,
)
from braket.task_result.program_set_task_metadata_v1 import ProgramMetadata

from braket.circuits import Circuit, Observable
from braket.circuits.observable import EULER_OBSERVABLE_PREFIX
from braket.circuits.observables import Sum
from braket.circuits.serialization import IRType
from braket.program_sets import CircuitBinding, ParameterSets, ProgramSet
from braket.tasks.measurement_utils import (
    expectation_from_measurements,
    measurement_counts_from_measurements,
    measurement_probabilities_from_measurement_counts,
    measurements_from_measurement_probabilities,
)

_PROGRAM_RESULT_SUFFIX = "/results.json"


@dataclass
class MeasuredEntry:
    """Result of a single executable in a program.

    Args:
        measurements (numpy.ndarray): 2d array - row is shot and column is qubit.
            The columns are in the order of `measured_qubits`.
        counts (Counter): A `Counter` of measurements. Key is the measurements
            in a big endian binary string. Value is the number of times that measurement occurred.
        probabilities (dict[str, float]): A dictionary of probabilistic results.
            Key is the measurements in a big endian binary string.
            Value is the probability the measurement occurred.
        measured_qubits (list[int]): The indices of the measured qubits.
        measurements_from_device (bool): flag whether `measurements`
            were copied from device. If false, `measurements` are calculated from device data.
        probabilities_from_device (bool): flag whether
            `measurement_probabilities` were copied from device. If false,
            `measurement_probabilities` are calculated from device data.
        program (str): The program this executable ran.
        inputs (dict[str, float] | None): The input parameters to this program, if any.
        observable (Observable | None): The observable of this program, if any.
    """

    measurements: np.ndarray
    counts: Counter
    probabilities: dict[str, float]
    measured_qubits: list[int]
    measurements_from_device: bool
    probabilities_from_device: bool
    program: str
    inputs: dict[str, float] | None
    observable: Observable | None

    @staticmethod
    def _from_object(
        executable_result: ProgramSetExecutableResult,
        *,
        shots: int,
        program: str,
        inputs: dict[str, float] | None = None,
        observable: Observable | None = None,
    ) -> MeasuredEntry:
        if executable_result.measurements:
            measurements = np.asarray(executable_result.measurements, dtype=int)
            m_counts = measurement_counts_from_measurements(measurements)
            m_probs = measurement_probabilities_from_measurement_counts(m_counts)
            measurements_copied_from_device = True
            m_probabilities_copied_from_device = False
        elif executable_result.measurementProbabilities:
            m_probs = executable_result.measurementProbabilities
            measurements = measurements_from_measurement_probabilities(m_probs, shots)
            m_counts = measurement_counts_from_measurements(measurements)
            measurements_copied_from_device = False
            m_probabilities_copied_from_device = True
        else:
            raise ValueError(
                'One of "measurements" or "measurementProbabilities" must be populated in',
                " the result object",
            )
        measured_qubits = executable_result.measuredQubits
        return MeasuredEntry(
            measurements=measurements,
            counts=m_counts,
            probabilities=m_probs,
            measured_qubits=measured_qubits,
            measurements_from_device=measurements_copied_from_device,
            probabilities_from_device=m_probabilities_copied_from_device,
            program=program,
            inputs=inputs,
            observable=observable,
        )

    def __post_init__(self):
        self._expectation = (
            expectation_from_measurements(
                self.measurements,
                self.measured_qubits,
                self.observable,
                self.observable.targets,
            )
            if self.observable
            else None
        )

    @property
    def expectation(self) -> float | None:
        """
        float | None: The expectation value of this entry's observable if there is one.
        """
        # TODO: Use program set payload to calculate expectation
        if self._expectation is None:
            warnings.warn("No observable was measured", stacklevel=1)
        return self._expectation


class CompositeEntry:
    """Results of a program in a program set

    Args:
        entries(list[MeasuredEntry]): The results of each executable in this program
        program (Program): The program that was run
        inputs (ParameterSets): The input values this program was run with
        observables (Sum | list[Observable] | None): The Sum Hamiltonian or observables
            that were measured, if any.
        shots_per_executable (int): The number of shots each underlying executable was run with
        additional_metadata (AdditionalMetadata | None): Additional metadata about this program.
            ``None`` for entries produced by ``ProgramSetQuantumTaskResult.merge``,
            since per-program metadata cannot be aggregated meaningfully across underlying tasks.
    """

    def __init__(
        self,
        entries: list[MeasuredEntry],
        program: Program,
        inputs: ParameterSets,
        observables: Sum | list[Observable] | None,
        shots_per_executable: int,
        additional_metadata: AdditionalMetadata | None,
    ):
        self._entries = entries
        self._program = program
        self._inputs = inputs
        self._observables = observables
        self._shots_per_executable = shots_per_executable
        self._additional_metadata = additional_metadata
        self._was_merged = False
        self._expectations = self._compute_expectations() if isinstance(observables, Sum) else None

    @property
    def entries(self) -> list[MeasuredEntry]:
        """list[MeasuredEntry]: The results of each executable in this program."""
        return self._entries

    @property
    def program(self) -> Program:
        """Program: The program that was run."""
        return self._program

    @property
    def inputs(self) -> ParameterSets:
        """ParameterSets: The input values this program was run with."""
        return self._inputs

    @property
    def observables(self) -> Sum | list[Observable] | None:
        """Sum | list[Observable] | None: The Sum Hamiltonian or observables measured,
        if any."""
        return self._observables

    @property
    def shots_per_executable(self) -> int:
        """int: The number of shots each underlying executable was run with."""
        return self._shots_per_executable

    @property
    def additional_metadata(self) -> AdditionalMetadata | None:
        """AdditionalMetadata | None: Additional metadata about this program.

        For entries produced by ``ProgramSetQuantumTaskResult.merge``, this will be ``None``;
        Use the original per-task results for true per-program metadata.
        """
        if self._was_merged:
            warnings.warn(
                "additional_metadata for a CompositeEntry on a merged "
                "ProgramSetQuantumTaskResult is None; "
                "use the original per-task results for true per-program metadata.",
                stacklevel=2,
            )
        return self._additional_metadata

    @staticmethod
    def _from_object(
        program_result: ProgramResult,
        *,
        s3_location: tuple[str, str] = (None, None),
        s3_client: BaseClient | None = None,
        shots_per_executable: int,
        observables: Sum | list[Observable] | None = None,
    ) -> CompositeEntry:
        s3_bucket, s3_prefix = s3_location
        program = CompositeEntry._get_program(
            program_result.source, s3_bucket, s3_prefix, s3_client
        )
        return CompositeEntry(
            entries=CompositeEntry._get_executable_results(
                program_result.executableResults,
                program,
                observables,
                shots_per_executable,
                s3_bucket,
                s3_prefix,
                s3_client,
            ),
            program=program,
            inputs=CompositeEntry._get_inputs(program, observables),
            observables=observables,
            shots_per_executable=shots_per_executable,
            additional_metadata=program_result.additionalMetadata,
        )

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, item: int):
        return self.entries[item]

    def expectation(self, i: int | None = None) -> float | None:
        """
        float | None: The expectation value of the Hamiltonian whose terms are the observables
        of the underlying entries, if observables were specified.
        """
        expectations = self._expectations
        if not expectations:
            raise ValueError("No Sum Hamiltonian was measured")
        num_expectations = len(expectations)
        if i is None and num_expectations > 1:
            raise ValueError(
                f"There are {num_expectations} expectation values available; returning first one",
            )
        i = i or 0
        if i >= num_expectations:
            raise ValueError(f"At most {num_expectations} expectation values available")
        return expectations[i]

    def _compute_expectations(self) -> dict[int, float]:
        num_expectations = len(self.inputs) or 1
        expectations = {}
        for i in range(num_expectations):
            num_summands = len(self.observables)
            start = i * num_summands
            expectations[i] = sum(
                entry.expectation for entry in self.entries[start : start + num_summands]
            )
        return expectations

    @staticmethod
    def _get_program(
        program: Program | str,
        s3_bucket: str | None,
        s3_prefix: str | None,
        s3_client: BaseClient | None,
    ) -> Program:
        if not s3_bucket:
            return program
        return BraketSchemaBase.parse_raw_schema(
            _retrieve_s3_object_body(s3_bucket, f"{s3_prefix}/{program}", s3_client)
        )

    @staticmethod
    def _get_inputs(program: Program, observables: Sum | list[Observable] | None) -> ParameterSets:
        if not observables:
            return ParameterSets(program.inputs or {})
        num_observables = len(observables)
        return ParameterSets({
            k: v[::num_observables]
            for k, v in (program.inputs or {}).items()
            if not k.startswith(EULER_OBSERVABLE_PREFIX)
        })

    @staticmethod
    def _get_executable_results(
        executable_results: Sequence[
            ProgramSetExecutableResult | ProgramSetExecutableFailure | str
        ],
        program: Program,
        observables: Sum | list[Observable] | None,
        shots_per_executable: int,
        s3_bucket: str | None,
        s3_prefix: str | None,
        s3_client: BaseClient | None,
    ) -> list[MeasuredEntry]:
        if not s3_bucket:
            return [
                CompositeEntry._dispatch_executable_result(
                    result, program, observables, shots_per_executable
                )
                for result in executable_results
            ]
        executable_list = []
        for result in executable_results:
            result_string = _retrieve_s3_object_body(s3_bucket, f"{s3_prefix}/{result}", s3_client)
            parsed: ProgramSetExecutableResult = BraketSchemaBase.parse_raw_schema(result_string)
            executable_list.append(
                CompositeEntry._dispatch_executable_result(
                    parsed, program, observables, shots_per_executable
                )
            )
        return executable_list

    @staticmethod
    def _dispatch_executable_result(
        result: ProgramSetExecutableResult,
        program: Program,
        observables: Sum | list[Observable] | None,
        shots_per_executable: int,
    ) -> MeasuredEntry | ProgramSetExecutableFailure:
        observables = observables.summands if isinstance(observables, Sum) else observables
        return (
            MeasuredEntry._from_object(
                result,
                program=program.source,
                shots=shots_per_executable,
                inputs={k: v[result.inputsIndex] for k, v in (program.inputs or {}).items()}
                or None,
                observable=(
                    observables[result.inputsIndex % len(observables)] if observables else None
                ),
            )
            if isinstance(result, ProgramSetExecutableResult)
            else result
        )


class ProgramSetQuantumTaskResult:
    """The result of a program set task.

    Args:
        entries (list[CompositeEntry]): The results of each program in this program set
        task_metadata (ProgramSetTaskMetadata) The metadata of the task
        num_executables (int): The total number of executables in this program set task
        program_set (ProgramSet | None): The program set that was run; if specified,
            information from the program set such as observable expectation values
            can be automatically computed.
    """

    def __init__(
        self,
        entries: list[CompositeEntry],
        task_metadata: ProgramSetTaskMetadata,
        num_executables: int,
        program_set: ProgramSet | None,
    ):
        self._entries = entries
        self._task_metadata = task_metadata
        self._num_executables = num_executables
        self._program_set = program_set
        self._was_merged = False

    @property
    def entries(self) -> list[CompositeEntry]:
        """list[CompositeEntry]: The results of each program in this program set."""
        return self._entries

    @property
    def task_metadata(self) -> ProgramSetTaskMetadata:
        """ProgramSetTaskMetadata: The metadata of the task."""
        if self._was_merged:
            warnings.warn(
                "task_metadata for a merged ProgramSetQuantumTaskResult is synthesized "
                "from multiple underlying tasks; it does not reflect any one underlying task. "
                "Use the original per-task results for true task metadata.",
                stacklevel=2,
            )
        return self._task_metadata

    @property
    def num_executables(self) -> int:
        """int: The total number of executables in this program set task."""
        return self._num_executables

    @property
    def program_set(self) -> ProgramSet | None:
        """ProgramSet | None: The program set that was run, if provided to the constructor."""
        return self._program_set

    @staticmethod
    def from_object(
        result_schema: ProgramSetTaskResult, program_set: ProgramSet | None = None
    ) -> ProgramSetQuantumTaskResult:
        """
        Create ProgramSetQuantumTaskResult from ProgramSetTaskResult object.

        Args:
            result_schema (ProgramSetTaskResult): The result returned by the device; programs
                and metadata may be specified as relative S3 paths, in which case they will be
                downloaded to populate the instance.
            program_set (ProgramSet): The program set that was run; if specified, information from
                the program set such as observable expectation values can be automatically computed.
                Default: None.

        Returns:
            ProgramSetQuantumTaskResult: A ProgramSetQuantumTaskResult based on the given
            schema object; all data stored in S3 is downloaded.
        """
        s3_bucket, s3_prefix = result_schema.s3Location or (None, None)
        # prevent circular import of AwsSession
        s3_client = boto3.client("s3") if s3_bucket else None
        metadata: ProgramSetTaskMetadata = ProgramSetQuantumTaskResult._get_metadata(
            result_schema.taskMetadata, s3_bucket, s3_prefix, s3_client
        )
        program_set = program_set if isinstance(program_set, ProgramSet) else None
        num_executables = ProgramSetQuantumTaskResult._compute_num_executables(metadata)
        shots_per_executable = metadata.requestedShots // num_executables
        return ProgramSetQuantumTaskResult(
            entries=ProgramSetQuantumTaskResult._get_entries(
                result_schema.programResults,
                shots_per_executable,
                program_set,
                s3_bucket,
                s3_prefix,
                s3_client,
            ),
            num_executables=num_executables,
            task_metadata=metadata,
            program_set=program_set,
        )

    @staticmethod
    def merge(
        results: Sequence[ProgramSetQuantumTaskResult],
        program_set: ProgramSet,
        index_map: list[list[int]],
    ) -> ProgramSetQuantumTaskResult:
        """Reconstruct a ``ProgramSetQuantumTaskResult`` from the task results produced by running
        each program set of ``program_set.split(...)``.

        ``index_map`` is the per-executable map returned alongside the program sets by
        ``ProgramSet.split``: ``index_map[k][j]`` gives the index, in the order of ``program_set``,
        of the executable that the jth executable of the kth task represents. The kth task's
        executables are read in order for its program set, namely across ``results[k].entries``,
        and within each ``CompositeEntry`` across its ``entries``.

        The returned ``ProgramSetQuantumTaskResult`` has the same shape as if ``program_set`` had
        been run unsplit, namely one ``CompositeEntry`` per entry of ``program_set.entries``,
        and ``MeasuredEntry`` objects in the order of the program.

        Expectation values and ``Sum`` Hamiltonian expectations are computed
        for the original ``ProgramSet``.

        Args:
            results (Sequence[ProgramSetQuantumTaskResult]): The result of each task, in the same
                order as ``program_set.split``'s return.
            program_set (ProgramSet): The original unsplit program set.
            index_map (list[list[int]]): The per-executable map from ``ProgramSet.split``.

        Returns:
            ProgramSetQuantumTaskResult: A result matching the shape of ``program_set``.

        Raises:
            ValueError: If ``len(results) != len(index_map)``, if the total size of ``index_map``
                doesn't match ``program_set.total_executables``, or if any task produces a
                different number of executables than its map expects.
        """
        if len(results) != len(index_map):
            raise ValueError(
                f"Got {len(results)} task results but {len(index_map)} entries in index_map"
            )
        total_executables = program_set.total_executables
        total_mapped = sum(len(m) for m in index_map)
        if total_mapped != total_executables:
            raise ValueError(
                f"Index map covers {total_mapped} executables but the original program set "
                f"has {total_executables}"
            )

        programs = [_binding_to_program(binding) for binding in program_set.entries]
        executable_indices = list(program_set.enumerate_executables())
        shots_per_executable = program_set.shots_per_executable

        executable_results_in_order = [None] * total_executables
        for k, result in enumerate(results):
            _reorder_executable_results(
                k=k,
                result=result,
                parent_indices=index_map[k],
                program_set=program_set,
                programs=programs,
                executable_indices=executable_indices,
                out=executable_results_in_order,
            )

        entries = []
        start = 0
        for binding_idx, binding in enumerate(program_set.entries):
            count = _count_executables(binding)
            program = programs[binding_idx]
            observables = binding.observables if isinstance(binding, CircuitBinding) else None
            entry = CompositeEntry(
                entries=executable_results_in_order[start : start + count],
                program=program,
                inputs=CompositeEntry._get_inputs(program, observables),
                observables=observables,
                shots_per_executable=shots_per_executable,
                additional_metadata=None,
            )
            entry._was_merged = True
            entries.append(entry)
            start += count

        metas = [r._task_metadata for r in results]
        merged = ProgramSetQuantumTaskResult(
            entries=entries,
            task_metadata=ProgramSetTaskMetadata(
                id=";".join(meta.id for meta in metas),  # Better way to do this?
                deviceId=metas[0].deviceId,
                requestedShots=sum(m.requestedShots for m in metas),
                successfulShots=sum(m.successfulShots for m in metas),
                programMetadata=[
                    ProgramMetadata(
                        executables=[
                            ProgramSetExecutableResultMetadata()
                            for _ in range(_count_executables(b))
                        ]
                    )
                    for b in program_set.entries
                ],
                deviceParameters=None,  # TODO: find a way to fill this in
                createdAt=min(m.createdAt for m in metas if m.createdAt),
                endedAt=max(m.endedAt for m in metas if m.endedAt),
                status="COMPLETED" if any(m.status == "COMPLETED" for m in metas) else "FAILED",
                totalFailedExecutables=sum(m.totalFailedExecutables for m in metas),
            ),
            num_executables=total_executables,
            program_set=program_set,
        )
        merged._was_merged = True
        return merged

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, item: int):
        return self.entries[item]

    @property
    def programs(self) -> list[Program]:
        """
        list[Program]: The OpenQASM programs specified in the program set
        """
        return [entry.program for entry in self.entries]

    @staticmethod
    def _get_metadata(
        metadata: ProgramSetTaskMetadata | str,
        s3_bucket: str | None,
        s3_prefix: str | None,
        s3_client: BaseClient | None,
    ) -> ProgramSetTaskMetadata:
        if not s3_bucket:
            return metadata
        meta_string = _retrieve_s3_object_body(s3_bucket, f"{s3_prefix}/{metadata}", s3_client)
        return BraketSchemaBase.parse_raw_schema(meta_string)

    @staticmethod
    def _get_entries(
        program_results: Sequence[ProgramResult | str],
        shots_per_executable: int,
        program_set: ProgramSet | None,
        s3_bucket: str | None,
        s3_prefix: str | None,
        s3_client: BaseClient | None,
    ) -> list[CompositeEntry | MeasuredEntry]:
        if program_set:
            entries = []
            for entry, result in zip(program_set.entries, program_results, strict=True):
                entries.append(
                    # The program has observables available to compute
                    ProgramSetQuantumTaskResult._result_to_entry(
                        result,
                        shots_per_executable,
                        s3_prefix=s3_prefix,
                        s3_bucket=s3_bucket,
                        s3_client=s3_client,
                        observables=entry.observables,
                    )
                    if isinstance(entry, CircuitBinding)
                    # The program has no observables
                    else ProgramSetQuantumTaskResult._result_to_entry(
                        result,
                        shots_per_executable,
                        s3_prefix=s3_prefix,
                        s3_bucket=s3_bucket,
                        s3_client=s3_client,
                    )
                )
            return entries
        return [
            ProgramSetQuantumTaskResult._result_to_entry(
                result,
                shots_per_executable,
                s3_prefix=s3_prefix,
                s3_bucket=s3_bucket,
                s3_client=s3_client,
            )
            for result in program_results
        ]

    @staticmethod
    def _result_to_entry(
        result: ProgramResult | str,
        shots_per_executable: int,
        # Note: prefix only refers to the part of the S3 prefix after
        # the _whole_ task result's prefix
        s3_bucket: str | None,
        s3_prefix: str | None,
        s3_client: BaseClient | None,
        observables: Sum | list[Observable] | None = None,
    ) -> CompositeEntry | MeasuredEntry:
        if isinstance(result, ProgramResult):
            return CompositeEntry._from_object(
                result,
                shots_per_executable=shots_per_executable,
                s3_client=None,
                s3_location=(None, None),
                observables=observables,
            )
        result_key = f"{s3_prefix}/{result}"
        return CompositeEntry._from_object(
            program_result=BraketSchemaBase.parse_raw_schema(
                _retrieve_s3_object_body(
                    s3_bucket,
                    result_key,
                    s3_client,
                )
            ),
            shots_per_executable=shots_per_executable,
            s3_client=s3_client,
            s3_location=(s3_bucket, result_key.removesuffix(_PROGRAM_RESULT_SUFFIX)),
            observables=observables,
        )

    @staticmethod
    def _compute_num_executables(metadata: ProgramSetTaskMetadata) -> int:
        counter = 0
        for program in metadata.programMetadata:
            counter += len(program.executables)
        return counter


def _binding_to_program(binding: CircuitBinding | Circuit) -> Program:
    if isinstance(binding, Circuit):
        return Program(source=binding.to_ir(IRType.OPENQASM).source, inputs=None)
    return binding.to_ir()


def _count_executables(binding: CircuitBinding | Circuit) -> int:
    if isinstance(binding, Circuit):
        return 1
    num_ps = len(binding.input_sets) if binding.input_sets is not None else 1
    num_obs = len(binding.observables) if binding.observables is not None else 1
    return num_ps * num_obs


def _reorder_executable_results(
    k: int,
    result: ProgramSetQuantumTaskResult,
    parent_indices: list[int],
    program_set: ProgramSet,
    programs: list[Program],
    executable_indices: list[tuple[int, int, int]],
    out: list[MeasuredEntry | ProgramSetExecutableFailure | None],
) -> None:
    j = 0
    for composite in result.entries:
        for entry in composite.entries:
            if j >= len(parent_indices):
                raise ValueError(
                    f"t=Task {result.task_metadata.id} at index {k} "
                    "produced more executables than index map expects"
                )
            orig_idx = parent_indices[j]
            binding_idx, ps_idx, obs_idx = executable_indices[orig_idx]
            out[orig_idx] = _convert_measured_entry(
                entry,
                program_set.entries[binding_idx],
                programs[binding_idx],
                ps_idx,
                obs_idx,
            )
            j += 1
    if j != len(parent_indices):
        raise ValueError(
            f"Task {result.task_metadata.id} at index {k} produced {j} executables "
            f"but index map expected {len(parent_indices)}"
        )


def _convert_measured_entry(
    entry: MeasuredEntry | ProgramSetExecutableFailure,
    original_binding: CircuitBinding | Circuit,
    original_program: Program,
    parameter_set_index: int,
    observable_index: int,
) -> MeasuredEntry | ProgramSetExecutableFailure:
    if isinstance(entry, ProgramSetExecutableFailure):
        return entry
    if isinstance(original_binding, Circuit):
        return replace(entry, program=original_program.source, inputs=None, observable=None)
    observables = original_binding.observables
    if observables is None:
        observable: Observable | None = None
        num_obs = 1
    elif isinstance(observables, Sum):
        observable = observables.summands[observable_index]
        num_obs = len(observables.summands)
    else:
        observable = observables[observable_index]
        num_obs = len(observables)
    orig_inputs_index = parameter_set_index * num_obs + observable_index
    program_inputs = original_program.inputs or {}
    return replace(
        entry,
        program=original_program.source,
        inputs={key: value[orig_inputs_index] for key, value in program_inputs.items()} or None,
        observable=observable,
    )


def _retrieve_s3_object_body(s3_bucket: str, s3_object_key: str, s3_client: BaseClient) -> str:
    """Retrieve the S3 object body.

    Args:
        s3_bucket (str): The S3 bucket name.
        s3_object_key (str): The S3 object key within the `s3_bucket`.
        s3_client (BaseClient): The S3 client that will be used to download objects.

    Returns:
        str: The body of the S3 object.
    """
    return s3_client.get_object(Bucket=s3_bucket, Key=s3_object_key)["Body"].read().decode("utf-8")
