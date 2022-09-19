# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from typing import List, Union

from oqpy import BitVar, Program
from oqpy.vendor.openpulse import ast
from oqpy.vendor.openpulse.printer import dumps
from oqpy.vendor.openqasm3.visitor import QASMTransformer

from braket.pulse.frame import Frame
from braket.pulse.waveforms import Waveform


class PulseSequence:
    """
    A representation of a collection of instructions to be performed on a quantum device
    and the requested results.
    """

    def __init__(self):
        self._capture_v0_count = 0
        self._program = Program()

    def set_frequency(self, frame: Frame, frequency: float) -> PulseSequence:
        """
        Adds an instruction to set the frequency of the frame to the specified `frequency` value.

        Args:
            frame (Frame): Frame for which the frequency needs to be set.
            frequency (float): frequency value to set for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        self._program.set_frequency(frame=frame, freq=frequency)
        return self

    def shift_frequency(self, frame: Frame, frequency: float) -> PulseSequence:
        """
        Adds an instruction to shift the frequency of the frame by the specified `frequency` value.

        Args:
            frame (Frame): Frame for which the frequency needs to be shifted.
            frequency (float): frequency value by which to shift the frequency for the specified
                frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        self._program.shift_frequency(frame=frame, freq=frequency)
        return self

    def set_phase(self, frame: Frame, phase: float) -> PulseSequence:
        """
        Adds an instruction to set the phase of the frame to the specified `phase` value.

        Args:
            frame (Frame): Frame for which the frequency needs to be set.
            phase (float): phase value to set for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        self._program.set_phase(frame=frame, phase=phase)
        return self

    def shift_phase(self, frame: Frame, phase: float) -> PulseSequence:
        """
        Adds an instruction to shift the phase of the frame by the specified `phase` value.

        Args:
            frame (Frame): Frame for which the phase needs to be shifted.
            phase (float): phase value by which to shift the phase for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        self._program.shift_phase(frame=frame, phase=phase)
        return self

    def set_scale(self, frame: Frame, scale: float) -> PulseSequence:
        """
        Adds an instruction to set the scale on the frame to the specified `scale` value.

        Args:
            frame (Frame): Frame for which the scale needs to be set.
            scale (float): scale value to set on the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        self._program.set_scale(frame=frame, scale=scale)
        return self

    def delay(self, frames: Union[Frame, List[Frame]], duration: float) -> PulseSequence:
        """
        Adds an instruction to advance the frame clock by the specified `duration` value.

        Args:
            frames (Union[Frame, List[Frame]]): Frame(s) on which the delay needs to be introduced.
            duration (float): value (in seconds) defining the duration of the delay.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        if not isinstance(frames, List):
            frames = [frames]
        self._program.delay(time=duration, qubits=frames)
        return self

    def barrier(self, frames: List[Frame]) -> PulseSequence:
        """
        Adds an instruction to align the frame clocks to the latest time across all the specified
        frames.

        Args:
            frames (List[Frame]): Frames across which the frame clocks need to be aligned.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        self._program.barrier(qubits=frames)
        return self

    def play(self, frame: Frame, waveform: Waveform) -> PulseSequence:
        """
        Adds an instruction to play the specified waveform on the supplied frame.

        Args:
            frame (Frame): Frame on which the specified waveform signal would be output.
            waveform (Waveform): Waveform envelope specifying the signal to output on the
                specified frame.
        """
        self._program.play(frame=frame, waveform=waveform)
        return self

    def capture_v0(self, frame: Frame) -> PulseSequence:
        """
        Adds an instruction to capture the bit output from measuring the specified frame.

        Args:
            frame (Frame): Frame on which the capture operation needs
                to be performed.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        # TODO: Replace with the public method when available.
        self._program._add_function_statement("capture_v0", [frame])
        self._capture_v0_count += 1
        return self

    def to_ir(self) -> str:
        """Returns a str representing the OpenPulse program encoding the PulseSequence."""
        if self._capture_v0_count:
            register_identifier = "b"
            self._program.declare(
                BitVar[self._capture_v0_count](ident=register_identifier), to_beginning=True
            )
            tree = self._program.to_ast(encal=True, include_externs=False)
            tree = _IRQASMTransformer(register_identifier).visit(tree)
        else:
            tree = self._program.to_ast(encal=True, include_externs=False)
        return dumps(tree, indent="    ").strip()


class _IRQASMTransformer(QASMTransformer):
    """
    QASMTransformer which walks the AST and makes the necessary modifications needed
    for IR generation. Currently, it performs the following operations:
      * Replaces capture_v0 function calls with assignment statements, assigning the
        readout value to a bit register element.
    """

    def __init__(self, register_identifier: str):
        self._register_identifier = register_identifier
        self._capture_v0_count = 0
        super().__init__()

    def visit_ExpressionStatement(self, expression_statement: ast.ExpressionStatement):
        if (
            isinstance(expression_statement.expression, ast.FunctionCall)
            and expression_statement.expression.name.name == "capture_v0"
        ):
            # For capture_v0 nodes, it replaces it with classical assignment statements
            # of the form:
            # b[0] = capture_v0(...)
            # b[1] = capture_v0(...)
            new_val = ast.ClassicalAssignment(
                # Ideally should use IndexedIdentifier here, but this works since it is just
                # for printing.
                ast.Identifier(name=f"{self._register_identifier}[{self._capture_v0_count}]"),
                ast.AssignmentOperator["="],
                expression_statement.expression,
            )
            self._capture_v0_count += 1
            return new_val
        else:
            return expression_statement
