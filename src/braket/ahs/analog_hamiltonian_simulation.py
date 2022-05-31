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

from braket.ahs.atom_arrangement import AtomArrangement
from braket.ahs.hamiltonian import Hamiltonian
from braket.aws.aws_device import AwsDevice


class AnalogHamiltonianSimulation:
    def __init__(self, register: AtomArrangement, hamiltonian: Hamiltonian) -> None:
        """Creates an AnalogHamiltonianSimulation with a given setup, and terms.

        Args:
            register (AtomArrangement): The initial atom arrangement for the simulation.
            hamiltonian (Hamiltonian): The hamiltonian to simulate.
        """
        self._register = register
        self._hamiltonian = hamiltonian

    def discretize(self, device: AwsDevice) -> AnalogHamiltonianSimulation:
        """Creates a new AnalogHamiltonianSimulation with all numerical values represented
        as Decimal objects with fixed precision based on the capabilities of the device.

        Args:
            device (AwsDevice): The device for which to discretize the model.

        Returns:
            AnalogHamiltonianSimulation: A discretized version of this model.

        Raises:
            DiscretizeError: If unable to discretize the model.
        """
        raise NotImplementedError("Discretize is not yet implemented.")

    @property
    def register(self) -> AtomArrangement:
        return self._register

    @property
    def hamiltonian(self) -> Hamiltonian:
        return self._hamiltonian
