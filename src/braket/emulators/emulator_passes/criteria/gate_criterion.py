from collections.abc import Iterator

from braket.circuits import Circuit
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.circuits.gate import Gate
from braket.circuits.translations import BRAKET_GATES
from braket.emulators.emulator_passes.criteria.emulator_criterion import EmulatorCriterion


class GateCriterion(EmulatorCriterion):
    def __init__(self, supported_gates: Iterator[str] = [], native_gates: Iterator[str] = []):
        """
        args:
            native_gates (Iterator[str]): A list of gates supported inside of verbatim mode by
            the emulator.
            supported_gates (Iterator[str]): A list of gates supported outside of verbatim mode
            by the emulator. A gate is a Braket gate name.
        """
        if len(supported_gates) == 0 and len(native_gates) == 0:
            raise ValueError("Supported gate set or native gate set must be provided.")

        try:
            self._supported_gates = set(BRAKET_GATES[gate.lower()] for gate in supported_gates)
            self._native_gates = set(BRAKET_GATES[gate.lower()] for gate in native_gates)
        except KeyError as e:
            raise ValueError(f"Input {str(e)} is not a valid Braket gate name.")

    def validate(self, circuit: Circuit) -> None:
        idx = 0
        while idx < len(circuit.instructions):
            instruction = circuit.instructions[idx]
            if isinstance(instruction.operator, StartVerbatimBox):
                idx += 1
                while idx < len(circuit.instructions) and not isinstance(
                    circuit.instructions[idx].operator, EndVerbatimBox
                ):
                    instruction = circuit.instructions[idx]
                    if isinstance(instruction.operator, Gate):
                        gate = instruction.operator
                        if not type(gate) in self._native_gates:
                            raise ValueError(
                                f"Gate {gate.name} is not a native gate supported by this device."
                            )
                    idx += 1
                if not isinstance(circuit.instructions[idx].operator, EndVerbatimBox):
                    raise ValueError(f"No end verbatim box found at index {idx} in the circuit.")
            elif isinstance(instruction.operator, Gate):
                gate = instruction.operator
                if not type(gate) in self._supported_gates:
                    raise ValueError(f"Gate {gate.name} is not supported by this device.")
            idx += 1

    def __eq__(self, other: EmulatorCriterion) -> bool:
        return (
            isinstance(other, GateCriterion)
            and self._supported_gates == other._supported_gates
            and self._native_gates == other._native_gates
        )
