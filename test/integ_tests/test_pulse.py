import math

import numpy as np
import pytest

from braket.aws import AwsDevice, AwsQuantumTask
from braket.circuits import Circuit, Gate, GateCalibrations, QubitSet
from braket.parametric import FreeParameter
from braket.pulse import ArbitraryWaveform, Frame, Port, PulseSequence


@pytest.fixture
def device():
    return AwsDevice("arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-2")


@pytest.fixture
def arbitrary_waveform():
    return ArbitraryWaveform([
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.00017888439538396808,
        0.00046751103636033026,
        0.0011372942989106456,
        0.002577059611929697,
        0.005443941944632366,
        0.010731922770068104,
        0.01976701723583167,
        0.03406712171899736,
        0.05503285980691202,
        0.08350670755829034,
        0.11932853352131022,
        0.16107456696238298,
        0.20614055551722368,
        0.2512065440720643,
        0.292952577513137,
        0.328774403476157,
        0.3572482512275353,
        0.3782139893154499,
        0.3925140937986156,
        0.40154918826437913,
        0.4068371690898149,
        0.4097040514225177,
        0.41114381673553674,
        0.411813599998087,
        0.4121022266390633,
        0.4122174383870584,
        0.41226003881132406,
        0.4122746298554775,
        0.4122792591252675,
        0.4122806196003006,
        0.41228098995582513,
        0.41228108334474756,
        0.4122811051578895,
        0.4122811098772742,
        0.4122811108230642,
        0.4122811109986316,
        0.41228111102881937,
        0.41228111103362725,
        0.4122811110343365,
        0.41228111103443343,
        0.4122811110344457,
        0.4122811110344471,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.41228111103444737,
        0.4122811110344471,
        0.4122811110344457,
        0.41228111103443343,
        0.4122811110343365,
        0.41228111103362725,
        0.41228111102881937,
        0.4122811109986316,
        0.4122811108230642,
        0.4122811098772742,
        0.4122811051578895,
        0.41228108334474756,
        0.41228098995582513,
        0.4122806196003006,
        0.4122792591252675,
        0.4122746298554775,
        0.41226003881132406,
        0.4122174383870584,
        0.4121022266390633,
        0.411813599998087,
        0.41114381673553674,
        0.4097040514225176,
        0.4068371690898149,
        0.40154918826437913,
        0.3925140937986155,
        0.37821398931544986,
        0.3572482512275351,
        0.32877440347615655,
        0.2929525775131368,
        0.2512065440720641,
        0.20614055551722307,
        0.16107456696238268,
        0.11932853352131002,
        0.08350670755829034,
        0.05503285980691184,
        0.03406712171899729,
        0.01976701723583167,
        0.010731922770068058,
        0.005443941944632366,
        0.002577059611929697,
        0.0011372942989106229,
        0.00046751103636033026,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ])


@pytest.fixture
def port():
    return Port("test_port_ff", dt=1e-9)


@pytest.fixture
def frame_id(device):
    return next(iter(device.frames))


@pytest.fixture
def frame(frame_id, port):
    return Frame(frame_id, port, 1e6, is_predefined=True)


@pytest.fixture
def pulse_sequence(frame, arbitrary_waveform):
    return (
        PulseSequence()
        .barrier(qubits_or_frames=[frame])
        .play(frame=frame, waveform=arbitrary_waveform)
    )


def h_gate(q0):
    return Circuit().rz(q0, np.pi).rx(q0, np.pi / 2).rz(q0, np.pi / 2).rx(q0, -np.pi / 2)


def make_pulse(
    q0: str,
    q1: str,
    shift_phases_q0: float,
    shift_phases_q1: float,
    waveform: ArbitraryWaveform,
    device: AwsDevice,
):
    q0_drive_frame = device.frames[f"Transmon_{q0}_charge_tx"]
    q1_drive_frame = device.frames[f"Transmon_{q1}_charge_tx"]
    frames = [q0_drive_frame, q1_drive_frame]

    dt = device.properties.pulse.ports[q0_drive_frame.port.id].dt
    wfm_duration = len(waveform.amplitudes) * dt

    pulse_sequence = (
        PulseSequence()
        .barrier(frames)
        .delay(q0_drive_frame, wfm_duration)
        .shift_phase(q0_drive_frame, shift_phases_q0)
        .delay(q1_drive_frame, wfm_duration)
        .shift_phase(q1_drive_frame, shift_phases_q1)
        .barrier(frames)
    )
    return pulse_sequence


