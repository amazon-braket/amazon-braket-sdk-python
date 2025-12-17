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

from braket.ir.openqasm import Program

from braket.circuits import Circuit, Gate, Observable
from braket.circuits.observable import euler_angle_parameter_names
from braket.circuits.observables import Sum
from braket.circuits.serialization import IRType
from braket.program_sets.parameter_sets import ParameterSets, ParameterSetsLike
from braket.pulse import PulseSequence
from braket.registers import QubitSet


class CircuitBinding:
    def __init__(
        self,
        circuit: Circuit,
        input_sets: ParameterSetsLike | None = None,
        observables: Sequence[Observable] | Sum | None = None,
    ):
        """
        A single parametrized circuit and multiple parameter sets and observables.

        In other words, running a circuit binding means running the circuit with each set of input
        parameters specified. Furthermore, observables are encoded as input parameters by way of
        Euler angle representation.

        If both input parameters and observables are provided, then each combination is executed,
        resulting in a total number of runs equal to the product of the two. For example, if there
        are 3 input sets and 4 parameters (or a Hamiltonian with 4 terms), the circuit will be run
        12 times.

        Note: Circuits cannot have result types attached.

        Args:
            circuit (Circuit): The parametrized circuit
            input_sets (ParameterSetsLike | None): The inputs to the circuit, if specified.
            observables (Sequence[Observable] | Sum | None): The observables or Hamiltonian
                to measure, if specified.

        Examples:
            >>> circuit = Circuit().rx(0, FreeParameter("theta")).cnot(0, 1)
            >>> observable = 2.1 * X(0) @ Z(1) - 4.5 * Z(0) @ Y(1)  # Sum Hamiltonian
            >>> # observable = [X(0) @ Z(1), Z(0) @ Y(1)]  # Or a list of single-term observables
            >>> binding = CircuitBinding(circuit, {"theta": [1.23, 1.73, 0.73]}, observable)
        """
        if not input_sets and not observables:
            raise ValueError("At least one of input_sets and observables must be specified")
        if observables:
            terms = observables.summands if isinstance(observables, Sum) else observables
            if any(isinstance(obs, Sum) for obs in terms):
                raise TypeError("Cannot have Sum Hamiltonian in list of observables")
        if circuit.result_types:
            raise ValueError("Circuit cannot have result types")
        self._circuit = circuit
        self._input_sets = ParameterSets(input_sets) if input_sets else None
        self._observables = observables or None

    @property
    def circuit(self) -> Circuit:
        """
        Circuit: The parametrized circuit
        """
        return self._circuit

    @property
    def input_sets(self) -> ParameterSets | None:
        """
        ParameterSets | None: The inputs to the circuit, if specified.
        """
        return self._input_sets

    @property
    def observables(self) -> Sequence[Observable] | Sum | None:
        """
        Sequence[Observable] | Sum | None: The observables or qubit Hamiltonian to measure,
        if specified.
        """
        return self._observables

    def to_ir(
        self,
        *,
        gate_definitions: Mapping[tuple[Gate, QubitSet], PulseSequence] | None = None,
    ) -> Program:
        """Serializes the circuit binding into a form that can run on a Braket device.

        Observables are treated as input parameters via conversion to Euler angles.

        Args:
            gate_definitions (dict[tuple[Gate, QubitSet], PulseSequence] | None): The
                calibration data for the device. default: None.

        Returns:
            Program: An OpenQASM program containing the serialized circuit and input parameters.
        """
        if observables := self._observables:
            terms = observables.summands if isinstance(observables, Sum) else observables
            euler_angles = {}
            for target in {target for obs in terms for target in obs.targets}:
                for param in euler_angle_parameter_names(target):
                    euler_angles[param] = [obs.euler_angles.get(param, 0) for obs in terms]
            return Program(
                source=self._circuit.with_euler_angles(observables)
                .to_ir(IRType.OPENQASM, gate_definitions=gate_definitions)
                .source,
                inputs=(
                    self._input_sets * euler_angles
                    if self._input_sets
                    else ParameterSets(euler_angles)
                ).as_dict(),
            )
        return Program(
            source=self._circuit.to_ir(IRType.OPENQASM, gate_definitions=gate_definitions).source,
            inputs=self._input_sets.as_dict() if self._input_sets else None,
        )

    def __len__(self):
        input_sets = self._input_sets
        observables = self._observables
        if input_sets and observables:
            return len(input_sets) * len(observables)
        if input_sets:
            return len(input_sets)
        return len(observables)

    def __eq__(self, other: CircuitBinding):
        if not isinstance(other, CircuitBinding):
            return False
        return (
            self._circuit == other._circuit
            and self._input_sets == other._input_sets
            and self._observables == other._observables
        )

    def __repr__(self):
        return (
            f"CircuitBinding(circuit={self._circuit!r}, "
            f"input_sets={self._input_sets}, "
            f"observables={self._observables})"
        )
