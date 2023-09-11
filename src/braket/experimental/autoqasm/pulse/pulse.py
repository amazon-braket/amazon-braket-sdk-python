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


"""Pulse instructions that apply to frames or qubits.
"""

import re
from typing import List, Union

import oqpy

from braket.circuits.qubit_set import QubitSet
from braket.experimental.autoqasm import program as aq_program
from braket.experimental.autoqasm.instructions.qubits import (
    QubitIdentifierType,
    is_qubit_identifier_type,
)
from braket.pulse import PulseSequence
from braket.pulse.frame import Frame
from braket.pulse.waveforms import Waveform


def _pulse_instruction(name: str, frame: Frame, *args) -> None:
    """Define a pulse instruction.

    Args:
        name (str): Name of the pulse instruction.
        frame (Frame): Frame for which the instruction is apply to.
    """
    program_conversion_context = aq_program.get_program_conversion_context()
    program_conversion_context._has_pulse_control = True

    pulse_sequence = PulseSequence()
    pulse_sequence._program = program_conversion_context.get_oqpy_program(
        mode=aq_program.ProgramMode.PULSE
    )

    if program_conversion_context._calibration_definitions_processing:
        getattr(pulse_sequence, name)(frame, *args)
    else:
        with oqpy.Cal(pulse_sequence._program):
            getattr(pulse_sequence, name)(frame, *args)


def _physical_qubit_to_braket_qubit(qids: List[str]) -> QubitSet:
    """Convert a physical qubit label to a QubitSet.

    Args:
        qids (List[str]): Physical qubit labels.

    Returns:
        QubitSet: Represent physical qubits.
    """
    braket_qubits = []
    for qid in qids:
        if not (isinstance(qid, str) and re.match(r"\$\d+", qid)):
            raise ValueError(
                f"invalid physical qubit label: '{qid}'. Physical qubit must be labeled as a string"
                "with `$` followed by an integer. For example: `$1`."
            )
        braket_qubits.append(int(qid[1:]))
    return QubitSet(braket_qubits)


def set_frequency(frame: Frame, frequency: float) -> None:
    """Adds an instruction to set the frequency of the frame to the specified `frequency` value.

    Args:
        frame (Frame): Frame for which the frequency needs to be set.
        frequency (float): Frequency value to set for the specified frame.
    """
    _pulse_instruction("set_frequency", frame, frequency)


def shift_frequency(frame: Frame, frequency: float) -> None:
    """Adds an instruction to shift the frequency of the frame by the specified `frequency` value.

    Args:
        frame (Frame): Frame for which the frequency needs to be shifted.
        frequency (float): Frequency value by which to shift the frequency for the specified frame.
    """
    _pulse_instruction("shift_frequency", frame, frequency)


def set_phase(frame: Frame, phase: float) -> None:
    """Adds an instruction to set the phase of the frame to the specified `phase` value.

    Args:
        frame (Frame): Frame for which the frequency needs to be set.
        phase (float): Phase value to set for the specified frame.
    """
    _pulse_instruction("set_phase", frame, phase)


def shift_phase(frame: Frame, phase: float) -> None:
    """Adds an instruction to shift the phase of the frame by the specified `phase` value.

    Args:
        frame (Frame): Frame for which the phase needs to be shifted.
        phase (float): Phase value by which to shift the phase for the specified frame.
    """
    _pulse_instruction("shift_phase", frame, phase)


def set_scale(frame: Frame, scale: float) -> None:
    """Adds an instruction to set the scale on the frame to the specified `scale` value.

    Args:
        frame (Frame): Frame for which the scale needs to be set.
        scale (float): scale value to set on the specified frame.
    """
    _pulse_instruction("set_scale", frame, scale)


def play(frame: Frame, waveform: Waveform) -> None:
    """Adds an instruction to play the specified waveform on the supplied frame.

    Args:
        frame (Frame): Frame on which the specified waveform signal would be output.
        waveform (Waveform): Waveform envelope specifying the signal to output on the specified
            frame.
    """
    _pulse_instruction("play", frame, waveform)


def capture_v0(frame: Frame) -> None:
    """Adds an instruction to capture the bit output from measuring the specified frame.

    Args:
        frame (Frame): Frame on which the capture operation needs to be performed.
    """
    _pulse_instruction("capture_v0", frame)


def delay(
    qubits_or_frames: Union[Frame, List[Frame], QubitIdentifierType, List[QubitIdentifierType]],
    duration: float,
) -> None:
    """Adds an instruction to advance the frame clock by the specified `duration` value.

    Args:
        qubits_or_frames (Union[Frame, List[Frame], QubitIdentifierType, List[QubitIdentifierType]]):
            Qubits or frame(s) on which the delay needs to be introduced.
        duration (float): Value (in seconds) defining the duration of the delay.
    """  # noqa: E501
    if not isinstance(qubits_or_frames, List):
        qubits_or_frames = [qubits_or_frames]
    if all(is_qubit_identifier_type(q) for q in qubits_or_frames):
        qubits_or_frames = _physical_qubit_to_braket_qubit(qubits_or_frames)
    _pulse_instruction("delay", qubits_or_frames, duration)


def barrier(
    qubits_or_frames: Union[Frame, List[Frame], QubitIdentifierType, List[QubitIdentifierType]]
) -> None:
    """Adds an instruction to align the frame clocks to the latest time across all the specified
    frames. When applied on qubits, it prevents compilations across the barrier, if the compiler
    supports barrier.

    Args:
        qubits_or_frames (Union[Frame, List[Frame], QubitIdentifierType, List[QubitIdentifierType]]):
            Qubits or frame(s) on which the barrier needs to be introduced.
    """  # noqa: E501
    if not isinstance(qubits_or_frames, List):
        qubits_or_frames = [qubits_or_frames]
    if all(is_qubit_identifier_type(q) for q in qubits_or_frames):
        qubits_or_frames = _physical_qubit_to_braket_qubit(qubits_or_frames)
    _pulse_instruction("barrier", qubits_or_frames)
