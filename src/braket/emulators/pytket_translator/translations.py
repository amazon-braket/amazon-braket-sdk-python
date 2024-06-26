from pytket.circuit import OpType

from braket.emulators.pytket_translator.composed_gates import ComposedGates

"""The measurement register identifier."""
MEASUREMENT_REGISTER_NAME = "c"

"""
    OpenQASM-3.0 to Pytket Name Translations
"""
QASM_TO_PYTKET = {
    "gphase": OpType.Phase,
    "i": OpType.noop,
    "h": OpType.H,
    "x": OpType.X,
    "y": OpType.Y,
    "z": OpType.Z,
    "cv": OpType.CV,
    "cnot": OpType.CX,
    "cy": OpType.CY,
    "cz": OpType.CZ,
    "ecr": OpType.ECR,
    "s": OpType.S,
    "si": OpType.Sdg,
    "t": OpType.T,
    "ti": OpType.Tdg,
    "v": OpType.V,
    "vi": OpType.Vdg,
    "phaseshift": OpType.U1,
    "rx": OpType.Rx,
    "ry": OpType.Ry,
    "rz": OpType.Rz,
    "U": OpType.U3,
    "swap": OpType.SWAP,
    "iswap": OpType.ISWAPMax,
    "xy": OpType.ISWAP,
    "xx": OpType.XXPhase,
    "yy": OpType.YYPhase,
    "zz": OpType.ZZPhase,
    "ccnot": OpType.CCX,
    "cswap": OpType.CSWAP,
    "unitary": OpType.U3,
    "gpi": OpType.GPI,
    "gpi2": OpType.GPI2,
    "ms": OpType.AAMS,
    "cphaseshift": OpType.CU1,
    "prx": OpType.PhasedX,
}


COMPOSED_GATES = {
    "cphaseshift00": ComposedGates.add_cphaseshift00,
    "cphaseshift01": ComposedGates.add_cphaseshift01,
    "cphaseshift10": ComposedGates.add_cphaseshift10,
    "pswap": ComposedGates.add_pswap,
}

"""
    Pytket to OpenQASM-3.0 Name Translations
"""
PYTKET_TO_QASM = {optype: qasm_name for qasm_name, optype in QASM_TO_PYTKET.items()}
