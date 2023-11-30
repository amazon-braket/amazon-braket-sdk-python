import numpy as np

import braket.experimental.autoqasm as aq
from braket.devices import LocalSimulator
from braket.experimental.autoqasm.instructions import measure, u


@aq.gate
def u2(target: aq.Qubit, phi: float, lambda_: float):
    u(target, np.pi, phi, lambda_)


@aq.gate
def u3(target: aq.Qubit, theta: float, phi: float, lambda_: float):
    u(target, theta, phi, lambda_)


@aq.main
def demo_gates():
    u(0, 1, 2, 3)
    u2(0, 4, 5)
    u3(0, 6, 7, 8)
    measure(0)


print(demo_gates.to_ir())
"""
OPENQASM 3.0;
gate u2(phi, lambda_) target {
    U(3.141592653589793, phi, lambda_) target;
}
gate u3(theta, phi, lambda_) target {
    U(theta, phi, lambda_) target;
}
qubit[1] __qubits__;
U(1, 2, 3) __qubits__[0];
u2(4, 5) __qubits__[0];
u3(6, 7, 8) __qubits__[0];
bit __bit_0__;
__bit_0__ = measure __qubits__[0];
"""
print(LocalSimulator().run(demo_gates, shots=10).result().measurements)
# {'__bit_0__': [1, 1, 1, 1, 1, 1, 1, 1, 0, 1]}
