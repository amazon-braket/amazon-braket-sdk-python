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

import json
import warnings
from unittest.mock import Mock, patch

import numpy as np
import pytest

from braket.circuits import Circuit
from braket.circuits.observables import X, Y, Z
from braket.circuits.serialization import IRType
from braket.ir.openqasm import Program
from braket.parametric import FreeParameter
from braket.program_sets import CircuitBinding, ParameterSets, ProgramSet
from braket.schema_common import BraketSchemaBase
from braket.tasks import ProgramSetQuantumTaskResult
from braket.tasks.program_set_quantum_task_result import CompositeEntry, MeasuredEntry


@pytest.fixture
def execution_measurements():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_executable_result",
            "version": "1",
        },
        "measurements": [
            [0, 0],
            [0, 0],
            [1, 1],
            [0, 0],
            [1, 1],
            [0, 0],
            [1, 1],
            [0, 0],
            [1, 1],
            [0, 0],
            [1, 1],
            [0, 0],
            [0, 0],
            [0, 0],
            [1, 1],
            [1, 1],
            [1, 1],
            [0, 0],
            [1, 1],
            [0, 0],
        ],
        "measuredQubits": [0, 1],
        "inputsIndex": 0,
    }


@pytest.fixture
def execution_measurement_probabilities():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_executable_result",
            "version": "1",
        },
        "measurementProbabilities": {"00": 0.7, "11": 0.3},
        "measuredQubits": [0, 1],
        "inputsIndex": 0,
    }


@pytest.fixture
def execution_results_missing():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_executable_result",
            "version": "1",
        },
        "measuredQubits": [0, 1],
        "inputsIndex": 0,
    }


@pytest.fixture
def execution_failure():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_executable_failure",
            "version": "1",
        },
        "inputsIndex": 0,
        "failureMetadata": {
            "failureReason": "QPU was sick, should be good again after getting some sleep",
            "retryable": True,
            "category": "DEVICE",
        },
    }


@pytest.fixture
def program():
    return {
        "braketSchemaHeader": {"name": "braket.ir.openqasm.program", "version": "1"},
        "source": "OPENQASM 3.0;\nbit[2] b;\nqubit[2] q;\nh q[0];\ncnot q[0], q[1];\nb[0] = measure q[0];\nb[1] = measure q[1];",  # noqa
        "inputs": {"theta": [0.12, 2.1]},
    }


@pytest.fixture
def program_observables():
    return {
        "braketSchemaHeader": {"name": "braket.ir.openqasm.program", "version": "1"},
        "source": "OPENQASM 3.0;\nbit[2] b;\nqubit[2] q;\nh q[0];\ncnot q[0], q[1];\nb[0] = measure q[0];\nb[1] = measure q[1];",  # noqa
        "inputs": {
            "theta": [0.12, 0.12, 0.12, 2.1, 2.1, 2.1],
            "_OBSERVABLE_THETA_0": [0, np.pi / 2, 0, 0, np.pi / 2, 0],
            "_OBSERVABLE_PHI_0": [0, np.pi / 2, np.pi / 2, 0, np.pi / 2, np.pi / 2],
            "_OBSERVABLE_OMEGA_0": [0, np.pi / 2, np.pi / 2, 0, np.pi / 2, np.pi / 2],
        },
    }


@pytest.fixture
def program_result_local(execution_measurement_probabilities, execution_failure, program):
    return {
        "braketSchemaHeader": {"name": "braket.task_result.program_result", "version": "1"},
        "executableResults": [execution_measurement_probabilities, execution_failure],
        "source": program,
        "additionalMetadata": {
            "simulatorMetadata": {
                "braketSchemaHeader": {
                    "name": "braket.task_result.simulator_metadata",
                    "version": "1",
                },
                "executionDuration": 50,
            }
        },
    }


@pytest.fixture
def program_result_s3():
    return {
        "braketSchemaHeader": {"name": "braket.task_result.program_result", "version": "1"},
        "executableResults": ["executables/0.json"],
        "source": "program.json",
        "additionalMetadata": {
            "simulatorMetadata": {
                "braketSchemaHeader": {
                    "name": "braket.task_result.simulator_metadata",
                    "version": "1",
                },
                "executionDuration": 47,
            }
        },
    }


