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
from dataclasses import dataclass

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

from braket.circuits import Observable
from braket.circuits.observable import EULER_OBSERVABLE_PREFIX
from braket.circuits.observables import Sum
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


@dataclass
class CompositeEntry:
    """Results of a program in a program set

    Args:
        entries(list[MeasuredEntry]): The results of each executable in this program
        program (Program): The program that was run
        inputs (ParameterSets): The input values this program was run with
        observables (Sum | list[Observable] | None): The Sum Hamiltonian or observables
            that were measured, if any.
        shots_per_executable (int): The number of shots each underlying executable was run with
        additional_metadata (AdditionalMetadata): Additional metadata about this program
    """

    entries: list[MeasuredEntry]
    program: Program
    inputs: ParameterSets
    observables: Sum | list[Observable] | None
    shots_per_executable: int
    additional_metadata: AdditionalMetadata

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

    def __post_init__(self):
        self._expectations = (
            self._compute_expectations() if isinstance(self.observables, Sum) else None
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


@dataclass
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

    entries: list[CompositeEntry]
    task_metadata: ProgramSetTaskMetadata
    num_executables: int
    program_set: ProgramSet | None

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
