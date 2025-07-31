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

from collections.abc import Iterable
from typing import Optional

from braket.device_schema.result_type import ResultType

from braket.circuits import Circuit
from braket.circuits.result_type import ObservableResultType
from braket.passes import ValidationPass


class ResultTypeValidator(ValidationPass[Circuit]):
    def __init__(
        self,
        supported_result_types: Optional[Iterable[ResultType]] = None,
        connectivity_graph: Optional[dict[str, list[str]]] = None,
    ):
        """
        Args:
            supported_result_types (Optional[Iterable[str]]): A list of result types supported
                by the emulator. A result type is a Braket result type name.
            connectivity_graph (Dict[str, List[str]]): Graph representing qubit
                connectivity. The keys are qubit indices as strings, and the values are lists
                of neighboring qubit indices as strings.

        Raises:
            ValueError: If supported_result_types is empty or None.
            ValueError: If connectivity_graph is None.
        """
        if not supported_result_types:
            raise ValueError("Supported result types must be provided.")
        if connectivity_graph is None:
            raise ValueError("Connectivity graph must be provided.")

        self._supported_result_types = {
            result_type.name: result_type.observables for result_type in supported_result_types
        }

        self._connectivity_graph = connectivity_graph

    def validate(self, program: Circuit) -> None:
        """
        Checks that all result types used in the circuit are in this validator's
        supported result types set and that the target qubits are valid qubits in the device.

        Args:
            program (Circuit): The Braket circuit whose result types to validate.

        Raises:
            ValueError: If a result type is not in this validator's supported result types set
                or if a target qubit is not a valid qubit in the device.
        """
        for result_type in program.result_types:
            if result_type.name not in self._supported_result_types:
                raise ValueError(
                    f"Result type {result_type.name} is not a supported result type "
                    f"for this device."
                )

            if isinstance(result_type, ObservableResultType):
                observable_name = result_type.observable.name.lower()
                if observable_name not in self._supported_result_types[result_type.name]:
                    raise ValueError(
                        f"Observable {observable_name} is not supported for result type "
                        f"{result_type.name} on this device. Supported observables are: "
                        f"{self._supported_result_types[result_type.name]}."
                    )

            # Check if target qubits are valid qubits in the device
            target = result_type.target
            for qubit in target:
                qubit_str = str(int(qubit))
                if qubit_str not in self._connectivity_graph:
                    raise ValueError(
                        f"Qubit {int(qubit)} in result type {result_type.name} "
                        f"is not a valid qubit for this device."
                    )

    def __eq__(self, other: ValidationPass) -> bool:
        return (
            isinstance(other, ResultTypeValidator)
            and self._supported_result_types == other._supported_result_types
            and self._connectivity_graph == other._connectivity_graph
        )
