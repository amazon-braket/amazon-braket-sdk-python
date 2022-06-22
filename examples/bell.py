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
import cmath
import math
import time

import numpy as np

from braket.aws import AwsDevice
from braket.circuits import Circuit

device = AwsDevice("arn:aws:braket:::device/quantum-simulator/amazon/sv1")

# https://wikipedia.org/wiki/Bell_state

bell = Circuit()
for i in range(30):
    bell.h(i)
start_builtin = time.time()
task = device.run(bell, shots=100)
result = task.result()
end_builtin = time.time()
print(f"builtin h: {end_builtin - start_builtin}")

bell = Circuit()
for i in range(30):
    bell.unitary([i], 1 / np.sqrt(2) * np.array([[1, 1], [1, -1]]))
start_custom_h = time.time()
task = device.run(bell, shots=100)
result = task.result()
end_custom_h = time.time()
print(f"custom h: {end_custom_h - start_custom_h}")


_theta, _lambda, _phi = 1, 2, 3
unitary = np.array(
    [
        [
            math.cos(_theta / 2),
            -cmath.exp(1j * _lambda) * math.sin(_theta / 2),
        ],
        [
            cmath.exp(1j * _phi) * math.sin(_theta / 2),
            cmath.exp(1j * (_phi + _lambda)) * math.cos(_theta / 2),
        ],
    ]
)

bell = Circuit()
for i in range(30):
    bell.unitary([i], unitary)
start_custom = time.time()
task = device.run(bell, shots=100)
result = task.result()
end_custom = time.time()
print(f"custom rand: {end_custom_h - start_custom_h}")
