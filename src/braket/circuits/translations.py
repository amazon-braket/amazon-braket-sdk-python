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

import operator
from functools import reduce

from braket.default_simulator.openqasm.interpreter import VerbatimBoxDelimiter
from braket.ir.jaqcd import (
    Amplitude,
    DensityMatrix,
    Expectation,
    Probability,
    Sample,
    StateVector,
    Variance,
)
from braket.ir.jaqcd.program_v1 import Results

import braket.circuits.gates as braket_gates
from braket.circuits import Observable, ResultType, noises, observables, result_types
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.experimental_capabilities.iqm.classical_control import CCPRx, MeasureFF

BRAKET_GATES = {
    "gphase": braket_gates.GPhase,
    "i": braket_gates.I,
    "h": braket_gates.H,
    "x": braket_gates.X,
    "y": braket_gates.Y,
    "z": braket_gates.Z,
    "cv": braket_gates.CV,
    "cnot": braket_gates.CNot,
    "cy": braket_gates.CY,
    "cz": braket_gates.CZ,
    "ecr": braket_gates.ECR,
    "s": braket_gates.S,
    "si": braket_gates.Si,
    "t": braket_gates.T,
    "ti": braket_gates.Ti,
    "v": braket_gates.V,
    "vi": braket_gates.Vi,
    "phaseshift": braket_gates.PhaseShift,
    "cphaseshift": braket_gates.CPhaseShift,
    "cphaseshift00": braket_gates.CPhaseShift00,
    "cphaseshift01": braket_gates.CPhaseShift01,
    "cphaseshift10": braket_gates.CPhaseShift10,
    "rx": braket_gates.Rx,
    "ry": braket_gates.Ry,
    "rz": braket_gates.Rz,
    "U": braket_gates.U,
    "swap": braket_gates.Swap,
    "iswap": braket_gates.ISwap,
    "pswap": braket_gates.PSwap,
    "xy": braket_gates.XY,
    "xx": braket_gates.XX,
    "yy": braket_gates.YY,
    "zz": braket_gates.ZZ,
    "ccnot": braket_gates.CCNot,
    "cswap": braket_gates.CSwap,
    "gpi": braket_gates.GPi,
    "gpi2": braket_gates.GPi2,
    "prx": braket_gates.PRx,
    "ms": braket_gates.MS,
    "unitary": braket_gates.Unitary,
    "cc_prx": CCPRx,
    "measure_ff": MeasureFF,
}

COMPILER_DIRECTIVES = {
    VerbatimBoxDelimiter.START_VERBATIM: StartVerbatimBox,
    VerbatimBoxDelimiter.END_VERBATIM: EndVerbatimBox,
}

one_prob_noise_map = {
    "bit_flip": noises.BitFlip,
    "phase_flip": noises.PhaseFlip,
    "pauli_channel": noises.PauliChannel,
    "depolarizing": noises.Depolarizing,
    "two_qubit_depolarizing": noises.TwoQubitDepolarizing,
    "two_qubit_dephasing": noises.TwoQubitDephasing,
    "amplitude_damping": noises.AmplitudeDamping,
    "generalized_amplitude_damping": noises.GeneralizedAmplitudeDamping,
    "phase_damping": noises.PhaseDamping,
}

SUPPORTED_NOISE_PRAGMA_TO_NOISE = {
    "braket_noise_bit_flip": noises.BitFlip,
    "braket_noise_phase_flip": noises.PhaseFlip,
    "braket_noise_pauli_channel": noises.PauliChannel,
    "braket_noise_depolarizing": noises.Depolarizing,
    "braket_noise_two_qubit_depolarizing": noises.TwoQubitDepolarizing,
    "braket_noise_two_qubit_dephasing": noises.TwoQubitDephasing,
    "braket_noise_amplitude_damping": noises.AmplitudeDamping,
    "braket_noise_generalized_amplitude_damping": noises.GeneralizedAmplitudeDamping,
    "braket_noise_phase_damping": noises.PhaseDamping,
    "braket_noise_kraus": noises.Kraus,
}


def _get_observable(obs: str) -> Observable:
    if isinstance(obs, str):
        return getattr(observables, obs.upper())()
    raise NotImplementedError


def get_tensor_product(observable: list[str]) -> Observable:
    """Generate an braket circuit observable

    Args:
        observable (list[str]): ir observable or a matrix

    Returns:
        Observable: braket circuit observable
    """
    circuit_observable = [_get_observable(obs) for obs in observable]
    return reduce(operator.matmul, circuit_observable)


def braket_result_to_result_type(result: Results) -> ResultType:
    return _braket_result_to_result_type(result)


def _braket_result_to_result_type(result: Results) -> ResultType:
    match result:
        case Expectation(observable=observable, targets=targets):
            tensor_product = get_tensor_product(observable)
            return result_types.Expectation(observable=tensor_product, target=targets)
        case Variance(observable=observable, targets=targets):
            tensor_product = get_tensor_product(observable)
            return result_types.Variance(observable=tensor_product, target=targets)
        case Sample(observable=observable, targets=targets):
            tensor_product = get_tensor_product(observable)
            return result_types.Sample(observable=tensor_product, target=targets)
        case Probability(targets=targets):
            return result_types.Probability(targets)
        case Amplitude(states=states):
            return result_types.Amplitude(state=states)
        case StateVector():
            return result_types.StateVector()
        case DensityMatrix(targets=targets):
            return result_types.DensityMatrix(target=targets)
        case _:
            raise TypeError(f"Result type {type(result).__name__} is not supported")
