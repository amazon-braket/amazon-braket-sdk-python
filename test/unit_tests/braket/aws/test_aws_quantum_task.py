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

import asyncio
import json
import threading
import time
import warnings
from unittest.mock import MagicMock, Mock, patch

import pytest
from common_test_utils import MockS3
from jsonschema import validate

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem, ProblemType
from braket.aws import AwsQuantumTask
from braket.aws.aws_quantum_task import _create_annealing_device_params
from braket.aws.aws_session import AwsSession
from braket.aws.queue_information import QuantumTaskQueueInfo, QueueType
from braket.circuits import Circuit
from braket.circuits.gates import PulseGate
from braket.circuits.serialization import (
    IRType,
    OpenQASMSerializationProperties,
    QubitReferenceType,
    SerializableProgram,
)
from braket.device_schema import GateModelParameters, error_mitigation
from braket.device_schema.dwave import (
    Dwave2000QDeviceParameters,
    DwaveAdvantageDeviceParameters,
    DwaveDeviceParameters,
)
from braket.device_schema.ionq import IonqDeviceParameters
from braket.device_schema.oqc import OqcDeviceParameters
from braket.device_schema.rigetti import RigettiDeviceParameters
from braket.device_schema.simulators import GateModelSimulatorDeviceParameters
from braket.error_mitigation.debias import Debias
from braket.ir.blackbird import Program as BlackbirdProgram
from braket.ir.openqasm import Program as OpenQASMProgram
from braket.pulse import Frame, Port, PulseSequence
from braket.tasks import (
    AnalogHamiltonianSimulationQuantumTaskResult,
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
    PhotonicModelQuantumTaskResult,
)

S3_TARGET = AwsSession.S3DestinationFolder("foo", "bar")

IONQ_ARN = "device/qpu/ionq"
RIGETTI_ARN = "device/qpu/rigetti"
OQC_ARN = "device/qpu/oqc"
SIMULATOR_ARN = "device/quantum-simulator"
XANADU_ARN = "device/qpu/xanadu"

DEVICE_PARAMETERS = [
    (IONQ_ARN, IonqDeviceParameters),
    (RIGETTI_ARN, RigettiDeviceParameters),
    (OQC_ARN, OqcDeviceParameters),
    (SIMULATOR_ARN, GateModelSimulatorDeviceParameters),
]


@pytest.fixture
def aws_session():
    mock = Mock()
    _mock_metadata(mock, "RUNNING")
    return mock


@pytest.fixture
def quantum_task(aws_session):
    return AwsQuantumTask("foo:bar:arn", aws_session, poll_timeout_seconds=2)


@pytest.fixture
def quantum_task_quiet(aws_session):
    return AwsQuantumTask("foo:bar:arn", aws_session, poll_timeout_seconds=2, quiet=True)


@pytest.fixture
def circuit_task(aws_session):
    return AwsQuantumTask("foo:bar:arn", aws_session, poll_timeout_seconds=4)


@pytest.fixture
def annealing_task(aws_session):
    return AwsQuantumTask("foo:bar:arn", aws_session, poll_timeout_seconds=2)


@pytest.fixture
def photonic_model_task(aws_session):
    return AwsQuantumTask("foo:bar:arn", aws_session, poll_timeout_seconds=2)


@pytest.fixture
def arn():
    return "foo:bar:arn"


@pytest.fixture
def circuit():
    return Circuit().h(0).cnot(0, 1)


@pytest.fixture
def problem():
    return Problem(ProblemType.ISING, linear={1: 3.14}, quadratic={(1, 2): 10.08})


@pytest.fixture
def openqasm_program():
    return OpenQASMProgram(source="OPENQASM 3.0; h $0;")


class DummySerializableProgram(SerializableProgram):
    def __init__(self, source: str):
        self.source = source

    def to_ir(self, ir_type: IRType = IRType.OPENQASM) -> str:
        return self.source


@pytest.fixture
def serializable_program():
    return DummySerializableProgram(source="OPENQASM 3.0; h $0;")


@pytest.fixture
def blackbird_program():
    return BlackbirdProgram(source="Vac | q[0]")


@pytest.fixture
def pulse_sequence():
    return PulseSequence().set_frequency(
        Frame(
            frame_id="predefined_frame_1",
            frequency=2e9,
            port=Port(port_id="device_port_x0", dt=1e-9, properties={}),
            phase=0,
            is_predefined=True,
        ),
        6e6,
    )


@pytest.fixture
def pulse_gate(pulse_sequence):
    return PulseGate(pulse_sequence, 1, "my_PG")


@pytest.fixture
def em():
    return Debias()


@pytest.fixture
def ahs_problem():
    mock = Mock(spec=AnalogHamiltonianSimulation)
    mock.to_ir.return_value.json.return_value = "Test AHS Problem"
    return mock


def test_equality(arn, aws_session):
    quantum_task_1 = AwsQuantumTask(arn, aws_session)
    quantum_task_2 = AwsQuantumTask(arn, aws_session)
    other_quantum_task = AwsQuantumTask("different:arn", aws_session)
    non_quantum_task = quantum_task_1.id

    assert quantum_task_1 == quantum_task_2
    assert quantum_task_1 is not quantum_task_2
    assert quantum_task_1 != other_quantum_task
    assert quantum_task_1 != non_quantum_task


def test_str(quantum_task):
    expected = f"AwsQuantumTask('id/taskArn':'{quantum_task.id}')"
    assert str(quantum_task) == expected


def test_hash(quantum_task):
    assert hash(quantum_task) == hash(quantum_task.id)


