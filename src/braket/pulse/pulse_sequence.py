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

from copy import deepcopy
from typing import Any, Dict, List, Set, Union

from openpulse import ast
from oqpy import BitVar, PhysicalQubits, Program
from oqpy.timing import OQDurationLiteral

from braket.circuits.qubit_set import QubitSet
from braket.parametric.free_parameter import FreeParameter
from braket.parametric.free_parameter_expression import FreeParameterExpression
from braket.parametric.parameterizable import Parameterizable
from braket.pulse.ast.approximation_parser import _ApproximationParser
from braket.pulse.ast.free_parameters import (
    _FreeParameterExpressionIdentifier,
    _FreeParameterTransformer,
)
from braket.pulse.ast.qasm_parser import ast_to_qasm
from braket.pulse.ast.qasm_transformer import _IRQASMTransformer
from braket.pulse.frame import Frame
from braket.pulse.pulse_sequence_trace import PulseSequenceTrace
from braket.pulse.waveforms import Waveform


class PulseSequence:
    """
    A representation of a collection of instructions to be performed on a quantum device
    and the requested results.
    """

    def __init__(self):
        self._capture_v0_count = 0
        self._program = Program()
        self._frames = {}
        self._waveforms = {}
        self._free_parameters = set()

    def to_time_trace(self) -> PulseSequenceTrace:
        """Generate an approximate trace of the amplitude, frequency, phase for each frame
        contained in the PulseSequence, under the action of the instructions contained in
        the pulse sequence.

        Returns:
            PulseSequenceTrace: The approximation information with each attribute
            (amplitude, frequency and phase) mapping a str (frame id) to a TimeSeries
            (containing the time evolution of that attribute).
        """
        parser = _ApproximationParser(deepcopy(self._program), self._frames)
        return PulseSequenceTrace(
            amplitudes=parser.amplitudes, frequencies=parser.frequencies, phases=parser.phases
        )

    @property
    def parameters(self) -> Set[FreeParameter]:
        """Returns the set of `FreeParameter` s in the PulseSequence."""
        return self._free_parameters.copy()

    def set_frequency(
        self, frame: Frame, frequency: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to set the frequency of the frame to the specified `frequency` value.

        Args:
            frame (Frame): Frame for which the frequency needs to be set.
            frequency (Union[float, FreeParameterExpression]): frequency value to set
                for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """

        _validate_uniqueness(self._frames, frame)
        self._program.set_frequency(frame=frame, freq=self._format_parameter_ast(frequency))
        self._frames[frame.id] = frame
        return self

    def shift_frequency(
        self, frame: Frame, frequency: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to shift the frequency of the frame by the specified `frequency` value.

        Args:
            frame (Frame): Frame for which the frequency needs to be shifted.
            frequency (Union[float, FreeParameterExpression]): frequency value by which to shift
                the frequency for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        _validate_uniqueness(self._frames, frame)
        self._program.shift_frequency(frame=frame, freq=self._format_parameter_ast(frequency))
        self._frames[frame.id] = frame
        return self

    def set_phase(
        self, frame: Frame, phase: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to set the phase of the frame to the specified `phase` value.

        Args:
            frame (Frame): Frame for which the frequency needs to be set.
            phase (Union[float, FreeParameterExpression]): phase value to set
                for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        _validate_uniqueness(self._frames, frame)
        self._program.set_phase(frame=frame, phase=self._format_parameter_ast(phase))
        self._frames[frame.id] = frame
        return self

    def shift_phase(
        self, frame: Frame, phase: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to shift the phase of the frame by the specified `phase` value.

        Args:
            frame (Frame): Frame for which the phase needs to be shifted.
            phase (Union[float, FreeParameterExpression]): phase value by which to shift
                the phase for the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        _validate_uniqueness(self._frames, frame)
        self._program.shift_phase(frame=frame, phase=self._format_parameter_ast(phase))
        self._frames[frame.id] = frame
        return self

    def set_scale(
        self, frame: Frame, scale: Union[float, FreeParameterExpression]
    ) -> PulseSequence:
        """
        Adds an instruction to set the scale on the frame to the specified `scale` value.

        Args:
            frame (Frame): Frame for which the scale needs to be set.
            scale (Union[float, FreeParameterExpression]): scale value to set
                on the specified frame.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        _validate_uniqueness(self._frames, frame)
        self._program.set_scale(frame=frame, scale=self._format_parameter_ast(scale))
        self._frames[frame.id] = frame
        return self

    def delay(
        self,
        qubits_or_frames: Union[Frame, List[Frame], QubitSet],
        duration: Union[float, FreeParameterExpression],
    ) -> PulseSequence:
        """
        Adds an instruction to advance the frame clock by the specified `duration` value.

        Args:
            qubits_or_frames (Union[Frame, List[Frame], QubitSet]): Qubits or frame(s) on which
                the delay needs to be introduced.
            duration (Union[float, FreeParameterExpression]): value (in seconds) defining
                the duration of the delay.
        Returns:
            PulseSequence: self, with the instruction added.
        """
        if isinstance(duration, FreeParameterExpression):
            for p in duration.expression.free_symbols:
                self._free_parameters.add(FreeParameter(p.name))
            duration = OQDurationLiteral(duration)
        if not isinstance(qubits_or_frames, QubitSet):
            if not isinstance(qubits_or_frames, list):
                qubits_or_frames = [qubits_or_frames]
            _validate_uniqueness(self._frames, qubits_or_frames)
            self._program.delay(time=duration, qubits_or_frames=qubits_or_frames)
            for frame in qubits_or_frames:
                self._frames[frame.id] = frame
        else:
            physical_qubits = list(PhysicalQubits[int(x)] for x in qubits_or_frames)
            self._program.delay(time=duration, qubits_or_frames=physical_qubits)
        return self

    def barrier(self, qubits_or_frames: Union[List[Frame], QubitSet]) -> PulseSequence:
        """
        Adds an instruction to align the frame clocks to the latest time across all the specified
        frames.

        Args:
            qubits_or_frames (Union[List[Frame], QubitSet]): Qubits or frames which the delay
                needs to be introduced.

        Returns:
            PulseSequence: self, with the instruction added.
        """
        if not isinstance(qubits_or_frames, QubitSet):
            _validate_uniqueness(self._frames, qubits_or_frames)
            self._program.barrier(qubits_or_frames=qubits_or_frames)
            for frame in qubits_or_frames:
                self._frames[frame.id] = frame
        else:
            physical_qubits = list(PhysicalQubits[int(x)] for x in qubits_or_frames)
            self._program.barrier(qubits_or_frames=physical_qubits)
        return self

    def play(self, frame: Frame, waveform: Waveform) -> PulseSequence:
        """Adds an instruction to play the specified waveform on the supplied frame.

        Args:
            frame (Frame): Frame on which the specified waveform signal would be output.
            waveform (Waveform): Waveform envelope specifying the signal to output on the
                specified frame.

        Returns:
            PulseSequence: returns self.
        """
        _validate_uniqueness(self._frames, frame)
        _validate_uniqueness(self._waveforms, waveform)
        self._program.play(frame=frame, waveform=waveform)
        if isinstance(waveform, Parameterizable):
            for param in waveform.parameters:
                if isinstance(param, FreeParameterExpression):
                    for p in param.expression.free_symbols:
                        self._free_parameters.add(FreeParameter(p.name))
        self._frames[frame.id] = frame
        self._waveforms[waveform.id] = waveform
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
        _validate_uniqueness(self._frames, frame)
        self._program.function_call("capture_v0", [frame])
        self._capture_v0_count += 1
        self._frames[frame.id] = frame
        return self

    def make_bound_pulse_sequence(self, param_values: Dict[str, float]) -> PulseSequence:
        """
        Binds FreeParameters based upon their name and values passed in. If parameters
        share the same name, all the parameters of that name will be set to the mapped value.

        Args:
            param_values (Dict[str, float]):  A mapping of FreeParameter names
                to a value to assign to them.

        Returns:
            PulseSequence: Returns a PulseSequence with all present parameters fixed to
            their respective values.
        """
        program = deepcopy(self._program)
        tree: ast.Program = program.to_ast(include_externs=False, ignore_needs_declaration=True)
        new_tree: ast.Program = _FreeParameterTransformer(param_values).visit(tree)

        new_program = Program()
        new_program.declared_vars = program.declared_vars
        new_program.undeclared_vars = program.undeclared_vars
        for x in new_tree.statements:
            new_program._add_statement(x)

        new_pulse_sequence = PulseSequence()
        new_pulse_sequence._program = new_program
        new_pulse_sequence._frames = deepcopy(self._frames)
        new_pulse_sequence._waveforms = {
            wf.id: wf.bind_values(**param_values) if isinstance(wf, Parameterizable) else wf
            for wf in deepcopy(self._waveforms).values()
        }

        # Update waveforms to bind values
        for v in new_program.undeclared_vars:
            if v in self._waveforms:
                new_program.undeclared_vars[v] = new_pulse_sequence._waveforms[
                    v
                ]._to_oqpy_expression()

        new_pulse_sequence._capture_v0_count = self._capture_v0_count
        new_pulse_sequence._free_parameters = set(
            [p for p in self._free_parameters if p.name not in param_values]
        )

        return new_pulse_sequence

    def to_ir(self) -> str:
        """Converts this OpenPulse problem into IR representation.

        Returns:
            str: a str representing the OpenPulse program encoding the PulseSequence.
        """
        program = deepcopy(self._program)
        if self._capture_v0_count:
            register_identifier = "psb"
            program.declare(
                BitVar[self._capture_v0_count](name=register_identifier), to_beginning=True
            )
            tree = program.to_ast(encal=True, include_externs=False)
            tree = _IRQASMTransformer(register_identifier).visit(tree)
        else:
            tree = program.to_ast(encal=True, include_externs=False)
        return ast_to_qasm(tree)

    def _format_parameter_ast(
        self, parameter: Union[float, FreeParameterExpression]
    ) -> Union[float, _FreeParameterExpressionIdentifier]:
        if isinstance(parameter, FreeParameterExpression):
            for p in parameter.expression.free_symbols:
                self._free_parameters.add(FreeParameter(p.name))
            return _FreeParameterExpressionIdentifier(parameter)
        return parameter

    def __call__(self, arg: Any = None, **kwargs) -> PulseSequence:
        """
        Implements the call function to easily make a bound PulseSequence.

        Args:
            arg (Any): A value to bind to all parameters. Defaults to None and
                can be overridden if the parameter is in kwargs.

        Returns:
            PulseSequence: A pulse sequence with the specified parameters bound.
        """
        param_values = dict()
        if arg is not None:
            for param in self.parameters:
                param_values[str(param)] = arg
        for key, val in kwargs.items():
            param_values[str(key)] = val
        return self.make_bound_pulse_sequence(param_values)


def _validate_uniqueness(
    mapping: Dict[str, Any], values: Union[Frame, Waveform, List[Frame], List[Waveform]]
) -> None:
    if not isinstance(values, list):
        values = [values]

    for value in values:
        if value.id in mapping and mapping[value.id] != value:
            raise ValueError(
                f"{value.id} has already been used for defining {mapping[value.id]} "
                f"which differs from {value}"
            )
