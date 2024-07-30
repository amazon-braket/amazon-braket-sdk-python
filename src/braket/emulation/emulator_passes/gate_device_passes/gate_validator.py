from collections.abc import Iterator
from typing import Optional

from braket.circuits import Circuit
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.circuits.gate import Gate
from braket.circuits.translations import BRAKET_GATES
from braket.emulation.emulator_passes.validation_pass import ValidationPass


class GateValidator(ValidationPass[Circuit]):
    def __init__(
        self,
        supported_gates: Optional[Iterator[str]] = None,
        native_gates: Optional[Iterator[str]] = None,
    ):
        """
        Args:
            supported_gates (Optional[Iterator[str]]): A list of gates supported outside of
                verbatim modeby the emulator. A gate is a Braket gate name.
            native_gates (Optional[Iterator[str]]): A list of gates supported inside of
                verbatim mode by the emulator.

        Raises:
            ValueError: If supported_gates and and native_gates are empty or any of the provided
            gate are not supported by the Braket BDK.
        """
        supported_gates, native_gates = (supported_gates or []), (native_gates or [])
        if not len(supported_gates) and not len(native_gates):
            raise ValueError("Supported gate set or native gate set must be provided.")

        try:
            self._supported_gates = set(BRAKET_GATES[gate.lower()] for gate in supported_gates)
        except KeyError as e:
            raise ValueError(f"Input {str(e)} in supported_gates is not a valid Braket gate name.")

        try:
            self._native_gates = set(BRAKET_GATES[gate.lower()] for gate in native_gates)
        except KeyError as e:
            raise ValueError(f"Input {str(e)} in native_gates is not a valid Braket gate name.")

    def validate(self, program: Circuit) -> None:
        """
        Checks that all non-verbatim gates used in the circuit are in this validator's
        supported gate set and that all verbatim gates used in the circuit are in this
        validator's native gate set.

        Args:
            program (Circuit): The Braket circuit whose gates to validate.

        Raises:
            ValueError: If a gate operation or verbatim gate operation is not in this validator's
            supported or native gate set, respectively.
        """
        idx = 0
        while idx < len(program.instructions):
            instruction = program.instructions[idx]
            if isinstance(instruction.operator, StartVerbatimBox):
                idx += 1
                while idx < len(program.instructions) and not isinstance(
                    program.instructions[idx].operator, EndVerbatimBox
                ):
                    instruction = program.instructions[idx]
                    if isinstance(instruction.operator, Gate):
                        gate = instruction.operator
                        if not type(gate) in self._native_gates:
                            raise ValueError(
                                f"Gate {gate.name} is not a native gate supported by this device."
                            )
                    idx += 1
                if idx == len(program.instructions) or not isinstance(
                    program.instructions[idx].operator, EndVerbatimBox
                ):
                    raise ValueError(f"No end verbatim box found at index {idx} in the circuit.")
            elif isinstance(instruction.operator, Gate):
                gate = instruction.operator
                if not type(gate) in self._supported_gates:
                    raise ValueError(f"Gate {gate.name} is not supported by this device.")
            idx += 1

    def __eq__(self, other: ValidationPass) -> bool:
        return (
            isinstance(other, GateValidator)
            and self._supported_gates == other._supported_gates
            and self._native_gates == other._native_gates
        )
