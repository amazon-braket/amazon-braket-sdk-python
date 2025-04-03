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
from functools import reduce, singledispatch
from typing import NoReturn

import braket.circuits.gates as braket_gates
import braket.circuits.result_types as ResultTypes  # noqa: N812
import braket.ir.jaqcd.shared_models as models
from braket.circuits import Observable, noises, observables
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


def get_observable(obs: models.Observable | list) -> Observable:
    """Gets the observable.

    Args:
        obs (models.Observable | list): The observable(s) to get translated.

    Returns:
        Observable: The translated observable.
    """
    return _get_observable(obs)


@singledispatch
def _get_observable(obs: models.Observable | list) -> Observable:
    raise NotImplementedError


@_get_observable.register(list)
def _(obs: Observable) -> NoReturn:
    raise NotImplementedError


@_get_observable.register(str)
def _(name: str):
    return getattr(observables, name.upper())()


def get_tensor_product(observable: models.Observable | list) -> Observable:
    """Generate an braket circuit observable

    Args:
        observable (Observable | list): ir observable or a matrix

    Returns:
        Observable: braket circuit observable
    """
    circuit_observable = [get_observable(obs) for obs in observable]
    return reduce(operator.matmul, circuit_observable)


@singledispatch
def _braket_result_to_result_type(result: Results) -> None:
    raise TypeError(f"Result type {type(result).__name__} is not supported")


def braket_result_to_result_type(result: Results) -> None:
    return _braket_result_to_result_type(result)


@_braket_result_to_result_type.register(Amplitude)
def _(result: Results) -> Amplitude:
    return ResultTypes.Amplitude(state=result.states)


@_braket_result_to_result_type.register(Expectation)
def _(result: Results) -> Expectation:
    tensor_product = get_tensor_product(result.observable)

    return ResultTypes.Expectation(observable=tensor_product, target=result.targets)


@_braket_result_to_result_type.register(Probability)
def _(result: Results) -> Probability:
    return ResultTypes.Probability(result.targets)


@_braket_result_to_result_type.register(Sample)
def _(result: Results) -> Sample:
    tensor_product = get_tensor_product(result.observable)
    return ResultTypes.Sample(observable=tensor_product, target=result.targets)


@_braket_result_to_result_type.register(StateVector)
def _(result: Results) -> StateVector:
    return ResultTypes.StateVector()


@_braket_result_to_result_type.register(DensityMatrix)
def _(result: Results):
    return ResultTypes.DensityMatrix(target=result.targets)


@_braket_result_to_result_type.register(Variance)
def _(result: Results):
    tensor_product = get_tensor_product(result.observable)
    return ResultTypes.Variance(observable=tensor_product, target=result.targets)
