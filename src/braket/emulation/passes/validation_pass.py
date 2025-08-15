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

from abc import ABC, abstractmethod

from braket.circuits import Circuit


class ValidationPass(ABC, Circuit):
    @abstractmethod
    def validate(self, circuit: Circuit) -> None:
        """
        An emulator validator is used to perform some non-modifying validation
        pass on an input circuit. Implementations of validate should return
        nothing if the input circuit passes validation and raise an error otherwise.

        Args:
            circuit (Circuit): The circuit to be evaluated against this criteria.
        """
        raise NotImplementedError

    def run(self, circuit: Circuit) -> Circuit:
        """
        Validate the input circuit and return the circuit, unmodified.

        Args:
            circuit (Circuit): The circuit to validate.

        Returns:
            Circuit: The unmodified circuit passed in as input.
        """
        self.validate(circuit)
        return circuit

    def __call__(self, circuit: Circuit) -> Circuit:
        return self.run(circuit)
