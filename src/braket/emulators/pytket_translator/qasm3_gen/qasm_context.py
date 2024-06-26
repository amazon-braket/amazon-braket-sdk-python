from collections import namedtuple
from typing import Dict, List, Union

from sympy import Expr, Symbol, pi

from braket.emulators.pytket_translator.translations import MEASUREMENT_REGISTER_NAME

"""A single measurement: from qubit index to the bit expression."""
Measurement = namedtuple("Measurement", ("qubit", "bit"))

"""A gate operation, with a given name, classical args, and qubits"""
Gate = namedtuple("Gate", ("name", "args", "qubits"))


class QasmContext:

    def __init__(self, input_parameters: Dict[str, str] = dict()):
        self.input_parameters = input_parameters
        self.num_bits: int = 0
        self.gates: List[Gate] = []
        self.measurements: List[Measurement] = []

    def set_num_bits(self, num_bits: int) -> None:
        self.num_bits = num_bits

    def add_gate(self, name: str, args: List[Union[Expr, Symbol]], qubits: List[int]):
        self.gates.append(Gate(name, args, qubits))

    def add_measurement(self, qubit: int, cbit: int):
        self.measurements.append(Measurement(qubit, f"{MEASUREMENT_REGISTER_NAME}[{cbit}]"))

    def add_parameter(self, param_name: str, param_type: str):
        self.input_parameters[param_name] = param_type
