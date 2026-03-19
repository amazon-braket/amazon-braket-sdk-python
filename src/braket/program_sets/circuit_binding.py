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

import warnings
from collections import defaultdict
from collections.abc import Mapping, Sequence

from braket.ir.openqasm import Program

from braket.circuits import Circuit, Gate, Observable
from braket.circuits.observable import euler_angle_parameter_names
from braket.circuits.observables import Sum
from braket.circuits.serialization import IRType
from braket.program_sets.parameter_sets import ParameterSets, ParameterSetsLike
from braket.pulse import PulseSequence
from braket.quantum_information import PauliString
from braket.registers import QubitSet


class CircuitBinding:
    def __init__(
        self,
        circuit: Circuit,
        input_sets: ParameterSetsLike | None = None,
        observables: Sequence[Observable | PauliString | str] | Sum | None = None,
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
            observables (Sequence[Observable | PauliString | str] | Sum | None): The observables
                or Hamiltonian to measure, if specified.

        Examples:
            >>> circuit = Circuit().rx(0, FreeParameter("theta")).cnot(0, 1)
            >>> observable = 2.1 * X(0) @ Z(1) - 4.5 * Z(0) @ Y(1)  # Sum Hamiltonian
            >>> # observable = [X(0) @ Z(1), Z(0) @ Y(1)]  # Or a list of single-term observables
            >>> binding = CircuitBinding(circuit, {"theta": [1.23, 1.73, 0.73]}, observable)
        """
        if not input_sets and not observables:
            raise ValueError("At least one of input_sets and observables must be specified")
        if (
            observables
            and not isinstance(observables, Sum)
            and any(isinstance(obs, Sum) for obs in observables)
        ):
            raise TypeError("Cannot have Sum Hamiltonian in list of observables")
        if circuit.result_types:
            raise ValueError("Circuit cannot have result types")
        self._circuit = circuit
        self._input_sets = ParameterSets(input_sets) if input_sets else None
        self._observables = CircuitBinding._to_observables(observables)

    @staticmethod
    def _to_observables(
        observables: Sequence[Observable | PauliString | str] | Sum | None,
    ) -> Sequence[Observable] | Sum | None:
        if not observables:
            return None
        if isinstance(observables, Sum):
            return observables
        obs = []
        for o in observables:
            if isinstance(o, Observable):
                obs.append(o)
            elif isinstance(o, PauliString):
                obs.append(o.phase * o.to_unsigned_observable(include_trivial=True))
            else:
                pauli = PauliString(o)
                obs.append(pauli.phase * pauli.to_unsigned_observable(include_trivial=True))
        return obs

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
        if not self._observables:
            return Program(
                source=self._circuit.to_ir(
                    IRType.OPENQASM, gate_definitions=gate_definitions
                ).source,
                inputs=self._input_sets.as_dict() if self._input_sets else None,
            )
        # with_euler_angles validates that the observable has valid Euler angle gates
        circuit_with_euler_angles = self._circuit.with_euler_angles(self._observables)
        euler_angles = self._get_euler_angles()
        return Program(
            source=circuit_with_euler_angles.to_ir(
                IRType.OPENQASM, gate_definitions=gate_definitions
            ).source,
            inputs=(
                self._input_sets * euler_angles if self._input_sets else ParameterSets(euler_angles)
            ).as_dict(),
        )

    def _get_euler_angles(self) -> dict[str, float] | None:
        observables = self._observables
        return (
            self._get_euler_angles_sum(observables)
            if isinstance(observables, Sum)
            else self._get_euler_angles_list(observables)
        )

    def _get_euler_angles_sum(self, observables: Sum) -> dict[str, float]:
        euler_angles = defaultdict(list)
        summands = observables.summands
        if not observables.targets:
            targets = self._circuit.qubits
            for obs in summands:
                for param, angle in obs.get_euler_angles(targets).items():
                    euler_angles[param].append(angle)
            return euler_angles
        targets = QubitSet(q for obs in summands for q in obs.targets)
        for obs in summands:
            obs_euler_angles = obs.euler_angles
            for q in targets:
                for param in euler_angle_parameter_names(q):
                    euler_angles[param].append(obs_euler_angles.get(param, 0))
        return euler_angles

    def _get_euler_angles_list(self, observables: Sequence[Observable]) -> dict[str, float]:
        euler_angles = defaultdict(list)
        circuit_qubits = self._circuit.qubits
        targets = QubitSet(q for obs in observables for q in (obs.targets or circuit_qubits))
        for obs in observables:
            if not obs.targets:
                for param, angle in obs.get_euler_angles(targets).items():
                    euler_angles[param].append(angle)
            else:
                obs_euler_angles = obs.euler_angles
                for q in targets:
                    for param in euler_angle_parameter_names(q):
                        euler_angles[param].append(obs_euler_angles.get(param, 0))
        return euler_angles

    def bind_observables_to_inputs(
        self,
        inplace: bool = True,
        add_measure: bool = True,
    ) -> CircuitBinding:
        """
        Bind observables to input sets of parameters.

        Translates observables in a CircuitBinding to local measurement bases via a parameterized
        quantum circuit. The resulting composite input_set will be indexed to the same index in the
        CompositeEntry. entry.expectation will no longer work, and data will have to be processed
        as from a distribution. If using a Sum, information on the coefficients will be lost, as
        well as CompositeEntry.expectation.

        Kwargs:
            inplace (bool): whether or not to return a new circuit binding or use the same one
            add_measure (bool): whether or not to apply Measure instructions to the circuit

        Returns:
            CircuitBinding: A new circuit binding with the observables bound.
        """
        measure = Circuit()
        parameters = self._input_sets.as_dict() if self._input_sets else None
        if observables := self._observables:
            if isinstance(observables, Sum):
                observables = observables.summands
                warnings.warn(
                    "Binding a Sum discards information on observable weights; please "
                    "distribute your observable in advance using observable.summands.",
                    stacklevel=2,
                )
            euler_angles = self._get_euler_angles()
            if add_measure:
                for target in {int(p.split("_")[-1]) for p in euler_angles}:
                    measure.measure(target)
            measure = Circuit().with_euler_angles(observables) + measure
            parameters = self._input_sets * euler_angles if parameters else euler_angles
        if inplace:
            self._circuit.add_circuit(measure)
            self._observables = None
            self._input_sets = parameters
            return self
        return CircuitBinding(self._circuit + measure, input_sets=parameters)

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
