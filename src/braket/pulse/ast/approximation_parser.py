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

import re
from collections import defaultdict
from collections.abc import KeysView
from dataclasses import dataclass
from typing import Any, ClassVar, Optional, Union

import numpy as np
from openpulse import ast
from openqasm3.visitor import QASMVisitor
from oqpy import Program

from braket.pulse.frame import Frame
from braket.pulse.waveforms import (
    ConstantWaveform,
    DragGaussianWaveform,
    ErfSquareWaveform,
    GaussianWaveform,
    Waveform,
)
from braket.timings.time_series import TimeSeries


@dataclass
class _FrameState:
    dt: float
    frequency: float = 0
    phase: float = 0
    current_time: float = 0
    amplitude: float = 0
    scale: float = 1


@dataclass
class _ParseState:
    variables: dict
    frame_data: dict[str, _FrameState]


class _ApproximationParser(QASMVisitor[_ParseState]):  # noqa: PLR0904
    """Walk the AST and build the output signal amplitude, frequency and phases
    for each channel.
    """

    TIME_UNIT_TO_EXP: ClassVar = {"dt": 4, "ns": 3, "us": 2, "ms": 1, "s": 0}

    def __init__(self, program: Program, frames: dict[str, Frame]):
        self.amplitudes = defaultdict(TimeSeries)
        self.frequencies = defaultdict(TimeSeries)
        self.phases = defaultdict(TimeSeries)
        context = _ParseState(variables={}, frame_data=_init_frame_data(frames))
        self._qubit_frames_mapping: dict[str, list[str]] = _init_qubit_frame_mapping(frames)
        self.visit(program.to_ast(include_externs=False), context)

    def visit(
        self, node: Union[ast.QASMNode, ast.Expression], context: Optional[_ParseState] = None
    ) -> Any:
        """Visit a node.

        Args:
            node (Union[ast.QASMNode, ast.Expression]): The node to visit.
            context (Optional[_ParseState]): The parse state context.

        Returns:
            Any: The parsed return value.
        """
        return super().visit(node, context)

    def _get_frame_parameters(
        self, parameters: list[ast.Expression], context: _ParseState
    ) -> Union[KeysView, list[str]]:
        frame_ids = set()
        for expression in parameters:
            identifier_name = self.visit(expression, context)
            if match := re.search(r"^\$[0-9]+$", identifier_name):
                qubit_number = match.group()[1:]
                frame_ids.update(self._qubit_frames_mapping.get(qubit_number, []))
            else:
                frame_ids.add(identifier_name)
        return frame_ids

    def _delay_frame(self, frame_id: str, to_delay_time: float, context: _ParseState) -> None:
        frame_data = context.frame_data[frame_id]
        if to_delay_time >= frame_data.current_time + frame_data.dt:
            start_time = frame_data.current_time
            self.amplitudes[frame_id].put(start_time, 0)
            self.frequencies[frame_id].put(start_time, frame_data.frequency)
            self.phases[frame_id].put(start_time, frame_data.phase)
        if to_delay_time >= frame_data.current_time + (2 * frame_data.dt):
            end_time = to_delay_time - frame_data.dt
            self.amplitudes[frame_id].put(end_time, 0)
            self.frequencies[frame_id].put(end_time, frame_data.frequency)
            self.phases[frame_id].put(end_time, frame_data.phase)
        context.frame_data[frame_id].current_time = to_delay_time

    def visit_Program(self, node: ast.Program, context: _ParseState = None) -> None:
        """Visit a Program.

        Args:
            node (ast.Program): The program.
            context (_ParseState): The parse state context.
        """
        for statement in node.statements:
            self.visit(statement, context)

    def visit_ExpressionStatement(self, node: ast.ExpressionStatement, context: _ParseState) -> Any:
        """Visit an Expression.

        Args:
            node (ast.ExpressionStatement): The expression.
            context (_ParseState): The parse state context.

        Returns:
            Any: The parsed return value.
        """
        return self.visit(node.expression, context)  # need to check

    def visit_ClassicalDeclaration(
        self, node: ast.ClassicalDeclaration, context: _ParseState
    ) -> Union[dict, None]:
        """Visit a Classical Declaration.
            node.type, node.identifier, node.init_expression
            angle[20] a = 1+2;
            waveform wf = [];
            port a;

        Args:
            node (ast.ClassicalDeclaration): The classical declaration.
            context (_ParseState): The parse state context.

        Raises:
            NotImplementedError: Raised if the node is not a PortType, FrameType, or
                WaveformType.

        Returns:
            Union[dict, None]: Returns a dict if WaveformType, None otherwise.
        """  # noqa: DOC202
        identifier = self.visit(node.identifier, context)
        if type(node.type) is ast.WaveformType:
            context.variables[identifier] = self.visit(node.init_expression, context)
        elif type(node.type) is ast.FrameType:
            pass
        elif type(node.type) is not ast.PortType:
            raise NotImplementedError

    def visit_DelayInstruction(self, node: ast.DelayInstruction, context: _ParseState) -> None:
        """Visit a Delay Instruction.
            node.duration, node.qubits
            delay[100ns] $0;

        Args:
            node (ast.DelayInstruction): The classical declaration.
            context (_ParseState): The parse state context.
        """
        duration = self.visit(node.duration, context)
        frames = self._get_frame_parameters(node.qubits, context)
        if len(frames) == 0:
            # barrier without arguments is applied to all the frames of the context
            frames = list(context.frame_data.keys())
        dts = [context.frame_data[frame_id].dt for frame_id in frames]
        max_time = max(context.frame_data[frame_id].current_time for frame_id in frames)
        # All frames are delayed till the first multiple of the LCM([port.dts])
        # after the longest time of all considered frames
        lcm = _lcm_floats(*dts)
        barrier_time = _ceil_approx(max_time / lcm) * lcm

        for frame_id in frames:
            self._delay_frame(frame_id, barrier_time + duration, context)

    def visit_QuantumBarrier(self, node: ast.QuantumBarrier, context: _ParseState) -> None:
        """Visit a Quantum Barrier.
            barrier $0;
            barrier;
            barrier frame, frame1;

        Args:
            node (ast.QuantumBarrier): The quantum barrier.
            context (_ParseState): The parse state context.
        """
        frames = self._get_frame_parameters(node.qubits, context)
        if len(frames) == 0:
            # barrier without arguments is applied to all the frames of the context
            frames = list(context.frame_data.keys())
        dts = [context.frame_data[frame_id].dt for frame_id in frames]
        max_time = max(context.frame_data[frame_id].current_time for frame_id in frames)
        # All frames are delayed till the first multiple of the LCM([port.dts])
        # after the longest time of all considered frames
        lcm = _lcm_floats(*dts)
        barrier_time = _ceil_approx(max_time / lcm) * lcm

        for frame_id in frames:
            self._delay_frame(frame_id, barrier_time, context)

    def visit_FunctionCall(self, node: ast.FunctionCall, context: _ParseState) -> Any:
        """Visit a Quantum Barrier.
            node.name, node.arguments
            f(args,arg2)

        Args:
            node (ast.FunctionCall): The function call.
            context (_ParseState): The parse state context.

        Returns:
            Any: The parsed return value.
        """
        func_name = node.name.name
        return getattr(self, func_name)(node, context)

    def visit_Identifier(self, node: ast.Identifier, context: _ParseState) -> Any:
        """Visit Identifier.
            node.name
            x
        Args:
            node (ast.Identifier): The identifier.
            context (_ParseState): The parse state context.

        Returns:
            Any: The parsed return value.
        """
        if node.name in context.variables:
            return context.variables[node.name]
        return node.name

    def visit_UnaryExpression(self, node: ast.UnaryExpression, context: _ParseState) -> bool:
        """Visit Unary Expression.
            node.op, node.expression
            ~ ! -

        Args:
            node (ast.UnaryExpression): The unary expression.
            context (_ParseState): The parse state context.

        Returns:
            bool: The parsed boolean operator.

        Raises:
            NotImplementedError: Raised for unsupported boolean operators.
        """
        if node.op == ast.UnaryOperator["-"]:
            return -1 * self.visit(node.expression, context)
        if node.op == ast.UnaryOperator["!"]:
            return not self.visit(node.expression, context)
        if node.op == ast.UnaryOperator["~"]:
            return ~self.visit(node.expression, context)
        raise NotImplementedError

    def visit_BinaryExpression(self, node: ast.BinaryExpression, context: _ParseState) -> Any:  # noqa: C901, PLR0911, PLR0912
        """Visit Binary Expression.
            node.lhs, node.rhs, node.op
            1+2
            a.b
            > < >= <= == != && || | ^ & << >> + - * / % ** .

        Args:
            node (ast.BinaryExpression): The binary expression.
            context (_ParseState): The parse state context.

        Raises:
            NotImplementedError: Raised if the binary operator is not in
                [> < >= <= == != && || | ^ & << >> + - * / % ** ]

        Returns:
            Any: The parsed binary operator.
        """
        lhs = self.visit(node.lhs, context)
        rhs = self.visit(node.rhs, context)

        op = ast.BinaryOperator

        if node.op == op["+"]:
            return lhs + rhs
        if node.op == op["-"]:
            return lhs - rhs
        if node.op == op["*"]:
            return lhs * rhs
        if node.op == op["/"]:
            return lhs / rhs
        if node.op == op["%"]:
            return lhs % rhs
        if node.op == op["**"]:
            return lhs**rhs
        if node.op == op[">"]:
            return lhs > rhs
        if node.op == op["<"]:
            return lhs < rhs
        if node.op == op[">="]:
            return lhs >= rhs
        if node.op == op["<="]:
            return lhs <= rhs
        if node.op == op["=="]:
            return lhs == rhs
        if node.op == op["!="]:
            return lhs != rhs
        if node.op == op["&&"]:
            return lhs and rhs
        if node.op == op["||"]:
            return lhs or rhs
        if node.op == op["|"]:
            return lhs | rhs
        if node.op == op["^"]:
            return lhs ^ rhs
        if node.op == op["&"]:
            return lhs & rhs
        if node.op == op["<<"]:
            return lhs << rhs
        if node.op == op[">>"]:
            return lhs >> rhs
        raise NotImplementedError

    def visit_ArrayLiteral(self, node: ast.ArrayLiteral, context: _ParseState) -> list[Any]:
        """Visit Array Literal.
            node.values
            {1,2,4}

        Args:
            node (ast.ArrayLiteral): The array literal.
            context (_ParseState): The parse state context.

        Returns:
            list[Any]: The parsed ArrayLiteral.
        """
        return [self.visit(e, context) for e in node.values]

    def visit_IntegerLiteral(self, node: ast.IntegerLiteral, context: _ParseState) -> int:
        """Visit Integer Literal.
            node.value
            1
        Args:
            node (ast.IntegerLiteral): The integer literal.
            context (_ParseState): The parse state context.

        Returns:
            int: The parsed int value.
        """
        return int(node.value)

    def visit_ImaginaryLiteral(self, node: ast.ImaginaryLiteral, context: _ParseState) -> complex:
        """Visit Imaginary Number Literal.
            node.value
            1.3im
        Args:
            node (ast.ImaginaryLiteral): The imaginary number literal.
            context (_ParseState): The parse state context.

        Returns:
            complex: The parsed complex value.
        """
        return complex(node.value * 1j)

    def visit_FloatLiteral(self, node: ast.FloatLiteral, context: _ParseState) -> float:
        """Visit Float Literal.
            node.value
            1.1
        Args:
            node (ast.FloatLiteral): The float literal.
            context (_ParseState): The parse state context.

        Returns:
            float: The parsed float value.
        """
        return float(node.value)

    def visit_BooleanLiteral(self, node: ast.BooleanLiteral, context: _ParseState) -> bool:
        """Visit Boolean Literal.
            node.value
            true
        Args:
            node (ast.BooleanLiteral): The boolean literal.
            context (_ParseState): The parse state context.

        Returns:
            bool: The parsed boolean value.
        """
        return bool(node.value)

    def visit_DurationLiteral(self, node: ast.DurationLiteral, context: _ParseState) -> float:
        """Visit Duration Literal.
            node.value, node.unit (node.unit.name, node.unit.value)
            1
        Args:
            node (ast.DurationLiteral): The duration literal.
            context (_ParseState): The parse state context.

        Raises:
            ValueError: Raised based on time unit not being in `self.TIME_UNIT_TO_EXP`.

        Returns:
            float: The duration represented as a float
        """
        if node.unit.name not in self.TIME_UNIT_TO_EXP:
            raise ValueError(f"Unexpected duration specified: {node.unit.name}:{node.unit.value}")
        multiplier = 10 ** (-3 * self.TIME_UNIT_TO_EXP[node.unit.name])
        return multiplier * node.value

    # The following are function call declarations supported by the parser.

    def set_frequency(self, node: ast.FunctionCall, context: _ParseState) -> None:
        """A 'set_frequency' Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.
        """
        frame = self.visit(node.arguments[0], context)
        value = self.visit(node.arguments[1], context)
        context.frame_data[frame].frequency = value

    def shift_frequency(self, node: ast.FunctionCall, context: _ParseState) -> None:
        """A 'shift_frequency' Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.
        """
        frame = self.visit(node.arguments[0], context)
        value = self.visit(node.arguments[1], context)
        context.frame_data[frame].frequency += value

    def set_phase(self, node: ast.FunctionCall, context: _ParseState) -> None:
        """A 'set_phase' Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.
        """
        frame = self.visit(node.arguments[0], context)
        value = self.visit(node.arguments[1], context)
        context.frame_data[frame].phase = value % (2 * np.pi)

    def shift_phase(self, node: ast.FunctionCall, context: _ParseState) -> None:
        """A 'shift_phase' Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.
        """
        frame = self.visit(node.arguments[0], context)
        value = self.visit(node.arguments[1], context)
        context.frame_data[frame].phase += value
        context.frame_data[frame].phase %= 2 * np.pi

    def set_scale(self, node: ast.FunctionCall, context: _ParseState) -> None:
        """A 'set_scale' Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.
        """
        frame = self.visit(node.arguments[0], context)
        value = self.visit(node.arguments[1], context)
        context.frame_data[frame].scale = value

    def swap_phases(self, node: ast.FunctionCall, context: _ParseState) -> None:
        """A 'swap_phases' Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.
        """
        frame1 = self.visit(node.arguments[0], context)
        frame2 = self.visit(node.arguments[1], context)
        phase1 = context.frame_data[frame1].phase
        phase2 = context.frame_data[frame2].phase
        context.frame_data[frame1].phase = phase2
        context.frame_data[frame2].phase = phase1

    def capture_v0(self, node: ast.FunctionCall, context: _ParseState) -> None:
        """A 'capture_v0' Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.
        """

    def play(self, node: ast.FunctionCall, context: _ParseState) -> None:
        """A 'play' Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.

        Raises:
            NotImplementedError: Raises if not of type
                [ast.Identifier, ast.FunctionCall, ast.ArrayLiteral]
        """
        frame_id = self.visit(node.arguments[0], context)
        if isinstance(node.arguments[1], ast.ArrayLiteral):
            amps = self.visit(node.arguments[1], context)
        elif isinstance(node.arguments[1], (ast.Identifier, ast.FunctionCall)):
            amps = self.visit(node.arguments[1], context)
            if isinstance(amps, Waveform):
                amps = amps.sample(context.frame_data[frame_id].dt)
            elif isinstance(amps, str):
                raise NameError(f"waveform '{amps}' is not defined.")  # noqa: TRY004
        else:
            raise NotImplementedError
        frame_data = context.frame_data[frame_id]
        for value in amps:
            self.amplitudes[frame_id].put(
                frame_data.current_time, complex(frame_data.scale * value)
            )
            self.frequencies[frame_id].put(frame_data.current_time, frame_data.frequency)
            self.phases[frame_id].put(frame_data.current_time, frame_data.phase)
            frame_data.current_time += frame_data.dt

    def constant(self, node: ast.FunctionCall, context: _ParseState) -> Waveform:
        """A 'constant' Waveform Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.

        Returns:
            Waveform: The waveform object representing the function call.
        """
        args = [self.visit(arg, context) for arg in node.arguments]
        return ConstantWaveform(*args)

    def gaussian(self, node: ast.FunctionCall, context: _ParseState) -> Waveform:
        """A 'gaussian' Waveform Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.

        Returns:
            Waveform: The waveform object representing the function call.
        """
        args = [self.visit(arg, context) for arg in node.arguments]
        return GaussianWaveform(*args)

    def drag_gaussian(self, node: ast.FunctionCall, context: _ParseState) -> Waveform:
        """A 'drag_gaussian' Waveform Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.

        Returns:
            Waveform: The waveform object representing the function call.
        """
        args = [self.visit(arg, context) for arg in node.arguments]
        return DragGaussianWaveform(*args)

    def erf_square(self, node: ast.FunctionCall, context: _ParseState) -> Waveform:
        """A 'erf_square' Waveform Function call.

        Args:
            node (ast.FunctionCall): The function call node.
            context (_ParseState): The parse state.

        Returns:
            Waveform: The waveform object representing the function call.
        """
        args = [self.visit(arg, context) for arg in node.arguments]
        return ErfSquareWaveform(*args)