@pytest.fixture
def program_result_observables(execution_measurement_probabilities, program_observables):
    executable_results = [dict(execution_measurement_probabilities) for _ in range(6)]
    for i, executable_result in enumerate(executable_results):
        executable_result["inputsIndex"] = i
    result = {
        "braketSchemaHeader": {"name": "braket.task_result.program_result", "version": "1"},
        "executableResults": executable_results,
        "source": program_observables,
        "additionalMetadata": {
            "simulatorMetadata": {
                "braketSchemaHeader": {
                    "name": "braket.task_result.simulator_metadata",
                    "version": "1",
                },
                "executionDuration": 100,
            }
        },
    }
    return result


@pytest.fixture
def metadata():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_metadata",
            "version": "1",
        },
        "id": "arn:aws:braket:us-west-2:667256736152:quantum-task/bfebc86f-e4ed-4d6f-8131-addd1a49d6dc",  # noqa
        "deviceId": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        "requestedShots": 120,
        "successfulShots": 100,
        "programMetadata": [{"executables": [{}, {}, {}]}],
        "deviceParameters": {
            "braketSchemaHeader": {
                "name": "braket.device_schema.simulators.gate_model_simulator_device_parameters",
                "version": "1",
            },
            "paradigmParameters": {
                "braketSchemaHeader": {
                    "name": "braket.device_schema.gate_model_parameters",
                    "version": "1",
                },
                "qubitCount": 5,
                "disableQubitRewiring": False,
            },
        },
        "createdAt": "2024-10-15T19:06:58.986Z",
        "endedAt": "2024-10-15T19:07:00.382Z",
        "status": "COMPLETED",
        "totalFailedExecutables": 1,
    }


@pytest.fixture
def result_local(metadata, program_result_local):
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_result",
            "version": "1",
        },
        "programResults": [program_result_local],
        "taskMetadata": metadata,
    }


@pytest.fixture
def result_s3():
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_result",
            "version": "1",
        },
        "programResults": ["programs/0/results.json"],
        "s3Location": ["amazon-braket-foo", "tasks/bar"],
        "taskMetadata": "metadata.json",
    }


@pytest.fixture
def result_observables(metadata, program_result_observables):
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_result",
            "version": "1",
        },
        "programResults": [program_result_observables],
        "taskMetadata": metadata,
    }


def test_local(result_local, metadata, execution_failure):
    result = ProgramSetQuantumTaskResult.from_object(
        BraketSchemaBase.parse_raw_schema(json.dumps(result_local))
    )
    assert len(result.programs) == 1
    assert result.num_executables == 3  # From metadata
    assert len(result) == 1

    entry = result[0]
    assert isinstance(entry, CompositeEntry)
    assert len(entry) == 2
    assert entry.inputs == ParameterSets({"theta": [0.12, 2.1]})
    with pytest.raises(ValueError):
        entry.expectation(0)
    assert entry.additional_metadata.simulatorMetadata.executionDuration == 50
    assert entry.shots_per_executable > 0

    success = entry[0]
    assert isinstance(success, MeasuredEntry)
    assert success.probabilities == {"00": 0.7, "11": 0.3}
    assert success.counts["00"] == 28
    assert success.counts["11"] == 12
    assert len(success.counts) == 2
    assert len(success.measurements) == 40
    with pytest.warns(UserWarning):
        assert success.expectation is None
    assert entry[1] == BraketSchemaBase.parse_raw_schema(json.dumps(execution_failure))
    assert result.task_metadata == BraketSchemaBase.parse_raw_schema(json.dumps(metadata))


