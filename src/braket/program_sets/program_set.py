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

from collections.abc import Mapping, Sequence

from braket.ir.openqasm import ProgramSet as OpenQASMProgramSet

from braket.circuits import Circuit, Gate, Observable
from braket.circuits.observables import Sum
from braket.circuits.serialization import IRType
from braket.program_sets.circuit_binding import CircuitBinding
from braket.pulse import PulseSequence
from braket.registers import QubitSet


class ProgramSet:
    def __init__(
        self,
        programs: list[CircuitBinding | Circuit] | CircuitBinding,
        shots_per_executable: int | None = None,
    ):
        """
        A set of programs to be run together on a device.

        Args:
            programs (list[CircuitBinding | Circuit] | CircuitBinding): A list of circuit bindings
                or circuits to execute. It is also possible to provide a single circuit binding.
                Note: circuits cannot have result types.
            shots_per_executable (int | None): The number of shots to run each executable;
                this will be used to enforce the total shots on task creation. If not provided,
                the only validation at task creation will be divisibility by number of executables.
        """
        self._programs = [programs] if isinstance(programs, CircuitBinding) else programs
        if any(isinstance(circuit, Circuit) and circuit.result_types for circuit in self._programs):
            raise ValueError("Circuit cannot have result types")
        self._shots_per_executable = shots_per_executable

    def to_ir(
        self,
        *,
        gate_definitions: Mapping[tuple[Gate, QubitSet], PulseSequence] | None = None,
    ) -> OpenQASMProgramSet:
        """Serializes the program set into a form that can run on a Braket device.

        Args:
            gate_definitions (dict[tuple[Gate, QubitSet], PulseSequence] | None): The
                calibration data for the device. default: None.

        Returns:
            braket.ir.openqasm.ProgramSet: The serialized program set.
        """
        return OpenQASMProgramSet(
            programs=[
                (
                    circuit_binding.to_ir(IRType.OPENQASM, gate_definitions=gate_definitions)
                    if isinstance(circuit_binding, Circuit)
                    else circuit_binding.to_ir(gate_definitions=gate_definitions)
                )
                for circuit_binding in self._programs
            ]
        )

    @property
    def entries(self) -> list[CircuitBinding | Circuit]:
        """list[CircuitBinding | Circuit]: The circuit bindings or circuits in this program set"""
        return self._programs

    @property
    def total_executables(self) -> int:
        """int: The total number of executables in this program set"""
        return sum(len(prog) if isinstance(prog, CircuitBinding) else 1 for prog in self._programs)

    @property
    def shots_per_executable(self) -> int | None:
        """int: The number of shots to run each executable in this program set"""
        return self._shots_per_executable

    @property
    def total_shots(self) -> int:
        """
        int: The total number of shots across all executables in this program set,
        if shots_per_executable was provided.
        """
        if not self._shots_per_executable:
            raise ValueError("No per-executable shots defined")
        return self._shots_per_executable * self.total_executables

    @staticmethod
    def zip(
        circuits: Sequence[Circuit] | CircuitBinding,
        *,
        input_sets: Sequence[Mapping[str, float]] | None = None,
        observables: Sequence[Observable | None] | None = None,
        shots_per_executable: int | None = None,
    ) -> ProgramSet:
        """
        Constructs a batch of circuits from a list of circuits and optionally an input set and/or
        observable for each; alternatively, a single CircuitBinding can be provided and paired
        with corresponding observables.

        Args:
            circuits (Sequence[Circuit] | CircuitBinding): The parametrized circuit with parameters
                or set of fixed circuits to run with multiple observables.
            input_sets (Sequence[Mapping[str, float]] | None): The inputs to the circuit;
                must match number of circuits if provided.
                Must be empty if circuits is a CircuitBinding.
            observables (Sequence[Observable | None]| None): A set of observables to measure
                with the circuits; must match number of circuits if provided.
            shots_per_executable (int | None): The number of shots to run each executable;
                this will be used to enforce the total shots on task creation. If not provided,
                the only validation at task creation will be divisibility by number of executables.

        Returns:
            ProgramSet: a program set consisting of matching sets of
            circuits, inputs and observables.
        """
        if isinstance(circuits, CircuitBinding):
            return _zip_circuit_bindings(circuits, input_sets, observables, shots_per_executable)
        return _zip_circuits(circuits, input_sets, observables, shots_per_executable)

    @staticmethod
    def product(
        circuits: Sequence[Circuit | CircuitBinding],
        observables: Sum | Sequence[Observable],
        shots_per_executable: int | None = None,
    ) -> ProgramSet:
        """
        Constructs a program set from the Cartesian product of the given observables with the given
        circuits or bindings.

        If an entry of the list is a single circuit, then the resulting program will consist of that
        circuit and all the observables; if an entry is a circuit binding, then the result program
        will be the Cartesian product of the binding's input values and observables.

        Args:
            circuits (Sequence[Circuit] | CircuitBinding): The parametrized circuit with parameters
                or set of fixed circuits to run with multiple observables.
            observables (Sum | Sequence[Observable]): A set of observables to measure
                with the circuits.
            shots_per_executable (int | None): The number of shots to run each executable;
                this will be used to enforce the total shots on task creation. If not provided,
                the only validation at task creation will be divisibility by number of executables.

        Returns:
            ProgramSet: a program set consisting of Cartesian products of the given observables
            with the given circuits or bindings.
        """
        if not observables:
            raise ValueError("Observables must be specified")
        programs = []
        for circuit in circuits:
            if isinstance(circuit, CircuitBinding):
                if circuit.observables:
                    raise ValueError(
                        "Cannot specify observables in both circuit bindings and product"
                    )
                programs.append(CircuitBinding(circuit.circuit, circuit.input_sets, observables))
            else:
                programs.append(CircuitBinding(circuit, input_sets=None, observables=observables))
        return ProgramSet(programs, shots_per_executable)

    def __len__(self):
        return len(self._programs)

    def __getitem__(self, item: int):
        return self._programs[item]

    def __add__(self, other: ProgramSet | list):
        if isinstance(other, ProgramSet):
            if (
                self._shots_per_executable == other._shots_per_executable
                or other._shots_per_executable is None
            ):
                return ProgramSet(self._programs + other._programs, self._shots_per_executable)
            if self._shots_per_executable is None:
                return ProgramSet(self._programs + other._programs, other._shots_per_executable)
            raise ValueError("Mismatched shots per executable")
        if isinstance(other, list):
            return ProgramSet(self._programs + other, self._shots_per_executable)
        raise TypeError(f"Cannot add type {type(other)} to ProgramSet")

    def __eq__(self, other: ProgramSet):
        if not isinstance(other, ProgramSet):
            return False
        return (
            self._programs == other._programs
            and self._shots_per_executable == other._shots_per_executable
        )

    def __repr__(self):
        return (
            f"ProgramSet(programs={self._programs}, "
            f"shots_per_executable={self._shots_per_executable})"
        )


