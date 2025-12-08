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

from collections.abc import Iterable

from braket.circuits import Circuit
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.circuits.gate import Gate
from braket.circuits.translations import BRAKET_GATES
from braket.emulation.passes import ValidationPass


class GateValidator(ValidationPass):
    def __init__(
        self,
        supported_gates: Iterable[str] | None = None,
        native_gates: Iterable[str] | None = None,
    ):
        """
        A GateValidator instance validates that a circuit uses the supported gates of the device, or
            native gates within a verbatim box if any.

        Args:
            supported_gates (Iterable[str] | None): A list of gates supported outside of
                verbatim modeby the emulator. A gate is a Braket gate name.
            native_gates (Iterable[str] | None): A list of gates supported inside of
                verbatim mode by the emulator.

        Raises:
            ValueError: If supported_gates and native_gates are empty or any of the provided
            gate are not supported by the Braket BDK.
        """
        supported_gates, native_gates = (supported_gates or []), (native_gates or [])
        if not supported_gates and not native_gates:
            raise ValueError("Supported gate set or native gate set must be provided.")

        try:
            self._supported_gates = frozenset(
                BRAKET_GATES[gate.lower()] for gate in supported_gates
            )
        except KeyError as e:
            raise ValueError(
                f"Input {e!s} in supported_gates is not a valid Braket gate name."
            ) from e

        try:
            self._native_gates = frozenset(BRAKET_GATES[gate.lower()] for gate in native_gates)
        except KeyError as e:
            raise ValueError(f"Input {e!s} in native_gates is not a valid Braket gate name.") from e

    def validate(self, circuit: Circuit) -> None:
        """
        Checks that all non-verbatim gates used in the circuit are in this validator's
        supported gate set and that all verbatim gates used in the circuit are in this
        validator's native gate set.

        Args:
            circuit (Circuit): The Braket circuit whose gates to validate.

        Raises:
            ValueError: If a gate operation or verbatim gate operation is not in this validator's
            supported or native gate set, respectively.
        """
        in_verbatim = False
        for instruction in circuit.instructions:
            operator = instruction.operator
            if isinstance(operator, Gate):
                self._validate_gate(in_verbatim, operator)
            elif isinstance(operator, StartVerbatimBox):
                if in_verbatim:
                    raise ValueError("Already in verbatim box")
                in_verbatim = True
            elif isinstance(operator, EndVerbatimBox):
                if not in_verbatim:
                    raise ValueError("Already outside of verbatim box")
                in_verbatim = False

        # Check for unclosed verbatim box
        if in_verbatim:
            raise ValueError("No end verbatim box found for the circuit.")

    def _validate_gate(self, in_verbatim: bool, operator: Gate) -> None:
        if in_verbatim:
            if type(operator) not in self._native_gates:
                raise ValueError(f"Gate {operator.name} is not a native gate for this device.")
        elif type(operator) not in self._supported_gates:
            raise ValueError(f"Gate {operator.name} is not a supported gate for this device.")
