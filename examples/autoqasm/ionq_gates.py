import numpy as np
import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.instructions import gpi, gpi2, ms


@aq.gate
def h(q: aq.Qubit):
    gpi2(q, np.pi / 2)
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