@patch("braket.tasks.program_set_quantum_task_result.boto3.client")
def test_s3(
    mock_boto3_client, result_s3, program_result_s3, program, execution_measurements, metadata
):
    mock_read_object = Mock()
    mock_read_object.decode.side_effect = [
        json.dumps(f) for f in [metadata, program_result_s3, program, execution_measurements]
    ]
    mock_body_object = Mock()
    mock_body_object.read.return_value = mock_read_object
    mock_client = Mock()
    mock_client.get_object.return_value = {"Body": mock_body_object}
    mock_boto3_client.return_value = mock_client
    result = ProgramSetQuantumTaskResult.from_object(
        BraketSchemaBase.parse_raw_schema(json.dumps(result_s3))
    )
    bucket = "amazon-braket-foo"
    assert mock_client.get_object.call_args_list == [
        (dict(Bucket=bucket, Key="tasks/bar/metadata.json"),),
        (dict(Bucket=bucket, Key="tasks/bar/programs/0/results.json"),),
        (dict(Bucket=bucket, Key="tasks/bar/programs/0/program.json"),),
        (dict(Bucket=bucket, Key="tasks/bar/programs/0/executables/0.json"),),
    ]

    assert len(result.programs) == 1
    assert result.num_executables == 3  # From metadata
    assert len(result) == 1

    entry = result[0]
    assert entry.inputs == ParameterSets({"theta": [0.12, 2.1]})
    with pytest.raises(ValueError):
        entry.expectation(0)
    assert entry.additional_metadata.simulatorMetadata.executionDuration == 47

    assert isinstance(entry, CompositeEntry)
    success = entry[0]
    assert isinstance(success, MeasuredEntry)
    assert len(success.measurements) == 20
    assert success.counts["00"] == 11
    assert success.counts["11"] == 9
    assert len(success.counts) == 2
    assert np.isclose(success.probabilities["00"], 0.55)
    assert np.isclose(success.probabilities["11"], 0.45)
    assert len(success.probabilities) == 2
    with pytest.warns(UserWarning):
        assert success.expectation is None


def test_observables(result_observables, metadata):
    result = ProgramSetQuantumTaskResult.from_object(
        BraketSchemaBase.parse_raw_schema(json.dumps(result_observables)),
        ProgramSet(
            CircuitBinding(
                Circuit().rx(0, FreeParameter("theta")),
                input_sets={"theta": [0.12, 2.1]},
                observables=10 * Z(0) + X(0) - 0.01 * Y(0) @ X(1),
            )
        ),
    )
    assert len(result.programs) == 1
    assert result.num_executables == 3  # From metadata
    assert len(result) == 1

    composite = result[0]
    assert isinstance(composite, CompositeEntry)
    assert composite.inputs == ParameterSets({"theta": [0.12, 2.1]})
    with pytest.raises(ValueError):
        composite.expectation()
    with pytest.raises(ValueError):
        composite.expectation(2)
    assert len(composite) == 6
    assert composite.additional_metadata.simulatorMetadata.executionDuration == 100

    for measured in composite:
        assert isinstance(measured, MeasuredEntry)
        assert measured.probabilities == {"00": 0.7, "11": 0.3}
        assert measured.counts["00"] == 28
        assert measured.counts["11"] == 12
        assert len(measured.counts) == 2
        assert len(measured.measurements) == 40
    assert composite[3].expectation == 4
    assert composite[4].expectation == 0.4
    assert composite[5].expectation == -0.01


def test_observables_no_inputs(result_observables, metadata):
    del result_observables["programResults"][0]["source"]["inputs"]["theta"]
    h = 10000 * Z(0) + 1000 * X(0) - 100 * Z(0) + 10 * Z(1) + X(1) - 0.1 * Y(1)
    result = ProgramSetQuantumTaskResult.from_object(
        BraketSchemaBase.parse_raw_schema(json.dumps(result_observables)),
        ProgramSet(CircuitBinding(Circuit().h(0).cnot(0, 1), observables=h)),
    )
    assert len(result.programs) == 1
    assert result.num_executables == 3  # From metadata
    assert len(result) == 1

    composite = result[0]
    assert isinstance(composite, CompositeEntry)
    assert composite.inputs == ParameterSets({})
    assert np.isclose(composite.expectation(), 4364.36)
    with pytest.raises(ValueError):
        composite.expectation(1)
    assert len(composite) == 6
    assert composite.additional_metadata.simulatorMetadata.executionDuration == 100

    for measured in composite:
        assert isinstance(measured, MeasuredEntry)
        assert measured.probabilities == {"00": 0.7, "11": 0.3}
        assert measured.counts["00"] == 28
        assert measured.counts["11"] == 12
        assert len(measured.counts) == 2
        assert len(measured.measurements) == 40


