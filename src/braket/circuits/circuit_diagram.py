# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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


class CircuitDiagram(ABC):
    """A class that builds circuit diagrams."""

    @staticmethod
    @abstractmethod
    def build_diagram(circuit) -> str:
        """
        Build a diagram for the suppplied `circuit`.

        Args:
            circuit (Circuit): The circuit to build a diagram for.

        Returns:
            str: String representation for the circuit diagram.
                Empty string is returned for an empty circuit.
        """
