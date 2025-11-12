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
from braket.circuits.noise_model import NoiseModel
from braket.emulation.passes import ModifierPass
from braket.program_sets import ProgramSet


class NoiseModelModifier(ModifierPass):
    """A modifier pass that applies noise models to circuits.

    This pass applies a specified noise model to circuits, adding noise operations
    according to the noise model's criteria. This is essential for realistic device
    emulation that includes noise characteristics.

    Supported specifications:
        - Circuit: Applies noise model to the circuit
        - ProgramSet: Recursively applies noise to all contained circuits

    Examples:
        >>> noise_model = NoiseModel().add_noise(BitFlip(0.1), GateCriteria(Gate.H))
        >>> modifier = NoiseModelModifier(noise_model)
        >>> circuit = Circuit().h(0)
        >>> noisy_circuit = modifier(circuit)
        >>> noisy_circuit = modifier.modify(circuit)
        >>> # Now has bit flip noise after H gate
    """

    def __init__(self, noise_model: NoiseModel):
        """Initialize the noise model modifier.

        Args:
            noise_model (NoiseModel): The noise model to apply to circuits. If None,
                        circuits are returned unchanged.
        """
        self._noise_model = noise_model
        self._supported_specifications = Circuit | ProgramSet

    def modify(self, circuits: Circuit | ProgramSet) -> Circuit | ProgramSet:
        """Apply noise model to circuits.

        Args:
            circuits: Circuit or ProgramSet to add noise to

        Returns:
            Circuit(s) with noise model applied
        """
        if self._noise_model is None:
            return circuits
        if isinstance(circuits, ProgramSet):
            return ProgramSet(
                [self.modify(item) for item in circuits],
                shots_per_executable=circuits.shots_per_executable,
            )
        return self._noise_model.apply(circuits)
