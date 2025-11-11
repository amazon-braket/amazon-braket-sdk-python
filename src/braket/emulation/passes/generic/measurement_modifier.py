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