def _init_frame_data(frames: dict[str, Frame]) -> dict[str, _FrameState]:
    return {
        frameId: _FrameState(frame.port.dt, frame.frequency, frame.phase % (2 * np.pi))
        for frameId, frame in frames.items()
    }


def _init_qubit_frame_mapping(frames: dict[str, Frame]) -> dict[str, list[str]]:
    mapping = {}
    for frameId in frames:
        if m := (
            re.search(r"q(\d+)_q(\d+)_[a-z_]+", frameId) or re.search(r"[rq](\d+)_[a-z_]+", frameId)
        ):
            for qubit in m.groups():
                if qubit in mapping:
                    mapping[qubit].append(frameId)
                else:
                    mapping[qubit] = [frameId]
    return mapping


def _lcm_floats(*dts: list[float]) -> float:
    """Return the least common multiple of time increments of a list of frames
        A time increment is the inverse of the corresponding sample rate which is considered
        an integer.
        LCM of rational numbers is lcm = (LCM of numerators) / (GCD of denominators)
        Hence the LCM of dts is 1/gcd([sample rates])

    Args:
        *dts (list[float]): list of time resolutions

    Returns:
        float: The LCM of time increments for a list of frames.
    """
    sample_rates = [round(1 / dt) for dt in dts]
    res_gcd = sample_rates[0]
    for sr in sample_rates[1:]:
        res_gcd = np.gcd(res_gcd, sr)
    return 1 / res_gcd


def _ceil_approx(number: float) -> int:
    return int(number) + 1 if abs(number - int(number)) > 0.001 else int(number)