def test_id_getter(arn, aws_session):
    quantum_task = AwsQuantumTask(arn, aws_session)
    assert quantum_task.id == arn


@pytest.mark.xfail(raises=AttributeError)
def test_no_id_setter(quantum_task):
    quantum_task.id = 123


def test_no_unknown_kwargs_no_warnings(arn, aws_session):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        AwsQuantumTask(arn, aws_session)


def test_unknown_kwarg_warning(arn, aws_session):
    with pytest.warns(UserWarning):
        AwsQuantumTask(arn, aws_session, unknown_kwarg=123)


def test_metadata(quantum_task):
    metadata_1 = {"status": "RUNNING"}
    quantum_task._aws_session.get_quantum_task.return_value = metadata_1
    assert quantum_task.metadata() == metadata_1
    quantum_task._aws_session.get_quantum_task.assert_called_with(quantum_task.id)

    metadata_2 = {"status": "COMPLETED"}
    quantum_task._aws_session.get_quantum_task.return_value = metadata_2
    assert quantum_task.metadata(use_cached_value=True) == metadata_1


def test_metadata_call_if_none(quantum_task):
    metadata_1 = {"status": "RUNNING"}
    quantum_task._aws_session.get_quantum_task.return_value = metadata_1
    assert quantum_task.metadata(use_cached_value=True) == metadata_1
    quantum_task._aws_session.get_quantum_task.assert_called_with(quantum_task.id)


def test_has_reservation_arn_from_metadata(quantum_task):
    metadata_true = {
        "associations": [
            {
                "arn": "123",
                "type": "RESERVATION_TIME_WINDOW_ARN",
            }
        ]
    }
    assert quantum_task._has_reservation_arn_from_metadata(metadata_true)

    metadata_false = {
        "status": "RUNNING",
        "associations": [
            {
                "arn": "123",
                "type": "other",
            }
        ],
    }
    assert not quantum_task._has_reservation_arn_from_metadata(metadata_false)


def test_queue_position(quantum_task):
    state_1 = "QUEUED"
    _mock_metadata(quantum_task._aws_session, state_1)
    assert quantum_task.queue_position() == QuantumTaskQueueInfo(
        queue_type=QueueType.NORMAL, queue_position="2", message=None
    )

    state_2 = "COMPLETED"
    message = (
        f"'Task is in {state_2} status. AmazonBraket does not show queue position for this status.'"
    )
    _mock_metadata(quantum_task._aws_session, state_2)
    assert quantum_task.queue_position() == QuantumTaskQueueInfo(
        queue_type=QueueType.NORMAL, queue_position=None, message=message
    )


def test_queued_quiet(quantum_task_quiet):
    state_1 = "QUEUED"
    _mock_metadata(quantum_task_quiet._aws_session, state_1)
    assert quantum_task_quiet.queue_position() == QuantumTaskQueueInfo(
        queue_type=QueueType.NORMAL, queue_position="2", message=None
    )

    state_2 = "COMPLETED"
    message = (
        f"'Task is in {state_2} status. AmazonBraket does not show queue position for this status.'"
    )
    _mock_metadata(quantum_task_quiet._aws_session, state_2)
    assert quantum_task_quiet.queue_position() == QuantumTaskQueueInfo(
        queue_type=QueueType.NORMAL, queue_position=None, message=message
    )


def test_state(quantum_task):
    state_1 = "RUNNING"
    _mock_metadata(quantum_task._aws_session, state_1)
    assert quantum_task.state() == state_1
    quantum_task._aws_session.get_quantum_task.assert_called_with(quantum_task.id)

    state_2 = "COMPLETED"
    _mock_metadata(quantum_task._aws_session, state_2)
    assert quantum_task.state(use_cached_value=True) == state_1

    state_3 = "FAILED"
    _mock_metadata(quantum_task._aws_session, state_3)
    assert quantum_task.state() == state_3

    state_4 = "CANCELLED"
    _mock_metadata(quantum_task._aws_session, state_4)
    assert quantum_task.state() == state_4


def test_cancel(quantum_task):
    future = quantum_task.async_result()

    assert not future.done()
    quantum_task.cancel()

    assert quantum_task.result() is None
    assert future.cancelled()
    quantum_task._aws_session.cancel_quantum_task.assert_called_with(quantum_task.id)


def test_cancel_without_fetching_result(quantum_task):
    quantum_task.cancel()

    assert quantum_task.result() is None
    assert quantum_task._future.cancelled()
    quantum_task._aws_session.cancel_quantum_task.assert_called_with(quantum_task.id)


def asyncio_get_event_loop_side_effect(*args, **kwargs):
    yield ValueError("unit-test-exception")
    mock = MagicMock()
    while True:
        yield mock


@patch("braket.aws.aws_quantum_task.asyncio")
def test_initialize_asyncio_event_loop_if_required(mock_asyncio, quantum_task):
    mock_asyncio.get_event_loop.side_effect = asyncio_get_event_loop_side_effect()
    mock_asyncio.set_event_loop.return_value = MagicMock()
    mock_asyncio.new_event_loop.return_value = MagicMock()

    quantum_task._get_future()

    assert mock_asyncio.get_event_loop.call_count == 2
    assert mock_asyncio.set_event_loop.call_count == 1
    assert mock_asyncio.new_event_loop.call_count == 1


def test_result_circuit(circuit_task):
    _mock_metadata(circuit_task._aws_session, "COMPLETED")
    _mock_s3(circuit_task._aws_session, MockS3.MOCK_S3_RESULT_GATE_MODEL)

    expected = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_GATE_MODEL)
    assert circuit_task.result() == expected

    s3_bucket = circuit_task.metadata()["outputS3Bucket"]
    s3_object_key = circuit_task.metadata()["outputS3Directory"]
    circuit_task._aws_session.retrieve_s3_object_body.assert_called_with(
        s3_bucket, f"{s3_object_key}/results.json"
    )


