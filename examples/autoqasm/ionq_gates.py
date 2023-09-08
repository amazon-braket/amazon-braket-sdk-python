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

"""Custom AutoQASM gate implementations using IonQ native gates."""

import numpy as np
import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.instructions import gpi, gpi2, ms


@aq.gate
def h(q: aq.Qubit):
    gpi2(q, np.pi / 2)
    gpi(q, 0)


@aq.gate
def x(q: aq.Qubit):
    gpi(q, 0)


@aq.gate
def u(q: aq.Qubit, a: float, b: float, c: float):
    gpi2(q, a)
    gpi(q, b)
    gpi2(q, c)


@aq.gate
def rx(q: aq.Qubit, theta: float):
    u(q, np.pi / 2, theta / 2 + np.pi / 2, np.pi / 2)


@aq.gate
def ry(q: aq.Qubit, theta: float):
    u(q, np.pi, theta / 2 + np.pi, np.pi)


@aq.gate
def cnot(q0: aq.Qubit, q1: aq.Qubit):
    ry(q0, np.pi / 2)
    ms(q0, q1, 0, 0, np.pi / 2)
    rx(q0, -np.pi / 2)
    rx(q1, -np.pi / 2)
    ry(q0, -np.pi / 2)
