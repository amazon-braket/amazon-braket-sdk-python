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

from abc import abstractmethod

from braket.circuits.noise_model.criteria import Criteria
from braket.registers.qubit_set import QubitSetInput


class InitializationCriteria(Criteria):
    """Criteria that implement these methods may be used to determine initialization noise."""

    @abstractmethod
    def qubit_intersection(self, qubits: QubitSetInput) -> QubitSetInput:
        """Returns subset of passed qubits that match the criteria.

        Args:
            qubits (QubitSetInput): A qubit or set of qubits that may match the criteria.

        Returns:
            QubitSetInput: The subset of passed qubits that match the criteria.
        """
        raise NotImplementedError