def test_result_annealing(annealing_task):
    _mock_metadata(annealing_task._aws_session, "COMPLETED")
    _mock_s3(annealing_task._aws_session, MockS3.MOCK_S3_RESULT_ANNEALING)

    expected = AnnealingQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_ANNEALING)
    assert annealing_task.result() == expected

    s3_bucket = annealing_task.metadata()["outputS3Bucket"]
    s3_object_key = annealing_task.metadata()["outputS3Directory"]
    annealing_task._aws_session.retrieve_s3_object_body.assert_called_with(
        s3_bucket, f"{s3_object_key}/results.json"
    )


def test_result_photonic_model(photonic_model_task):
    _mock_metadata(photonic_model_task._aws_session, "COMPLETED")
    _mock_s3(photonic_model_task._aws_session, MockS3.MOCK_S3_RESULT_PHOTONIC_MODEL)

    expected = PhotonicModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_PHOTONIC_MODEL)
    assert photonic_model_task.result() == expected

    s3_bucket = photonic_model_task.metadata()["outputS3Bucket"]
    s3_object_key = photonic_model_task.metadata()["outputS3Directory"]
    photonic_model_task._aws_session.retrieve_s3_object_body.assert_called_with(
        s3_bucket, f"{s3_object_key}/results.json"
    )


def test_result_analog_hamiltonian_simulation(quantum_task):
    _mock_metadata(quantum_task._aws_session, "COMPLETED")
    _mock_s3(quantum_task._aws_session, MockS3.MOCK_S3_RESULT_ANALOG_HAMILTONIAN_SIMULTION)

    expected = AnalogHamiltonianSimulationQuantumTaskResult.from_string(
        MockS3.MOCK_S3_RESULT_ANALOG_HAMILTONIAN_SIMULTION
    )
    assert quantum_task.result() == expected

    s3_bucket = quantum_task.metadata()["outputS3Bucket"]
    s3_object_key = quantum_task.metadata()["outputS3Directory"]
    quantum_task._aws_session.retrieve_s3_object_body.assert_called_with(
        s3_bucket, f"{s3_object_key}/results.json"
    )


@pytest.mark.xfail(raises=TypeError)
def test_result_invalid_type(circuit_task):
    _mock_metadata(circuit_task._aws_session, "COMPLETED")
    _mock_s3(circuit_task._aws_session, json.dumps(MockS3.MOCK_TASK_METADATA))
    circuit_task.result()


def test_result_circuit_cached(circuit_task):
    _mock_metadata(circuit_task._aws_session, "COMPLETED")
    expected = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_GATE_MODEL)
    circuit_task._result = expected
    assert circuit_task.result() == expected
    assert not circuit_task._aws_session.retrieve_s3_object_body.called


def test_no_result(circuit_task):
    _mock_metadata(circuit_task._aws_session, "FAILED")
    circuit_task._result = None
    assert circuit_task.result() is None
    assert not circuit_task._aws_session.retrieve_s3_object_body.called


@pytest.mark.parametrize(
    "result_string",
    [MockS3.MOCK_S3_RESULT_GATE_MODEL, MockS3.MOCK_S3_RESULT_GATE_MODEL_WITH_RESULT_TYPES],
)
def test_result_cached_future(circuit_task, result_string):
    _mock_metadata(circuit_task._aws_session, "COMPLETED")
    _mock_s3(circuit_task._aws_session, result_string)
    circuit_task.result()

    _mock_s3(circuit_task._aws_session, "")
    expected = GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_GATE_MODEL)
    assert circuit_task.result() == expected


@pytest.mark.parametrize(
    "status, result",
    [
        ("COMPLETED", GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_GATE_MODEL)),
        ("FAILED", None),
    ],
)
def test_async_result(circuit_task, status, result):
    def set_result_from_callback(future):
        # Set the result_from_callback variable in the enclosing functions scope
        nonlocal result_from_callback
        result_from_callback = future.result()

    _mock_metadata(circuit_task._aws_session, "RUNNING")
    _mock_s3(circuit_task._aws_session, MockS3.MOCK_S3_RESULT_GATE_MODEL)

    future = circuit_task.async_result()

    # test the different ways to get the result from async

    # via callback
    result_from_callback = None
    future.add_done_callback(set_result_from_callback)

    # via asyncio waiting for result
    _mock_metadata(circuit_task._aws_session, status)
    event_loop = asyncio.get_event_loop()
    result_from_waiting = event_loop.run_until_complete(future)

    # via future.result(). Note that this would fail if the future is not complete.
    result_from_future = future.result()

    assert result_from_callback == result
    assert result_from_waiting == result
    assert result_from_future == result


@pytest.mark.parametrize(
    "status, result",
    [
        ("COMPLETED", GateModelQuantumTaskResult.from_string(MockS3.MOCK_S3_RESULT_GATE_MODEL)),
        ("FAILED", None),
    ],
)
def test_async_result_queued(circuit_task, status, result):
    def set_result_from_callback(future):
        # Set the result_from_callback variable in the enclosing functions scope
        nonlocal result_from_callback
        result_from_callback = future.result()

    _mock_metadata(circuit_task._aws_session, "QUEUED")
    _mock_s3(circuit_task._aws_session, MockS3.MOCK_S3_RESULT_GATE_MODEL)

    future = circuit_task.async_result()

    # test the different ways to get the result from async

    # via callback
    result_from_callback = None
    future.add_done_callback(set_result_from_callback)

    # via asyncio waiting for result
    _mock_metadata(circuit_task._aws_session, status)
    event_loop = asyncio.get_event_loop()
    result_from_waiting = event_loop.run_until_complete(future)

    # via future.result(). Note that this would fail if the future is not complete.
    result_from_future = future.result()

    assert result_from_callback == result
    assert result_from_waiting == result
    assert result_from_future == result


