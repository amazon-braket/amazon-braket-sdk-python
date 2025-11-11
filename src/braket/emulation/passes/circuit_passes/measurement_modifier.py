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
from braket.emulation.passes import ModifierPass
from braket.program_sets import ProgramSet


class MeasurementModifier(ModifierPass):
    def __init__(self):
        self._supported_specifications = Circuit | ProgramSet

    def modify(self, circuits: Circuit | ProgramSet) -> Circuit | ProgramSet:
        if isinstance(circuits, ProgramSet):
            return ProgramSet(
                [self.modify(item) for item in circuits],
                shots_per_executable=circuits.shots_per_executable)

        has_measurement = any(
            isinstance(instr.operator, Measure) for instr in circuits.instructions
        )
        if (not has_measurement) and len(circuits.result_types) == 0:
            circuits.measure(target_qubits=circuits.qubits)
        return circuits