def test_results_missing(metadata, execution_results_missing, program):
    result = {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_result",
            "version": "1",
        },
        "programResults": [
            {
                "braketSchemaHeader": {"name": "braket.task_result.program_result", "version": "1"},
                "executableResults": [execution_results_missing],
                "source": program,
                "additionalMetadata": {
                    "simulatorMetadata": {
                        "braketSchemaHeader": {
                            "name": "braket.task_result.simulator_metadata",
                            "version": "1",
                        },
                        "executionDuration": 50,
                    }
                },
            }
        ],
        "taskMetadata": metadata,
    }
    with pytest.raises(ValueError):
        ProgramSetQuantumTaskResult.from_object(
            BraketSchemaBase.parse_raw_schema(json.dumps(result))
        )


def test_dispatch_executable_result_with_none_inputs(execution_measurement_probabilities):
    mock_program = Mock()
    mock_program.source = "OPENQASM 3.0;\nbit[2] b;\nqubit[2] q;\nh q[0];\ncnot q[0], q[1];\nb[0] = measure q[0];\nb[1] = measure q[1];"
    mock_program.inputs = None
    result = BraketSchemaBase.parse_raw_schema(json.dumps(execution_measurement_probabilities))

    measured_entry = CompositeEntry._dispatch_executable_result(
        result=result, program=mock_program, observables=None, shots_per_executable=40
    )
    assert isinstance(measured_entry, MeasuredEntry)
    assert measured_entry.inputs is None
    assert measured_entry.probabilities == {"00": 0.7, "11": 0.3}


_SIM_METADATA_HEADER = {
    "braketSchemaHeader": {"name": "braket.task_result.simulator_metadata", "version": "1"},
    "executionDuration": 50,
}
_DEVICE_PARAMS = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.simulators.gate_model_simulator_device_parameters",
        "version": "1",
    },
    "paradigmParameters": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.gate_model_parameters",
            "version": "1",
        },
        "qubitCount": 5,
        "disableQubitRewiring": False,
    },
}


def _make_exec_result(inputs_index, probs=None):
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_executable_result",
            "version": "1",
        },
        "inputsIndex": inputs_index,
        "measurementProbabilities": probs or {"00": 0.7, "11": 0.3},
        "measuredQubits": [0, 1],
    }


def _make_program_result(program_dict, executable_dicts):
    return {
        "braketSchemaHeader": {"name": "braket.task_result.program_result", "version": "1"},
        "executableResults": executable_dicts,
        "source": program_dict,
        "additionalMetadata": {"simulatorMetadata": dict(_SIM_METADATA_HEADER)},
    }


def _make_task_metadata(
    program_executable_counts, task_id="arn:aws:braket:::task/sub", shots_per_executable=40
):
    total = sum(program_executable_counts)
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_metadata",
            "version": "1",
        },
        "id": task_id,
        "deviceId": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        "requestedShots": shots_per_executable * total,
        "successfulShots": shots_per_executable * total,
        "programMetadata": [
            {"executables": [{} for _ in range(n)]} for n in program_executable_counts
        ],
        "deviceParameters": dict(_DEVICE_PARAMS),
        "createdAt": "2024-10-15T19:06:58.986Z",
        "endedAt": "2024-10-15T19:07:00.382Z",
        "status": "COMPLETED",
        "totalFailedExecutables": 0,
    }


def _make_task_result(program_results, metadata):
    return {
        "braketSchemaHeader": {
            "name": "braket.task_result.program_set_task_result",
            "version": "1",
        },
        "programResults": program_results,
        "taskMetadata": metadata,
    }


def _parse(d):
    return BraketSchemaBase.parse_raw_schema(json.dumps(d))