def test_failed_task(quantum_task):
    _mock_metadata(quantum_task._aws_session, "FAILED")
    _mock_s3(quantum_task._aws_session, MockS3.MOCK_S3_RESULT_GATE_MODEL)
    result = quantum_task.result()
    assert result is None


def test_timeout_completed(aws_session):
    _mock_metadata(aws_session, "RUNNING")
    _mock_s3(aws_session, MockS3.MOCK_S3_RESULT_GATE_MODEL)

    # Setup the poll timing such that the timeout will occur after one API poll
    quantum_task = AwsQuantumTask(
        "foo:bar:arn",
        aws_session,
        poll_timeout_seconds=0.5,
        poll_interval_seconds=1,
    )
    assert quantum_task.result() is None
    _mock_metadata(aws_session, "COMPLETED")
    assert quantum_task.state() == "COMPLETED"
    assert quantum_task.result() == GateModelQuantumTaskResult.from_string(
        MockS3.MOCK_S3_RESULT_GATE_MODEL
    )
    # Cached status is still COMPLETED, so result should be fetched
    _mock_metadata(aws_session, "RUNNING")
    quantum_task._result = None
    assert quantum_task.result() == GateModelQuantumTaskResult.from_string(
        MockS3.MOCK_S3_RESULT_GATE_MODEL
    )


def test_timeout_no_result_terminal_state(aws_session):
    _mock_metadata(aws_session, "RUNNING")
    _mock_s3(aws_session, MockS3.MOCK_S3_RESULT_GATE_MODEL)

    # Setup the poll timing such that the timeout will occur after one API poll
    quantum_task = AwsQuantumTask(
        "foo:bar:arn",
        aws_session,
        poll_timeout_seconds=0.5,
        poll_interval_seconds=1,
    )
    assert quantum_task.result() is None

    _mock_metadata(aws_session, "FAILED")
    assert quantum_task.result() is None


@pytest.mark.xfail(raises=ValueError)
def test_create_invalid_s3_folder(aws_session, arn, circuit):
    AwsQuantumTask.create(aws_session, arn, circuit, ("bucket",), 1000)


@pytest.mark.xfail(raises=TypeError)
def test_create_invalid_task_specification(aws_session, arn):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    AwsQuantumTask.create(aws_session, arn, "foo", S3_TARGET, 1000)


def test_create_openqasm_program(aws_session, arn, openqasm_program):
    aws_session.create_quantum_task.return_value = arn
    shots = 21
    AwsQuantumTask.create(aws_session, SIMULATOR_ARN, openqasm_program, S3_TARGET, shots)

    _assert_create_quantum_task_called_with(
        aws_session,
        SIMULATOR_ARN,
        openqasm_program.json(),
        S3_TARGET,
        shots,
    )


def test_create_openqasm_program_em(aws_session, arn, openqasm_program, em):
    aws_session.create_quantum_task.return_value = arn
    shots = 21
    AwsQuantumTask.create(
        aws_session,
        IONQ_ARN,
        openqasm_program,
        S3_TARGET,
        shots,
        device_parameters={"errorMitigation": em},
    )
    _assert_create_quantum_task_called_with(
        aws_session,
        IONQ_ARN,
        openqasm_program.json(),
        S3_TARGET,
        shots,
        device_parameters=IonqDeviceParameters(
            paradigmParameters=GateModelParameters(qubitCount=0),
            errorMitigation=[error_mitigation.Debias()],
        ),
    )


def test_create_openqasm_program_em_serialized(aws_session, arn, openqasm_program, em):
    aws_session.create_quantum_task.return_value = arn
    shots = 21
    AwsQuantumTask.create(
        aws_session,
        IONQ_ARN,
        openqasm_program,
        S3_TARGET,
        shots,
        device_parameters={"errorMitigation": em.serialize()},
    )
    _assert_create_quantum_task_called_with(
        aws_session,
        IONQ_ARN,
        openqasm_program.json(),
        S3_TARGET,
        shots,
        device_parameters=IonqDeviceParameters(
            paradigmParameters=GateModelParameters(qubitCount=0),
            errorMitigation=[error_mitigation.Debias()],
        ),
    )


def test_create_serializable_program(aws_session, arn, serializable_program):
    aws_session.create_quantum_task.return_value = arn
    shots = 21
    AwsQuantumTask.create(aws_session, SIMULATOR_ARN, serializable_program, S3_TARGET, shots)

    _assert_create_quantum_task_called_with(
        aws_session,
        SIMULATOR_ARN,
        OpenQASMProgram(source=serializable_program.to_ir()).json(),
        S3_TARGET,
        shots,
    )


def test_create_blackbird_program(aws_session, arn, blackbird_program):
    aws_session.create_quantum_task.return_value = arn
    shots = 21
    AwsQuantumTask.create(aws_session, XANADU_ARN, blackbird_program, S3_TARGET, shots)

    _assert_create_quantum_task_called_with(
        aws_session,
        XANADU_ARN,
        blackbird_program.json(),
        S3_TARGET,
        shots,
    )


