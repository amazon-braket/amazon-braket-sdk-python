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

from typing import List

from braket.ahs.field import Field
from braket.ahs.hamiltonian import Hamiltonian


class ShiftingField(Hamiltonian):
    def __init__(self, magnitude: Field) -> None:
        """Creates Hamiltonian Term for representing the Shifting Field that changes
        the energy of the Rydberg level in an AnalogHamiltonianSimulation.

        formula: - Delta(t) * Sum_k h_k |r_k><r_k|
        states:
          |r_k> : Rydberg state of atom k.
        other symbols:
          Sum_k : summation over all target atoms.

        Args:
            magnitude (Field): containing the global magnitude (Delta(t)) and the local
                pattern of real numbers between 0 and 1 (h_k):
        """
        super().__init__()
        self._magnitude = magnitude

    @property
    def terms(self) -> List[Hamiltonian]:
        return [self]

    @property
    def magnitude(self) -> Field:
        return self._magnitude
