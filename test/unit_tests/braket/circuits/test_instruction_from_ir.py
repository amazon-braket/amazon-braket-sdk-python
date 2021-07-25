# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import numpy as np
import pytest

from braket.circuits import (
    AngledGate,
    Circuit,
    Gate,
    Instruction,
    Noise,
    Observable,
    ObservableResultType,
    ResultType,
)
from braket.circuits.gates import Unitary
from braket.circuits.noises import DampingNoise, GeneralizedAmplitudeDampingNoise, Kraus, PauliNoise
from braket.circuits.result_types import Amplitude
from braket.ir.jaqcd.program_v1 import Results, _valid_gates, _valid_noise_channels

ANGLE = 1.2

MATRIX = np.array([[1.0, 0.0], [0.0, 1.0]])

PROBABILITY = 0.1
GAMMA = 0.2

STATE = ["01", "10"]

CIRC = Circuit().h(0).cnot(0, 1)


@pytest.mark.parametrize("gate", _valid_gates.values())
def test_instr_ir_gate(gate):
    assert hasattr(Gate, gate.__name__)
    op_class = getattr(Gate, gate.__name__)
    if issubclass(op_class, AngledGate):
        op = op_class(ANGLE)
    elif issubclass(op_class, Unitary):
        op = op_class(MATRIX)
    else:
        op = op_class()
    instr_inp = Instruction(op, range(op.qubit_count))
    instr_out = Instruction.from_ir(instr_inp.to_ir())
    assert instr_inp == instr_out


@pytest.mark.parametrize("noise", _valid_noise_channels.values())
def test_instr_ir_noise(noise):
    assert hasattr(Noise, noise.__name__)
    op_class = getattr(Noise, noise.__name__)
    if issubclass(op_class, PauliNoise):
        op = op_class(PROBABILITY, PROBABILITY, PROBABILITY)
    elif issubclass(op_class, GeneralizedAmplitudeDampingNoise):
        op = op_class(GAMMA, PROBABILITY)
    elif issubclass(op_class, DampingNoise):
        op = op_class(GAMMA)
    elif issubclass(op_class, Kraus):
        op = op_class([MATRIX * np.sqrt(0.2), MATRIX * np.sqrt(0.8)])
    else:
        op = op_class(PROBABILITY)
    instr_inp = Instruction(op, range(op.qubit_count))
    instr_out = Instruction.from_ir(instr_inp.to_ir())
    assert instr_inp == instr_out


@pytest.mark.parametrize("result", Results.__args__)
def test_instr_ir_rt(result):
    assert hasattr(ResultType, result.__name__)
    rt_class = getattr(ResultType, result.__name__)
    if issubclass(rt_class, ObservableResultType):
        rt = rt_class(Observable.H())
    elif issubclass(rt_class, Amplitude):
        rt = rt_class(STATE)
    else:
        rt = rt_class()
    circ_inp = CIRC.copy()
    circ_inp.add_result_type(rt)
    circ_out = Circuit().from_ir(circ_inp.to_ir())
    assert circ_inp == circ_out


@pytest.mark.xfail(raises=ValueError)
def test_from_ir_instr():
    # Invalid instruction (e.g., None)
    prog = Circuit().h(0).cnot(0, 1).to_ir()
    getattr(prog, "instructions").append(None)
    Circuit().from_ir(prog)