def test_create_ahs_problem(aws_session, arn, ahs_problem):
    aws_session.create_quantum_task.return_value = arn
    shots = 21
    AwsQuantumTask.create(aws_session, SIMULATOR_ARN, ahs_problem, S3_TARGET, shots)

    _assert_create_quantum_task_called_with(
        aws_session,
        SIMULATOR_ARN,
        ahs_problem.to_ir().json(),
        S3_TARGET,
        shots,
    )


def test_create_task_with_reservation_arn(aws_session, arn, ahs_problem):
    aws_session.create_quantum_task.return_value = arn
    shots = 21
    reservation_arn = (
        "arn:aws:braket:us-west-2:123456789123:reservation/a1b123cd-45e6-789f-gh01-i234567jk8l9"
    )
    AwsQuantumTask.create(
        aws_session,
        SIMULATOR_ARN,
        ahs_problem,
        S3_TARGET,
        shots,
        reservation_arn=reservation_arn,
    )

    _assert_create_quantum_task_called_with(
        aws_session,
        SIMULATOR_ARN,
        ahs_problem.to_ir().json(),
        S3_TARGET,
        shots,
        reservation_arn=reservation_arn,
    )


def test_create_pulse_sequence(aws_session, arn, pulse_sequence):
    expected_openqasm = "\n".join([
        "OPENQASM 3.0;",
        "cal {",
        "    set_frequency(predefined_frame_1, 6000000.0);",
        "}",
    ])
    expected_program = OpenQASMProgram(source=expected_openqasm, inputs={})

    aws_session.create_quantum_task.return_value = arn
    AwsQuantumTask.create(aws_session, SIMULATOR_ARN, pulse_sequence, S3_TARGET, 10)

    _assert_create_quantum_task_called_with(
        aws_session,
        SIMULATOR_ARN,
        expected_program.json(),
        S3_TARGET,
        10,
    )


@pytest.mark.parametrize("device_arn,device_parameters_class", DEVICE_PARAMETERS)
def test_create_pulse_gate_circuit(
    aws_session, arn, pulse_sequence, device_arn, device_parameters_class
):
    pulse_gate_circuit = Circuit().pulse_gate([0, 1], pulse_sequence, "my_PG")
    expected_openqasm = "\n".join((
        "OPENQASM 3.0;",
        "bit[2] b;",
        "cal {",
        "    set_frequency(predefined_frame_1, 6000000.0);",
        "}",
        "b[0] = measure $0;",
        "b[1] = measure $1;",
    ))

    expected_program = OpenQASMProgram(source=expected_openqasm, inputs={})

    aws_session.create_quantum_task.return_value = arn
    AwsQuantumTask.create(aws_session, device_arn, pulse_gate_circuit, S3_TARGET, 10)

    _assert_create_quantum_task_called_with(
        aws_session,
        device_arn,
        expected_program.json(),
        S3_TARGET,
        10,
        device_parameters_class(
            paradigmParameters=GateModelParameters(
                qubitCount=pulse_gate_circuit.qubit_count, disableQubitRewiring=False
            )
        ),
    )


@pytest.mark.parametrize("device_arn,device_parameters_class", DEVICE_PARAMETERS)
def test_create_circuit_with_shots(device_arn, device_parameters_class, aws_session, circuit):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    shots = 53

    task = AwsQuantumTask.create(aws_session, device_arn, circuit, S3_TARGET, shots)
    assert task == AwsQuantumTask(mocked_task_arn, aws_session)
    program = circuit.to_ir(ir_type=IRType.OPENQASM)
    assert program.inputs == {}

    _assert_create_quantum_task_called_with(
        aws_session,
        device_arn,
        program.json(),
        S3_TARGET,
        shots,
        device_parameters_class(
            paradigmParameters=GateModelParameters(
                qubitCount=circuit.qubit_count, disableQubitRewiring=False
            )
        ),
    )


def test_create_circuit_em(aws_session, circuit, em):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    shots = 53

    task = AwsQuantumTask.create(
        aws_session, IONQ_ARN, circuit, S3_TARGET, shots, device_parameters={"errorMitigation": em}
    )
    assert task == AwsQuantumTask(mocked_task_arn, aws_session)
    program = circuit.to_ir(ir_type=IRType.OPENQASM)
    assert program.inputs == {}

    _assert_create_quantum_task_called_with(
        aws_session,
        IONQ_ARN,
        program.json(),
        S3_TARGET,
        shots,
        IonqDeviceParameters(
            paradigmParameters=GateModelParameters(qubitCount=circuit.qubit_count),
            errorMitigation=[error_mitigation.Debias()],
        ),
    )


@pytest.mark.parametrize("device_arn,device_parameters_class", DEVICE_PARAMETERS)
def test_create_circuit_with_input_params(
    device_arn, device_parameters_class, aws_session, circuit
):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    shots = 53
    inputs = {"beta": 3}

    task = AwsQuantumTask.create(aws_session, device_arn, circuit, S3_TARGET, shots, inputs=inputs)
    assert task == AwsQuantumTask(mocked_task_arn, aws_session)
    program = circuit.to_ir(ir_type=IRType.OPENQASM)
    assert program.inputs == {}
    program.inputs.update(inputs)

    _assert_create_quantum_task_called_with(
        aws_session,
        device_arn,
        program.json(),
        S3_TARGET,
        shots,
        device_parameters_class(
            paradigmParameters=GateModelParameters(
                qubitCount=circuit.qubit_count, disableQubitRewiring=False
            )
        ),
    )


