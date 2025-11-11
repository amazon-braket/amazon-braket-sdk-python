from braket.circuits import Circuit
from braket.circuits.noise_model import NoiseModel
from braket.emulation.passes import ModifierPass
from braket.program_sets import ProgramSet


class NoiseModelModifier(ModifierPass):
    def __init__(self, noise_model: NoiseModel):
        """ """
        self._noise_model = noise_model
        self._supported_specifications = Circuit | ProgramSet

    def modify(self, circuits: Circuit | ProgramSet) -> Circuit | ProgramSet:
        if self._noise_model is None:
            return circuits
        if isinstance(circuits, ProgramSet):
            return ProgramSet(
                [self.modify(item) for item in circuits],
                shots_per_executable=circuits.shots_per_executable)
        return self._noise_model.apply(circuits)
