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

from braket.circuits import Circuit
from braket.circuits.measure import Measure
from braket.emulation.passes import TransformationPass
from braket.program_sets import ProgramSet, CircuitBinding


class MeasurementTransformation(TransformationPass):
    """A transformation pass that automatically adds measurements to circuits that lack them.

    This pass ensures that circuits have measurements for execution by adding measurements
    to all qubits in circuits that have neither explicit measurements nor result types.

    Supported specifications:
        - Circuit: Adds measurements if needed
        - ProgramSet: Recursively applies to all contained circuits

    Examples:
        >>> modifier = MeasurementModifier()
        >>> circuit = Circuit().h(0).cnot(0, 1)  # No measurements
        >>> modified = modifier(circuit)
        >>> # Now has measurements on qubits 0 and 1
    """

    def __init__(self):
        """Initialize the measurement modifier."""
        self._supported_specifications = Circuit | ProgramSet

    def transform(self, circuits: Circuit | ProgramSet) -> Circuit | ProgramSet:
        """Add measurements to circuits that lack them.

        For ProgramSets, we only apply if there are no observables. 

        Args:
            circuits: Circuit or ProgramSet to modify

        Returns:
            Modified circuit(s) with measurements added where needed
        """
        if isinstance(circuits, ProgramSet):
            new_programs = []
            for program in circuits:
                match program:
                    case Circuit():
                        new_programs.append(self.transform(program))
                    case CircuitBinding() as entry if entry.observables:
                        new_programs.append(entry)
                    case CircuitBinding():
                        new_programs.append(CircuitBinding(
                            self.transform(program.circuit),
                            input_sets=program.input_sets))
                    case _:
                        raise NotImplementedError
            return ProgramSet(new_programs, shots_per_executable=circuits.shots_per_executable)

        has_measurement = any(
            isinstance(instr.operator, Measure) for instr in circuits.instructions
        )
        if (not has_measurement) and len(circuits.result_types) == 0:
            circuits.measure(target_qubits=circuits.qubits)
        return circuits