@pytest.mark.parametrize(
    "device_arn,device_parameters_class", [(RIGETTI_ARN, RigettiDeviceParameters)]
)
def test_create_circuit_with_disabled_rewiring(
    device_arn, device_parameters_class, aws_session, circuit
):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    shots = 53

    task = AwsQuantumTask.create(
        aws_session, device_arn, circuit, S3_TARGET, shots, disable_qubit_rewiring=True
    )
    assert task == AwsQuantumTask(mocked_task_arn, aws_session)

    _assert_create_quantum_task_called_with(
        aws_session,
        device_arn,
        circuit.to_ir(
            ir_type=IRType.OPENQASM,
            serialization_properties=OpenQASMSerializationProperties(QubitReferenceType.PHYSICAL),
        ).json(),
        S3_TARGET,
        shots,
        device_parameters_class(
            paradigmParameters=GateModelParameters(
                qubitCount=circuit.qubit_count, disableQubitRewiring=True
            )
        ),
    )


@pytest.mark.parametrize(
    "device_arn,device_parameters_class, disable_qubit_rewiring",
    [(RIGETTI_ARN, RigettiDeviceParameters, True), (RIGETTI_ARN, RigettiDeviceParameters, False)],
)
def test_create_circuit_with_verbatim(
    device_arn, device_parameters_class, disable_qubit_rewiring, aws_session
):
    circ = Circuit().add_verbatim_box(Circuit().h(0))
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    shots = 1337

    task = AwsQuantumTask.create(
        aws_session,
        device_arn,
        circ,
        S3_TARGET,
        shots,
        disable_qubit_rewiring=disable_qubit_rewiring,
    )
    assert task == AwsQuantumTask(mocked_task_arn, aws_session)

    serialization_properties = OpenQASMSerializationProperties(
        qubit_reference_type=QubitReferenceType.PHYSICAL
    )

    _assert_create_quantum_task_called_with(
        aws_session,
        device_arn,
        circ.to_ir(
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
        ).json(),
        S3_TARGET,
        shots,
        device_parameters_class(
            paradigmParameters=GateModelParameters(
                qubitCount=circ.qubit_count, disableQubitRewiring=disable_qubit_rewiring
            )
        ),
    )


@pytest.mark.xfail(raises=ValueError)
def test_create_circuit_with_shots_value_error(aws_session, arn, circuit):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    AwsQuantumTask.create(aws_session, arn, circuit, S3_TARGET, 0)