def _build_sub_quantum_result(sub_program_set, programs_execs, shots_per_executable=40):
    """Build a :class:`ProgramSetQuantumTaskResult` for a sub-program-set by first
    building a wire-format ``ProgramSetTaskResult`` and passing it through
    :meth:`ProgramSetQuantumTaskResult.from_object`.

    Args:
        sub_program_set: The sub-``ProgramSet`` whose run produced the result.
        programs_execs: One list of exec-result dicts per entry in ``sub_program_set.entries``.
        shots_per_executable: shots per executable, propagated to the metadata.
    """
    program_results = []
    counts = []
    for entry, execs in zip(sub_program_set.entries, programs_execs, strict=True):
        if isinstance(entry, CircuitBinding):
            source_dict = entry.to_ir().dict()
        else:
            source_dict = Program(source=entry.to_ir(IRType.OPENQASM).source, inputs=None).dict()
        program_results.append(_make_program_result(source_dict, execs))
        counts.append(len(execs))
    wire = _parse(
        _make_task_result(
            program_results, _make_task_metadata(counts, shots_per_executable=shots_per_executable)
        )
    )
    return ProgramSetQuantumTaskResult.from_object(wire, sub_program_set)


def test_from_multiple_single_task_no_split_roundtrips(circuit_rx_parametrized_fixture):
    """If split returns [self], from_multiple should reproduce from_object's output."""
    binding = CircuitBinding(
        circuit_rx_parametrized_fixture,
        input_sets={"theta": [0.12, 2.1]},
        observables=10 * Z(0) + X(0) - 0.01 * Y(0) @ X(1),
    )
    ps = ProgramSet(binding)
    subs, index_map = ps.split(100)  # fits, so one task identical to ps.
    assert subs == [ps]

    # Build a ProgramSetQuantumTaskResult that represents running this ps: the wire
    # payload goes through from_object first.
    sub_program = subs[0].to_ir().programs[0].dict()
    execs = [_make_exec_result(i) for i in range(ps.total_executables)]
    wire = _parse(
        _make_task_result(
            [_make_program_result(sub_program, execs)],
            _make_task_metadata([ps.total_executables]),
        )
    )
    reference = ProgramSetQuantumTaskResult.from_object(wire, ps)

    merged = ProgramSetQuantumTaskResult.merge([reference], ps, index_map)

    assert len(merged) == len(reference) == 1
    ref_composite = reference[0]
    got_composite = merged[0]
    assert len(got_composite) == len(ref_composite)
    assert got_composite.program == ref_composite.program
    assert got_composite.inputs == ref_composite.inputs
    assert got_composite.observables == ref_composite.observables
    for m_got, m_ref in zip(got_composite.entries, ref_composite.entries):
        assert m_got.measured_qubits == m_ref.measured_qubits
        assert m_got.probabilities == m_ref.probabilities
        assert m_got.observable == m_ref.observable
        assert m_got.inputs == m_ref.inputs


def test_from_multiple_split_list_observables(circuit_rx_parametrized_fixture):
    """Split a binding with more observables than fit; scatter + regroup must
    reconstruct the same CompositeEntry as running unsplit."""
    binding = CircuitBinding(
        circuit_rx_parametrized_fixture,
        input_sets={"theta": [0.12]},
        observables=[X(0), Y(0), Z(0), X(0) @ Y(1)],  # 4 observables.
    )
    ps = ProgramSet(binding)
    subs, index_map = ps.split(2)  # 4 > 2, so observables split into windows (0,2), (2,4).
    assert [s.total_executables for s in subs] == [2, 2]

    # One sub-quantum-result per sub-program-set, built by running each through
    # from_object on an inline wire payload.
    sub_results = [
        _build_sub_quantum_result(
            sub, [[_make_exec_result(i, {"00": 1.0}) for i in range(sub.total_executables)]]
        )
        for sub in subs
    ]

    merged = ProgramSetQuantumTaskResult.merge(sub_results, ps, index_map)
    assert len(merged) == 1
    composite = merged[0]
    # The merged composite should have 4 MeasuredEntries in canonical order, each with
    # the ORIGINAL binding's observable attached at that index.
    assert len(composite) == 4
    for i, measured in enumerate(composite.entries):
        assert isinstance(measured, MeasuredEntry)
        assert measured.observable == binding.observables[i]
    assert composite.inputs == ParameterSets({"theta": [0.12]})
    # task metadata was aggregated across tasks.
    assert merged.num_executables == 4
    assert merged.program_set is ps
    assert merged.task_metadata.requestedShots == sum(
        r.task_metadata.requestedShots for r in sub_results
    )
    assert merged.task_metadata.successfulShots == sum(
        r.task_metadata.successfulShots for r in sub_results
    )