def _zip_circuit_bindings(
    circuit_binding: CircuitBinding,
    input_sets: Sequence[Mapping[str, float]] | None,
    observables: Sequence[Observable | None] | None,
    shots_per_executable: int | None,
) -> ProgramSet:
    circuit = circuit_binding.circuit
    if circuit_binding.observables:
        if isinstance(circuit_binding.observables, Sum):
            raise TypeError("Cannot zip with Sum observable")
        if observables:
            raise ValueError("Cannot specify observables in both circuit bindings and zip")
        if not input_sets:
            raise ValueError("Must specify input sets")
        if len(circuit_binding.observables) != len(input_sets):
            raise ValueError("Number of observables must match number of input sets")
        return ProgramSet(
            [
                CircuitBinding(circuit, [input_set], [observable])
                for input_set, observable in zip(
                    input_sets, circuit_binding.observables, strict=True
                )
            ],
            shots_per_executable,
        )
    if input_sets:
        raise ValueError("Cannot specify input sets in both circuit bindings and zip")
    if not observables:
        raise ValueError("Must specify observables")
    if any(isinstance(obs, Sum) for obs in observables):
        raise TypeError("Cannot have Sum Hamiltonian in list of observables")
    if len(circuit_binding.input_sets) != len(observables):
        raise ValueError("Number of observables must match number of input sets")
    inputs_list = circuit_binding.input_sets.as_list()
    return ProgramSet(
        [
            CircuitBinding(circuit, [input_set], [observable])
            for input_set, observable in zip(inputs_list, observables, strict=True)
        ],
        shots_per_executable,
    )


def _zip_circuits(
    circuits: Sequence[Circuit],
    input_sets: Sequence[Mapping[str, float]] | None,
    observables: Sequence[Observable | None] | None,
    shots_per_executable: int | None,
) -> ProgramSet:
    if input_sets and observables:
        if len(circuits) != len(observables):
            raise ValueError("Number of circuits must match number of observables")
        if len(circuits) != len(input_sets):
            raise ValueError("Number of circuits must match number of input sets")
        return ProgramSet(
            [
                CircuitBinding(circuit, [input_set], [observable])
                for circuit, input_set, observable in zip(
                    circuits, input_sets, observables, strict=True
                )
            ],
            shots_per_executable,
        )
    if input_sets:
        if len(circuits) != len(input_sets):
            raise ValueError("Number of circuits must match number of input sets")
        return ProgramSet(
            [
                CircuitBinding(circuit, [input_set], None)
                for circuit, input_set in zip(circuits, input_sets, strict=True)
            ],
            shots_per_executable,
        )
    if observables:
        if len(circuits) != len(observables):
            raise ValueError("Number of circuits must match number of observables")
        return ProgramSet(
            [
                CircuitBinding(circuit, None, [observable])
                for circuit, observable in zip(circuits, observables, strict=True)
            ],
            shots_per_executable,
        )
    raise ValueError("Must specify either input sets or observables")