@pytest.mark.parametrize(
    "device_parameters,arn",
    [
        (
            {
                "providerLevelParameters": {
                    "postprocessingType": "OPTIMIZATION",
                    "annealingOffsets": [3.67, 6.123],
                    "annealingSchedule": [[13.37, 10.08], [3.14, 1.618]],
                    "annealingDuration": 1,
                    "autoScale": False,
                    "beta": 0.2,
                    "chains": [[0, 1, 5], [6]],
                    "compensateFluxDrift": False,
                    "fluxBiases": [1.1, 2.2, 3.3, 4.4],
                    "initialState": [1, 3, 0, 1],
                    "maxResults": 1,
                    "programmingThermalizationDuration": 625,
                    "readoutThermalizationDuration": 256,
                    "reduceIntersampleCorrelation": False,
                    "reinitializeState": True,
                    "resultFormat": "RAW",
                    "spinReversalTransformCount": 100,
                }
            },
            "arn:aws:braket:::device/qpu/d-wave/Advantage_system1",
        ),
        (
            {
                "deviceLevelParameters": {
                    "postprocessingType": "OPTIMIZATION",
                    "beta": 0.2,
                    "annealingOffsets": [3.67, 6.123],
                    "annealingSchedule": [[13.37, 10.08], [3.14, 1.618]],
                    "annealingDuration": 1,
                    "autoScale": False,
                    "chains": [[0, 1, 5], [6]],
                    "compensateFluxDrift": False,
                    "fluxBiases": [1.1, 2.2, 3.3, 4.4],
                    "initialState": [1, 3, 0, 1],
                    "maxResults": 1,
                    "programmingThermalizationDuration": 625,
                    "readoutThermalizationDuration": 256,
                    "reduceIntersampleCorrelation": False,
                    "reinitializeState": True,
                    "resultFormat": "RAW",
                    "spinReversalTransformCount": 100,
                }
            },
            "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
        ),
        pytest.param(
            {
                "deviceLevelParameters": {
                    "postprocessingType": "OPTIMIZATION",
                    "beta": 0.2,
                    "annealingOffsets": [3.67, 6.123],
                    "annealingSchedule": [[13.37, 10.08], [3.14, 1.618]],
                    "annealingDuration": 1,
                    "autoScale": False,
                    "chains": [[0, 1, 5], [6]],
                    "compensateFluxDrift": False,
                    "fluxBiases": [1.1, 2.2, 3.3, 4.4],
                    "initialState": [1, 3, 0, 1],
                    "maxResults": 1,
                    "programmingThermalizationDuration": 625,
                    "readoutThermalizationDuration": 256,
                    "reduceIntersampleCorrelation": False,
                    "reinitializeState": True,
                    "resultFormat": "RAW",
                    "spinReversalTransformCount": 100,
                }
            },
            "arn:aws:braket:::device/qpu/d-wave/Advantage_system1",
            # this doesn't fail... yet
            # marks=pytest.mark.xfail(reason='beta not a valid parameter for Advantage device'),
        ),
        pytest.param(
            {
                "deviceLevelParameters": {
                    "postprocessingType": "OPTIMIZATION",
                    "beta": 0.2,
                    "annealingOffsets": [3.67, 6.123],
                    "annealingSchedule": [[13.37, 10.08], [3.14, 1.618]],
                    "annealingDuration": 1,
                    "autoScale": False,
                    "chains": [[0, 1, 5], [6]],
                    "compensateFluxDrift": False,
                    "fluxBiases": [1.1, 2.2, 3.3, 4.4],
                    "initialState": [1, 3, 0, 1],
                    "maxResults": 1,
                    "programmingThermalizationDuration": 625,
                    "readoutThermalizationDuration": 256,
                    "reduceIntersampleCorrelation": False,
                    "reinitializeState": True,
                    "resultFormat": "RAW",
                    "spinReversalTransformCount": 100,
                }
            },
            "arn:aws:braket:::device/qpu/d-wave/fake_arn",
            marks=pytest.mark.xfail(reason="Bad ARN"),
        ),
        (
            {
                "deviceLevelParameters": {
                    "postprocessingType": "OPTIMIZATION",
                    "annealingOffsets": [3.67, 6.123],
                    "annealingSchedule": [[13.37, 10.08], [3.14, 1.618]],
                    "annealingDuration": 1,
                    "autoScale": False,
                    "beta": 0.2,
                    "chains": [[0, 1, 5], [6]],
                    "compensateFluxDrift": False,
                    "fluxBiases": [1.1, 2.2, 3.3, 4.4],
                    "initialState": [1, 3, 0, 1],
                    "maxResults": 1,
                    "programmingThermalizationDuration": 625,
                    "readoutThermalizationDuration": 256,
                    "reduceIntersampleCorrelation": False,
                    "reinitializeState": True,
                    "resultFormat": "RAW",
                    "spinReversalTransformCount": 100,
                }
            },
            "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
        ),
        (
            DwaveDeviceParameters.parse_obj({
                "providerLevelParameters": {
                    "postprocessingType": "OPTIMIZATION",
                    "annealingOffsets": [3.67, 6.123],
                    "annealingSchedule": [[13.37, 10.08], [3.14, 1.618]],
                    "annealingDuration": 1,
                    "autoScale": False,
                    "beta": 0.2,
                    "chains": [[0, 1, 5], [6]],
                    "compensateFluxDrift": False,
                    "fluxBiases": [1.1, 2.2, 3.3, 4.4],
                    "initialState": [1, 3, 0, 1],
                    "maxResults": 1,
                    "programmingThermalizationDuration": 625,
                    "readoutThermalizationDuration": 256,
                    "reduceIntersampleCorrelation": False,
                    "reinitializeState": True,
                    "resultFormat": "RAW",
                    "spinReversalTransformCount": 100,
                }
            }),
            "arn:aws:braket:::device/qpu/d-wave/Advantage_system1",
        ),
        (
            DwaveDeviceParameters.parse_obj(
                {
                    "deviceLevelParameters": {
                        "postprocessingType": "OPTIMIZATION",
                        "annealingOffsets": [3.67, 6.123],
                        "annealingSchedule": [[13.37, 10.08], [3.14, 1.618]],
                        "annealingDuration": 1,
                        "autoScale": False,
                        "beta": 0.2,
                        "chains": [[0, 1, 5], [6]],
                        "compensateFluxDrift": False,
                        "fluxBiases": [1.1, 2.2, 3.3, 4.4],
                        "initialState": [1, 3, 0, 1],
                        "maxResults": 1,
                        "programmingThermalizationDuration": 625,
                        "readoutThermalizationDuration": 256,
                        "reduceIntersampleCorrelation": False,
                        "reinitializeState": True,
                        "resultFormat": "RAW",
                        "spinReversalTransformCount": 100,
                    }
                },
            ),
            "arn:aws:braket:::device/qpu/d-wave/Advantage_system1",
        ),
        (
            DwaveAdvantageDeviceParameters.parse_obj(
                {
                    "deviceLevelParameters": {
                        "annealingOffsets": [3.67, 6.123],
                        "annealingSchedule": [[13.37, 10.08], [3.14, 1.618]],
                        "annealingDuration": 1,
                        "autoScale": False,
                        "beta": 0.2,
                        "chains": [[0, 1, 5], [6]],
                        "compensateFluxDrift": False,
                        "fluxBiases": [1.1, 2.2, 3.3, 4.4],
                        "initialState": [1, 3, 0, 1],
                        "maxResults": 1,
                        "programmingThermalizationDuration": 625,
                        "readoutThermalizationDuration": 256,
                        "reduceIntersampleCorrelation": False,
                        "reinitializeState": True,
                        "resultFormat": "RAW",
                        "spinReversalTransformCount": 100,
                    }
                },
            ),
            "arn:aws:braket:::device/qpu/d-wave/Advantage_system1",
        ),
        (
            Dwave2000QDeviceParameters.parse_obj({
                "deviceLevelParameters": {
                    "postprocessingType": "OPTIMIZATION",
                    "annealingOffsets": [3.67, 6.123],
                    "annealingSchedule": [[13.37, 10.08], [3.14, 1.618]],
                    "annealingDuration": 1,
                    "autoScale": False,
                    "beta": 0.2,
                    "chains": [[0, 1, 5], [6]],
                    "compensateFluxDrift": False,
                    "fluxBiases": [1.1, 2.2, 3.3, 4.4],
                    "initialState": [1, 3, 0, 1],
                    "maxResults": 1,
                    "programmingThermalizationDuration": 625,
                    "readoutThermalizationDuration": 256,
                    "reduceIntersampleCorrelation": False,
                    "reinitializeState": True,
                    "resultFormat": "RAW",
                    "spinReversalTransformCount": 100,
                }
            }),
            "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
        ),
        (
            Dwave2000QDeviceParameters.parse_obj({"deviceLevelParameters": {}}),
            "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
        ),
        pytest.param(
            {},
            "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
        ),
    ],
)
def test_from_annealing(device_parameters, aws_session, arn, problem):
    mocked_task_arn = "task-arn-1"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    task = AwsQuantumTask.create(
        aws_session,
        arn,
        problem,
        S3_TARGET,
        1000,
        device_parameters=device_parameters,
    )
    assert task == AwsQuantumTask(mocked_task_arn, aws_session)
    annealing_parameters = _create_annealing_device_params(device_parameters, device_arn=arn)
    validate(
        json.loads(annealing_parameters.json(exclude_none=True)), annealing_parameters.schema()
    )
    _assert_create_quantum_task_called_with(
        aws_session,
        arn,
        problem.to_ir().json(),
        S3_TARGET,
        1000,
        annealing_parameters,
    )


