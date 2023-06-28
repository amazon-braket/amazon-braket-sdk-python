from functools import singledispatch, reduce
from typing import Tuple
import importlib
from braket.circuits import Instruction, observables
import braket.circuits.noises as noises
from braket.circuits.gates import (
    I,
    H,
    X,
    Y,
    Z,
    CV,
    CNot,
    CY,
    CZ,
    ECR,
    S,
    Si,
    T,
    Ti,
    V,
    Vi,
    PhaseShift,
    CPhaseShift,
    CPhaseShift00,
    CPhaseShift01,
    CPhaseShift10,
    Rx,
    Ry,
    Rz,
    Swap,
    ISwap,
    PSwap,
    XY,
    XX,
    YY,
    ZZ,
    CCNot,
    CSwap,
    GPi,
    GPi2,
    MS,
    Unitary,
)
import braket.circuits.result_types as ResultTypes

from braket.default_simulator.noise_operations import (
    BitFlip,
    PhaseFlip,
    GeneralizedAmplitudeDamping,
    PhaseDamping,
    AmplitudeDamping,
    Depolarizing,
    PauliChannel,
    TwoQubitDepolarizing,
    TwoQubitDephasing,
)
from braket.ir.jaqcd import (
    Amplitude,
    Expectation,
    Probability,
    Sample,
    StateVector,
    DensityMatrix,
    Variance,
    AdjointGradient,
)


BRAKET_GATES = {
    "i": I,
    "h": H,
    "x": X,
    "y": Y,
    "z": Z,
    "cv": CV,
    "cnot": CNot,
    "cy": CY,
    "cz": CZ,
    "ecr": ECR,
    "s": S,
    "si": Si,
    "t": T,
    "ti": Ti,
    "v": V,
    "vi": Vi,
    "phaseshift": PhaseShift,
    "cphaseshift": CPhaseShift,
    "cphaseshift00": CPhaseShift00,
    "cphaseshift01": CPhaseShift01,
    "cphaseshift10": CPhaseShift10,
    "rx": Rx,
    "ry": Ry,
    "rz": Rz,
    "swap": Swap,
    "iswap": ISwap,
    "pswap": PSwap,
    "xy": XY,
    "xx": XX,
    "yy": YY,
    "zz": ZZ,
    "ccnot": CCNot,
    "cswap": CSwap,
    "gpi": GPi,
    "gpi2": GPi2,
    "ms": MS,
    "unitary": Unitary,
}


@singledispatch
def braket_noise_gate_to_instruction(noise):
    raise TypeError(f"Operation {type(noise).__name__} not supported")


@braket_noise_gate_to_instruction.register(BitFlip)
def _(noise):
    return Instruction(noises.BitFlip(noise.probability), target=noise.targets)


@braket_noise_gate_to_instruction.register(PhaseFlip)
def _(noise):
    return Instruction(noises.PhaseFlip(noise.probability), target=noise.targets)


@braket_noise_gate_to_instruction.register(PauliChannel)
def _(noise):
    return Instruction(noises.PauliChannel(*noise.probabilities), target=noise.targets)


@braket_noise_gate_to_instruction.register(Depolarizing)
def _(noise):
    return Instruction(noises.Depolarizing(noise.probability), target=noise.targets)


@braket_noise_gate_to_instruction.register(TwoQubitDepolarizing)
def _(noise):
    return Instruction(noises.TwoQubitDepolarizing(noise.probability), target=noise.targets)


@braket_noise_gate_to_instruction.register(TwoQubitDephasing)
def _(noise):
    return Instruction(noises.TwoQubitDephasing(noise.probability), target=noise.targets)


@braket_noise_gate_to_instruction.register(AmplitudeDamping)
def _(noise):
    return Instruction(noises.AmplitudeDamping(noise.gamma), target=noise.targets)


@braket_noise_gate_to_instruction.register(GeneralizedAmplitudeDamping)
def _(noise):
    return Instruction(
        noises.GeneralizedAmplitudeDamping(noise.gamma, noise.probability), target=noise.targets
    )


@braket_noise_gate_to_instruction.register(PhaseDamping)
def _(noise):
    return Instruction(noises.PhaseDamping(noise.gamma), target=noise.targets)


def get_observable(name: str):
    return getattr(observables, name.upper())()


def get_tensor_prodct(observable):
    circuit_observable = [get_observable(obs) for obs in observable]
    return reduce(lambda obs1, obs2: obs1 @ obs2, circuit_observable)


@singledispatch
def braket_result_to_result_type(result):
    raise TypeError(f"Result type {type(result).__name__} is not supported")


@braket_result_to_result_type.register(Amplitude)
def _(result):
    return ResultTypes.Amplitude(state=result.states)


@braket_result_to_result_type.register(Expectation)
def _(result):
    tensor_product = get_tensor_product(result.observable)

    return ResultTypes.Expectation(observable=tensor_product, target=result.targets)


@braket_result_to_result_type.register(Probability)
def _(result):
    return ResultTypes.Probability(result.targets)


@braket_result_to_result_type.register(Sample)
def _(result):
    tensor_product = get_tensor_product(result.observable)
    return ResultTypes.Sample(observable=tensor_product, target=result.targets)


@braket_result_to_result_type.register(StateVector)
def _(result):
    return ResultTypes.StateVector()


@braket_result_to_result_type.register(DensityMatrix)
def _(result):
    return ResultTypes.DensityMatrix(target=result.targets)


@braket_result_to_result_type.register(Variance)
def _(result):
    tensor_product = get_tensor_product(result.observable)
    return ResultTypes.Variance(observable=tensor_product, target=result.targets)


@braket_result_to_result_type.register(AdjointGradient)
def _(result):
    tensor_product = get_tensor_product(result.observable)
    return ResultTypes.AdjointGradient(observable=tensor_product, target=result.targets)
