from enum import Enum


class IRType(str, Enum):
    OPENQASM = "OPENQASM"
    JAQCD = "JAQCD"


class QubitReferenceType(str, Enum):
    VIRTUAL = "VIRTUAL"
    PHYSICAL = "PHYSICAL"