@pytest.mark.parametrize("device_arn,device_parameters_class", DEVICE_PARAMETERS)
def test_create_with_tags(device_arn, device_parameters_class, aws_session, circuit):
    mocked_task_arn = "task-arn-tags"
    aws_session.create_quantum_task.return_value = mocked_task_arn
    shots = 53
    tags = {"state": "washington"}

    task = AwsQuantumTask.create(aws_session, device_arn, circuit, S3_TARGET, shots, tags=tags)
    assert task == AwsQuantumTask(mocked_task_arn, aws_session)
    _assert_create_quantum_task_called_with(
        aws_session,
        device_arn,
        circuit.to_ir(ir_type=IRType.OPENQASM).json(),
        S3_TARGET,
        shots,
        device_parameters_class(
            paradigmParameters=GateModelParameters(qubitCount=circuit.qubit_count)
        ),
        tags,
    )


def test_init_new_thread(aws_session, arn):
    tasks_list = []
    threading.Thread(target=_init_and_add_to_list, args=(aws_session, arn, tasks_list)).start()
    time.sleep(0.1)
    assert len(tasks_list) == 1


@patch("braket.aws.aws_quantum_task.boto3.Session")
def test_aws_session_for_task_arn(mock_session):
    region = "us-west-2"
    arn = f"arn:aws:aqx:{region}:account_id:quantum-task:task_id"
    mock_boto_session = Mock()
    mock_session.return_value = mock_boto_session
    mock_boto_session.region_name = region
    aws_session = AwsQuantumTask._aws_session_for_task_arn(arn)
    mock_session.assert_called_with(region_name=region)
    assert aws_session.boto_session == mock_boto_session


def _init_and_add_to_list(aws_session, arn, task_list):
    task_list.append(AwsQuantumTask(arn, aws_session))


def _assert_create_quantum_task_called_with(
    aws_session,
    arn,
    task_description,
    s3_results_prefix,
    shots,
    device_parameters=None,
    tags=None,
    reservation_arn=None,
):
    test_kwargs = {
        "deviceArn": arn,
        "outputS3Bucket": s3_results_prefix[0],
        "outputS3KeyPrefix": s3_results_prefix[1],
        "action": task_description,
        "shots": shots,
    }

    if device_parameters is not None:
        test_kwargs["deviceParameters"] = device_parameters.json(exclude_none=True)
    if tags is not None:
        test_kwargs["tags"] = tags
    if reservation_arn:
        test_kwargs["associations"] = [
            {
                "arn": reservation_arn,
                "type": "RESERVATION_TIME_WINDOW_ARN",
            }
        ]
    aws_session.create_quantum_task.assert_called_with(**test_kwargs)


def _mock_metadata(aws_session, state):
    message = (
        f"'Task is in {state} status. AmazonBraket does not show queue position for this status.'"
    )
    if state in AwsQuantumTask.TERMINAL_STATES or state in ["RUNNING", "CANCELLING"]:
        aws_session.get_quantum_task.return_value = {
            "status": state,
            "outputS3Bucket": S3_TARGET.bucket,
            "outputS3Directory": S3_TARGET.key,
            "queueInfo": {
                "queue": "QUANTUM_TASKS_QUEUE",
                "position": "None",
                "queuePriority": "Normal",
                "message": message,
            },
        }
    else:
        aws_session.get_quantum_task.return_value = {
            "status": state,
            "outputS3Bucket": S3_TARGET.bucket,
            "outputS3Directory": S3_TARGET.key,
            "queueInfo": {
                "queue": "QUANTUM_TASKS_QUEUE",
                "position": "2",
                "queuePriority": "Normal",
            },
        }


def _mock_s3(aws_session, result):
    aws_session.retrieve_s3_object_body.return_value = result


@pytest.mark.parametrize("source_input", [{}, {"gamma": 0.15}, None])
@pytest.mark.parametrize("device_arn", DEVICE_PARAMETERS[0])
def test_program_inputs(aws_session, device_arn, source_input):
    bell_qasm = """
    OPENQASM 3;
    input float theta;
    qubit[2] q;
    bit[2] c;
    h q[0];
    cnot q[0], q[1];
    c = measure q;
    """
    openqasm_program = OpenQASMProgram(source=bell_qasm, inputs=source_input)
    aws_session.create_quantum_task.return_value = arn
    shots = 21
    inputs = {"theta": 0.2}
    AwsQuantumTask.create(
        aws_session, device_arn, openqasm_program, S3_TARGET, shots, inputs=inputs
    )

    assert openqasm_program.inputs == source_input
    inputs_copy = openqasm_program.inputs.copy() if openqasm_program.inputs is not None else {}
    inputs_copy.update(inputs)
    openqasm_program = OpenQASMProgram(source=openqasm_program.source, inputs=inputs_copy)

    _assert_create_quantum_task_called_with(
        aws_session,
        device_arn,
        openqasm_program.json(),
        S3_TARGET,
        shots,
    )