def test_from_multiple_split_sum_hamiltonian_reconstructs_expectation(
    circuit_rx_parametrized_fixture,
):
    """Splitting a Sum Hamiltonian across multiple tasks and then merging must
    reconstruct the full expectation value, because scatter+regroup feeds the original
    Sum back into ``_compute_expectations``."""
    # Same fixture as existing test_observables_no_inputs (with known expectation).
    circuit = Circuit().h(0).cnot(0, 1)
    h = 10000 * Z(0) + 1000 * X(0) - 100 * Z(0) + 10 * Z(1) + X(1) - 0.1 * Y(1)
    binding = CircuitBinding(circuit, observables=h)
    ps = ProgramSet(binding)
    assert ps.total_executables == 6

    subs, index_map = ps.split(2)  # 6 > 2, so Sum splits into 3 windows of size 2.
    assert [s.total_executables for s in subs] == [2, 2, 2]

    # Each executable's measurement is the same {"00": 0.7, "11": 0.3} as the existing
    # test_observables_no_inputs fixture, so the expectation should match 4364.36.
    sub_results = [
        _build_sub_quantum_result(
            sub, [[_make_exec_result(i) for i in range(sub.total_executables)]]
        )
        for sub in subs
    ]

    merged = ProgramSetQuantumTaskResult.merge(sub_results, ps, index_map)
    composite = merged[0]
    assert composite.observables is h
    assert len(composite) == 6
    assert np.isclose(composite.expectation(), 4364.36)


def test_from_multiple_mixed_bindings_and_failures(circuit_rx_parametrized_fixture):
    """A program set with multiple bindings, split across tasks, with one
    executable failing in a task. Failures must land at the correct original
    position in the merged result."""
    c1 = circuit_rx_parametrized_fixture
    c2 = Circuit().rx(0, FreeParameter("phi"))
    b1 = CircuitBinding(c1, {"theta": [0.1, 0.2, 0.3]}, observables=[X(0), Y(0)])  # 6 execs
    b2 = CircuitBinding(c2, {"phi": [0.4, 0.5]})  # 2 execs, no observables
    ps = ProgramSet([b1, b2])
    assert ps.total_executables == 8

    subs, index_map = ps.split(5)
    # Greedy pack with max=5: b1 classes (sizes 2,2,2) fill [2+2=4, +2>5 flush], so
    # sub 0 = 2 b1 classes (4 execs), sub 1 = 1 b1 class (2 execs) + b2 (2 execs) = 4 execs.
    assert [s.total_executables for s in subs] == [4, 4]

    def _failure(inputs_index):
        return {
            "braketSchemaHeader": {
                "name": "braket.task_result.program_set_executable_failure",
                "version": "1",
            },
            "inputsIndex": inputs_index,
            "failureMetadata": {
                "failureReason": "test failure",
                "retryable": False,
                "category": "DEVICE",
            },
        }

    # Inject a failure at original index 5 (b1 ps=2, obs=1) which lives in sub 1.
    sub_results = []
    failure_injected = False
    for k, sub in enumerate(subs):
        programs_execs = []
        for prog_idx, entry in enumerate(sub.entries):
            num_execs = len(entry) if isinstance(entry, CircuitBinding) else 1
            execs = []
            for i in range(num_execs):
                # Figure out this sub-executable's original index. Within sub k,
                # j runs across all programs so we need a running counter.
                j = (
                    sum(
                        len(prev_entry) if isinstance(prev_entry, CircuitBinding) else 1
                        for prev_entry in sub.entries[:prog_idx]
                    )
                    + i
                )
                if index_map[k][j] == 5:
                    execs.append(_failure(i))
                    failure_injected = True
                else:
                    execs.append(_make_exec_result(i))
            programs_execs.append(execs)
        sub_results.append(_build_sub_quantum_result(sub, programs_execs))

    assert failure_injected
    merged = ProgramSetQuantumTaskResult.merge(sub_results, ps, index_map)
    assert len(merged) == 2
    # Binding 0: 6 executables, position 5 is a failure.
    assert len(merged[0]) == 6
    # Binding 1: 2 executables, all successful.
    assert len(merged[1]) == 2
    from braket.task_result import ProgramSetExecutableFailure

    assert isinstance(merged[0].entries[5], ProgramSetExecutableFailure)
    # All non-failure entries for binding 0 have the correct observables.
    for i, entry in enumerate(merged[0].entries):
        if isinstance(entry, MeasuredEntry):
            expected_obs = b1.observables[i % len(b1.observables)]
            assert entry.observable == expected_obs
    # Binding 1 entries have no observable.
    for entry in merged[1].entries:
        if isinstance(entry, MeasuredEntry):
            assert entry.observable is None


