from braket.emulators.pytket_translator.composed_gates import ComposedGates

"""
    OpenQASM-3.0 to Pytket Name Translations
"""
PYTKET_GATES = {
    "gphase": "Phase",
    "i": "noop",
    "h": "H",
    "x": "X",
    "y": "Y",
    "z": "Z",
    "cv": "CV",
    "cnot": "CX",
    "cy": "CY",
    "cz": "CZ",
    "ecr": "ECR",
    "s": "S",
    "si": "Sdg",
    "t": "T",
    "ti": "Ti",
    "v": "V",
    "vi": "Vi",
    "phaseshift": "U1",
    "rx": "Rx",
    "ry": "Ry",
    "rz": "Rz",
    "U": "U3",
    "swap": "SWAP",
    "iswap": "ISWAPMax",
    "xy": "ISWAP",
    "xx": "XXPhase",
    "yy": "YYPhase",
    "zz": "ZZPhase",
    "ccnot": "CCX",
    "cswap": "CSWAP",
    "unitary": "U3",
    "gpi": "GPI", 
    "gpi2": "GPI2", 
    "ms": "AAMS"
}


COMPOSED_GATES = {
        "cphaseshift": ComposedGates.add_cphaseshift,
        "cphaseshift00": ComposedGates.add_cphaseshift00,
        "cphaseshift01": ComposedGates.add_cphaseshift01,
        "cphaseshift10": ComposedGates.add_cphaseshift10,
        "pswap": ComposedGates.add_pswap,
        "prx": ComposedGates.add_prx,
}