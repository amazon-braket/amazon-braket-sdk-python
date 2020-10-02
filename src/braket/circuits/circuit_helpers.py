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

from braket.circuits import Circuit, ResultType


def validate_circuit_and_shots(circuit: Circuit, shots: int) -> None:
    """
    Validates if circuit and shots are correct before running on a device

    Args:
        circuit (Circuit): circuit to validate
        shots (int): shots to validate

    Raises:
        ValueError: If circuit has no instructions. Also, if no result types
            specified for circuit and `shots=0`. See `braket.circuit.result_types`.
            Or, if `StateVector` or `Amplitude` are specified as result types when `shots > 0`.
    """
    if not circuit.instructions:
        raise ValueError("Circuit must have instructions to run on a device")
    if not shots and not circuit.result_types:
        raise ValueError(
            "No result types specified for circuit and shots=0. See `braket.circuit.result_types`"
        )
    elif shots and circuit.result_types:
        for rt in circuit.result_types:
            if isinstance(rt, ResultType.StateVector) or isinstance(rt, ResultType.Amplitude):
                raise ValueError("StateVector or Amplitude cannot be specified when shots>0")