def test_from_multiple_validates_index_map_size(circuit_rx_parametrized_fixture):
    binding = CircuitBinding(circuit_rx_parametrized_fixture, input_sets={"theta": [0.1, 0.2]})
    ps = ProgramSet(binding)
    sub_result = _build_sub_quantum_result(ps, [[_make_exec_result(0), _make_exec_result(1)]])
    # index_map has 1 entry for 1 task, but size doesn't match ps.total_executables.
    with pytest.raises(ValueError, match="Index map covers 1"):
        ProgramSetQuantumTaskResult.merge([sub_result], ps, [[0]])
    # Task count doesn't match index_map's length.
    with pytest.raises(ValueError, match="1 task results but 2 entries in index_map"):
        ProgramSetQuantumTaskResult.merge([sub_result], ps, [[0], [1]])


@pytest.fixture
def circuit_rx_parametrized_fixture():
    return Circuit().rx(0, FreeParameter("theta")).cnot(0, 1)


def test_from_multiple_with_plain_circuit_entries():
    """from_multiple should handle plain Circuit entries (no inputs, no observables)."""
    c1 = ghz_test(2)
    c2 = ghz_test(1)
    ps = ProgramSet([c1, c2])
    subs, index_map = ps.split(1)
    assert [s.total_executables for s in subs] == [1, 1]

    sub_results = [_build_sub_quantum_result(sub, [[_make_exec_result(0)]]) for sub in subs]

    merged = ProgramSetQuantumTaskResult.merge(sub_results, ps, index_map)
    assert len(merged) == 2
    assert len(merged[0]) == 1
    assert len(merged[1]) == 1
    assert merged[0].observables is None
    assert merged[0].entries[0].observable is None
    assert merged[0].entries[0].inputs is None


def test_from_multiple_rejects_task_over_index_map(circuit_rx_parametrized_fixture):
    """Task has more executables than index_map[k] covers."""
    binding = CircuitBinding(circuit_rx_parametrized_fixture, input_sets={"theta": [0.1, 0.2]})
    ps = ProgramSet(binding)
    # Task reports 2 executables, but index_map says there's only 1.
    sub_result = _build_sub_quantum_result(ps, [[_make_exec_result(0), _make_exec_result(1)]])
    with pytest.raises(ValueError, match="produced more executables than index map"):
        ProgramSetQuantumTaskResult.merge(
            [sub_result],
            ProgramSet(CircuitBinding(circuit_rx_parametrized_fixture, {"theta": [0.1]})),
            [[0]],
        )


def test_from_multiple_rejects_task_under_index_map(circuit_rx_parametrized_fixture):
    """Task has fewer executables than index_map[k] covers."""
    binding = CircuitBinding(circuit_rx_parametrized_fixture, input_sets={"theta": [0.1, 0.2]})
    ps = ProgramSet(binding)
    # Task reports only 1 executable, but index_map says there are 2.
    sub_result = _build_sub_quantum_result(ps, [[_make_exec_result(0)]])
    with pytest.raises(ValueError, match="expected 2"):
        ProgramSetQuantumTaskResult.merge([sub_result], ps, [[0, 1]])