def test_pulse_bell(arbitrary_waveform, device):
    if device.status != "ONLINE":
        pytest.skip("Device not online")
    (
        a,
        b,
    ) = (
        26,
        33,
    )  # qubits used
    p0, p1 = 1.1733407221086924, 6.269846678712192
    theta_0, theta_1 = FreeParameter("theta_0"), FreeParameter("theta_1")
    a_b_waveform = arbitrary_waveform
    pulse = make_pulse(a, b, theta_0, theta_1, a_b_waveform, device)

    bell_pair_with_gates = Circuit().h(a).h(b).iswap(a, b).h(b)
    bell_pair_with_pulses_unbound = (
        h_gate(a) + h_gate(b) + Circuit().pulse_gate([a, b], pulse) + h_gate(b)
    )
    bell_pair_with_pulses = bell_pair_with_pulses_unbound(theta_0=p0, theta_1=p1)

    num_shots = 1000
    gate_task = device.run(bell_pair_with_gates, shots=num_shots, disable_qubit_rewiring=True)
    pulse_task = device.run(bell_pair_with_pulses, shots=num_shots)

    if not device.is_available:
        try:
            assert gate_task.state not in AwsQuantumTask.TERMINAL_STATES
            assert pulse_task.state not in AwsQuantumTask.TERMINAL_STATES
        finally:
            gate_task.cancel()
            pulse_task.cancel()
        return

    gate_measurements = gate_task.result().measurement_counts
    pulse_measurements = pulse_task.result().measurement_counts

    # 1-smoothing to avoid nans for 0 counts
    observed = (
        np.array([pulse_measurements.get(state, 1) for state in ("00", "01", "10", "11")])
        / num_shots
    )
    expected = (
        np.array([gate_measurements.get(state, 1) for state in ("00", "01", "10", "11")])
        / num_shots
    )
    chi_squared = np.sum((observed - expected) ** 2 / expected)
    assert chi_squared < 10  # adjust this threshold if test is flaky


def test_pulse_sequence(arbitrary_waveform, device):
    if device.status != "ONLINE":
        pytest.skip("Device not online")
    (
        a,
        b,
    ) = (
        26,
        33,
    )  # qubits used
    p0, p1 = 1.1733407221086924, 6.269846678712192
    theta_0, theta_1 = FreeParameter("theta_0"), FreeParameter("theta_1")
    a_b_waveform = arbitrary_waveform

    pulse_unbound = make_pulse(a, b, theta_0, theta_1, a_b_waveform, device)

    q0_readout_frame = device.frames[f"Transmon_{a}_readout_rx"]
    q1_readout_frame = device.frames[f"Transmon_{b}_readout_rx"]
    pulses = (
        pulse_unbound(theta_0=p0, theta_1=p1)
        .capture_v0(q0_readout_frame)
        .capture_v0(q1_readout_frame)
    )
    circuit_with_gates = Circuit().iswap(a, b)

    num_shots = 1000
    gate_task = device.run(circuit_with_gates, shots=num_shots, disable_qubit_rewiring=True)
    pulse_task = device.run(pulses, shots=num_shots)

    if not device.is_available:
        try:
            assert gate_task.state not in AwsQuantumTask.TERMINAL_STATES
            assert pulse_task.state not in AwsQuantumTask.TERMINAL_STATES
        finally:
            gate_task.cancel()
            pulse_task.cancel()
        return

    gate_measurements = gate_task.result().measurement_counts
    pulse_measurements = pulse_task.result().measurement_counts

    # 1-smoothing to avoid nans for 0 counts
    observed = (
        np.array([pulse_measurements.get(state, 1) for state in ("00", "01", "10", "11")])
        / num_shots
    )
    expected = (
        np.array([gate_measurements.get(state, 1) for state in ("00", "01", "10", "11")])
        / num_shots
    )
    chi_squared = np.sum((observed - expected) ** 2 / expected)
    assert chi_squared < 10  # adjust this threshold if test is flaky


@pytest.mark.skip(reason="needs to be updated to work correctly on Ankaa-2")
def test_gate_calibration_run(device, pulse_sequence):
    if device.status != "ONLINE":
        pytest.skip("Device not online")
    user_gate_calibrations = GateCalibrations({(Gate.Rx(math.pi / 2), QubitSet(0)): pulse_sequence})
    num_shots = 50
    bell_circuit = Circuit().rx(0, math.pi / 2).rx(1, math.pi / 2).iswap(0, 1).rx(1, -math.pi / 2)
    user_calibration_task = device.run(
        bell_circuit,
        gate_definitions=user_gate_calibrations.pulse_sequences,
        shots=num_shots,
        disable_qubit_rewiring=True,
    )
    device_calibration_task = device.run(
        bell_circuit,
        gate_definitions=device.gate_calibrations.pulse_sequences,
        shots=num_shots,
        disable_qubit_rewiring=True,
    )

    if not device.is_available:
        try:
            assert user_calibration_task.state not in AwsQuantumTask.TERMINAL_STATES
            assert device_calibration_task.state not in AwsQuantumTask.TERMINAL_STATES
        finally:
            user_calibration_task.cancel()
            device_calibration_task.cancel()
        return

    assert user_calibration_task.result().measurement_counts
    assert device_calibration_task.result().measurement_counts
