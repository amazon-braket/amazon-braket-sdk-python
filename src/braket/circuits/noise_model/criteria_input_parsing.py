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
from typing import Optional, Union

from braket.circuits.quantum_operator import QuantumOperator
from braket.registers.qubit_set import QubitSetInput


def parse_operator_input(
    operators: Union[QuantumOperator, Iterable[QuantumOperator]],
) -> Optional[set[QuantumOperator]]:
    """Processes the quantum operator input to __init__ to validate and return a set of
    QuantumOperators.

    Args:
        operators (Union[QuantumOperator, Iterable[QuantumOperator]]): QuantumOperator input.

    Returns:
        Optional[set[QuantumOperator]]: The set of relevant QuantumOperators or None if none
        is specified.

    Throws:
        ValueError: If no quantum operator are provided, if the quantum operator don't all operate
            on the same number of qubits.
    """
    if not operators:
        return None
    if not isinstance(operators, Iterable):
        return {operators}
    fixed_qubit_counts = {operator.fixed_qubit_count() for operator in operators}
    if len(fixed_qubit_counts) != 1:
        raise ValueError("All operators in a criteria must operate on the same number of qubits.")
    return set(operators)


def parse_qubit_input(
    qubits: Optional[QubitSetInput], expected_qubit_count: Optional[int] = 0
) -> Optional[set[Union[int, tuple[int]]]]:
    """Processes the qubit input to __init__ to validate and return a set of qubit targets.

    Args:
        qubits (Optional[QubitSetInput]): Qubit input.
        expected_qubit_count (Optional[int]): The expected number of qubits that the input
            gates operates on. If the value is non-zero, this method will validate that the
            expected qubit count matches the actual qubit count. Default is 0.

    Returns:
        Optional[set[Union[int, tuple[int]]]]: The set of qubit targets, or None if no qubits
        are specified.
    """
    if qubits is None:
        return None
    if not isinstance(qubits, Iterable):
        return {int(qubits)}
    if len(qubits) == 0:
        return None
    types = {type(item) for item in qubits}
    if len(types) != 1:
        raise TypeError("Qubit targets must be all the same type.")
    qubit_count = (
        expected_qubit_count if expected_qubit_count is not None and expected_qubit_count > 0 else 1
    )
    if isinstance(qubits[0], Iterable):
        qubit_count = (
            expected_qubit_count
            if expected_qubit_count is not None and expected_qubit_count > 0
            else len(qubits[0])
        )
        target_set_all_same = all(len(item) == qubit_count for item in qubits)
        if not target_set_all_same:
            raise ValueError(f"Qubits must all target {qubit_count}-qubit operations.")
        if qubit_count == 1:
            return {item[0] for item in qubits}
        return {tuple(item) for item in qubits}
    return {tuple(qubits)} if qubit_count > 1 else set(qubits)