def test_from_object_task_metadata_does_not_warn(circuit_rx_parametrized_fixture):
    """A result built from a single ProgramSetTaskResult is not merged, so
    accessing task_metadata should not emit a warning."""
    binding = CircuitBinding(circuit_rx_parametrized_fixture, input_sets={"theta": [0.1, 0.2]})
    ps = ProgramSet(binding)
    result = _build_sub_quantum_result(ps, [[_make_exec_result(0), _make_exec_result(1)]])
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # turn any UserWarning into an exception
        # Accessing task_metadata multiple times must not raise.
        _ = result.task_metadata
        _ = result.task_metadata.requestedShots


def test_merge_task_metadata_warns_on_every_access(circuit_rx_parametrized_fixture):
    """Every access to task_metadata on a merged result emits a warning."""
    binding = CircuitBinding(circuit_rx_parametrized_fixture, input_sets={"theta": [0.1, 0.2]})
    ps = ProgramSet(binding)
    subs, index_map = ps.split(1)
    sub_results = [_build_sub_quantum_result(sub, [[_make_exec_result(0)]]) for sub in subs]
    merged = ProgramSetQuantumTaskResult.merge(sub_results, ps, index_map)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _ = merged.task_metadata
        _ = merged.task_metadata
        _ = merged.task_metadata.id
    user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
    assert len(user_warnings) == 3
    for w in user_warnings:
        assert "synthesized from multiple underlying tasks" in str(w.message)


def test_from_object_composite_additional_metadata_does_not_warn(circuit_rx_parametrized_fixture):
    """A CompositeEntry on a non-merged result returns its actual additional_metadata
    without warning."""
    binding = CircuitBinding(circuit_rx_parametrized_fixture, input_sets={"theta": [0.1, 0.2]})
    ps = ProgramSet(binding)
    result = _build_sub_quantum_result(ps, [[_make_exec_result(0), _make_exec_result(1)]])
    composite = result[0]
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # any UserWarning becomes a test failure
        meta = composite.additional_metadata
        _ = composite.additional_metadata  # repeat read also silent
    assert meta is not None  # populated from the wire fixture


def test_merge_composite_additional_metadata_warns_on_every_access(
    circuit_rx_parametrized_fixture,
):
    """Every access to additional_metadata on a merged CompositeEntry emits a
    warning, and the value is None."""
    binding = CircuitBinding(circuit_rx_parametrized_fixture, input_sets={"theta": [0.1, 0.2]})
    ps = ProgramSet(binding)
    subs, index_map = ps.split(1)
    sub_results = [_build_sub_quantum_result(sub, [[_make_exec_result(0)]]) for sub in subs]
    merged = ProgramSetQuantumTaskResult.merge(sub_results, ps, index_map)
    composite = merged[0]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        a = composite.additional_metadata
        b = composite.additional_metadata
    user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
    assert len(user_warnings) == 2
    for w in user_warnings:
        assert "additional_metadata for a CompositeEntry on a merged" in str(w.message)
    assert a is None and b is None


def test_merge_does_not_warn_when_reading_inputs_during_construction(
    circuit_rx_parametrized_fixture,
):
    """If an already-merged result is fed back into ``merge`` as an input, the
    internal read of ``task_metadata`` to build the aggregated metadata must not
    trigger that input's task_metadata warning."""
    binding = CircuitBinding(circuit_rx_parametrized_fixture, input_sets={"theta": [0.1, 0.2]})
    ps = ProgramSet(binding)
    subs, index_map = ps.split(1)
    sub_results = [_build_sub_quantum_result(sub, [[_make_exec_result(0)]]) for sub in subs]
    inner_merged = ProgramSetQuantumTaskResult.merge(sub_results, ps, index_map)

    # Re-merging a single already-merged result is degenerate but exercises the
    # internal ``task_metadata`` reads inside merge.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ProgramSetQuantumTaskResult.merge([inner_merged], ps, [list(range(ps.total_executables))])
    user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
    # No warning should fire from inside merge itself.
    assert user_warnings == [], (
        f"merge emitted unexpected warnings during construction: "
        f"{[str(w.message) for w in user_warnings]}"
    )


def ghz_test(n):
    """Local ghz helper so tests don't depend on program_set_test_utils."""
    circuit = Circuit().h(0)
    for i in range(n - 1):
        circuit.cnot(i, i + 1)
    return circuit
