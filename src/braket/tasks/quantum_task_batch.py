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

from abc import ABC, abstractmethod

from braket.tasks import AnalogHamiltonianSimulationQuantumTaskResult, GateModelQuantumTaskResult


class QuantumTaskBatch(ABC):
    """An abstraction over a quantum task batch on a quantum device."""

    @abstractmethod
    def results(
        self,
    ) -> list[GateModelQuantumTaskResult | AnalogHamiltonianSimulationQuantumTaskResult]:
        """Get the quantum task results.

        Returns:
            list[GateModelQuantumTaskResult | AnalogHamiltonianSimulationQuantumTaskResult]: Get
            the quantum task results.
        """
