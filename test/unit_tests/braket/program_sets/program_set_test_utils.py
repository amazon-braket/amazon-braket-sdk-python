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
from braket.circuits.serialization import IRType


def get_circuit_source(circuit):
    return circuit.to_ir(IRType.OPENQASM).source


def ghz(n):
    circuit = Circuit().h(0)
    for i in range(n - 1):
        circuit.cnot(i, i + 1)
    return circuit
