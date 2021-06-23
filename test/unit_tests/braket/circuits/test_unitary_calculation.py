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

import numpy as np
import pytest

from braket.circuits import Circuit, Observable, ResultType, gates, noise
from braket.circuits.unitary_calculation import as_unitary


def test_as_unitary_empty_instructions_returns_empty_array():
    as_unitary(Circuit()) == []


@pytest.mark.parametrize(
    "circuit",
    [
        (Circuit().phaseshift(0, 0.15).apply_gate_noise(noise.Noise.BitFlip(probability=0.1))),
        (Circuit().cnot(1, 0).apply_gate_noise(noise.Noise.TwoQubitDepolarizing(probability=0.1))),
        (
            Circuit()
            .x(1)
            .i(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[1])
        ),
        (
            Circuit()
            .x(1)
            .i(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[2])
        ),
        (Circuit().x(1).i(2).apply_gate_noise(noise.Noise.BitFlip(probability=0.1))),
        (Circuit().x(1).apply_gate_noise(noise.Noise.BitFlip(probability=0.1)).i(2)),
        (
            Circuit()
            .y(1)
            .z(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[1])
        ),
        (
            Circuit()
            .y(1)
            .z(2)
            .apply_gate_noise(noise.Noise.BitFlip(probability=0.1), target_qubits=[2])
        ),
        (Circuit().y(1).z(2).apply_gate_noise(noise.Noise.BitFlip(probability=0.1))),
        (Circuit().y(1).apply_gate_noise(noise.Noise.BitFlip(probability=0.1)).z(2)),
        (
            Circuit()
            .cphaseshift(2, 1, 0.15)
            .si(3)
            .apply_gate_noise(
                noise.Noise.TwoQubitDepolarizing(probability=0.1), target_qubits=[1, 2]
            )
        ),
        (
            Circuit()
            .cphaseshift(2, 1, 0.15)
            .apply_gate_noise(noise.Noise.TwoQubitDepolarizing(probability=0.1))
            .si(3)
        ),
    ],
)
@pytest.mark.xfail(raises=TypeError)
def test_as_unitary_noise_raises_error(circuit):
    as_unitary(circuit)


def test_as_unitary_noise_not_apply_returns_expected_unitary(recwarn):
    circuit = (
        Circuit()
        .cphaseshift(2, 1, 0.15)
        .si(3)
        .apply_gate_noise(noise.Noise.TwoQubitDepolarizing(probability=0.1), target_qubits=[1, 3])
    )

    assert len(recwarn) == 1
    assert str(recwarn[0].message).startswith("Noise is not applied to any gate")

    assert np.allclose(
        as_unitary(circuit),
        np.kron(gates.Si().to_matrix(), np.kron(gates.CPhaseShift(0.15).to_matrix(), np.eye(2))),
    )


@pytest.mark.parametrize(
    "circuit,expected_unitary",
    [
        (Circuit().h(0), gates.H().to_matrix()),
        (Circuit().h(0).add_result_type(ResultType.Probability(target=[0])), gates.H().to_matrix()),
        (Circuit().x(0), gates.X().to_matrix()),
        (Circuit().y(0), gates.Y().to_matrix()),
        (Circuit().z(0), gates.Z().to_matrix()),
        (Circuit().s(0), gates.S().to_matrix()),
        (Circuit().si(0), gates.Si().to_matrix()),
        (Circuit().t(0), gates.T().to_matrix()),
        (Circuit().ti(0), gates.Ti().to_matrix()),
        (Circuit().v(0), gates.V().to_matrix()),
        (Circuit().vi(0), gates.Vi().to_matrix()),
        (Circuit().rx(0, 0.15), gates.Rx(0.15).to_matrix()),
        (Circuit().ry(0, 0.15), gates.Ry(0.15).to_matrix()),
        (Circuit().rz(0, 0.15), gates.Rz(0.15).to_matrix()),
        (Circuit().phaseshift(0, 0.15), gates.PhaseShift(0.15).to_matrix()),
        (Circuit().cnot(1, 0), gates.CNot().to_matrix()),
        (Circuit().cnot(1, 0).add_result_type(ResultType.StateVector()), gates.CNot().to_matrix()),
        (Circuit().swap(1, 0), gates.Swap().to_matrix()),
        (Circuit().swap(0, 1), gates.Swap().to_matrix()),
        (Circuit().iswap(1, 0), gates.ISwap().to_matrix()),
        (Circuit().iswap(0, 1), gates.ISwap().to_matrix()),
        (Circuit().pswap(1, 0, 0.15), gates.PSwap(0.15).to_matrix()),
        (Circuit().pswap(0, 1, 0.15), gates.PSwap(0.15).to_matrix()),
        (Circuit().xy(1, 0, 0.15), gates.XY(0.15).to_matrix()),
        (Circuit().xy(0, 1, 0.15), gates.XY(0.15).to_matrix()),
        (Circuit().cphaseshift(1, 0, 0.15), gates.CPhaseShift(0.15).to_matrix()),
        (Circuit().cphaseshift00(1, 0, 0.15), gates.CPhaseShift00(0.15).to_matrix()),
        (Circuit().cphaseshift01(1, 0, 0.15), gates.CPhaseShift01(0.15).to_matrix()),
        (Circuit().cphaseshift10(1, 0, 0.15), gates.CPhaseShift10(0.15).to_matrix()),
        (Circuit().cy(1, 0), gates.CY().to_matrix()),
        (Circuit().cz(1, 0), gates.CZ().to_matrix()),
        (Circuit().xx(1, 0, 0.15), gates.XX(0.15).to_matrix()),
        (Circuit().yy(1, 0, 0.15), gates.YY(0.15).to_matrix()),
        (Circuit().zz(1, 0, 0.15), gates.ZZ(0.15).to_matrix()),
        (Circuit().ccnot(2, 1, 0), gates.CCNot().to_matrix()),
        (
            Circuit()
            .ccnot(2, 1, 0)
            .add_result_type(ResultType.Expectation(observable=Observable.Y(), target=[1])),
            gates.CCNot().to_matrix(),
        ),
        (Circuit().ccnot(1, 2, 0), gates.CCNot().to_matrix()),
        (Circuit().cswap(2, 1, 0), gates.CSwap().to_matrix()),
        (Circuit().cswap(2, 0, 1), gates.CSwap().to_matrix()),
        (Circuit().h(1), np.kron(gates.H().to_matrix(), np.eye(2))),
        (Circuit().x(1).i(2), np.kron(np.eye(2), np.kron(gates.X().to_matrix(), np.eye(2)))),
        (
            Circuit().y(1).z(2),
            np.kron(gates.Z().to_matrix(), np.kron(gates.Y().to_matrix(), np.eye(2))),
        ),
        (Circuit().rx(1, 0.15), np.kron(gates.Rx(0.15).to_matrix(), np.eye(2))),
        (
            Circuit().ry(1, 0.15).i(2),
            np.kron(np.eye(2), np.kron(gates.Ry(0.15).to_matrix(), np.eye(2))),
        ),
        (
            Circuit().rz(1, 0.15).s(2),
            np.kron(gates.S().to_matrix(), np.kron(gates.Rz(0.15).to_matrix(), np.eye(2))),
        ),
        (Circuit().pswap(2, 1, 0.15), np.kron(gates.PSwap(0.15).to_matrix(), np.eye(2))),
        (Circuit().pswap(1, 2, 0.15), np.kron(gates.PSwap(0.15).to_matrix(), np.eye(2))),
        (
            Circuit().xy(2, 1, 0.15).i(3),
            np.kron(np.eye(2), np.kron(gates.XY(0.15).to_matrix(), np.eye(2))),
        ),
        (
            Circuit().xy(1, 2, 0.15).i(3),
            np.kron(np.eye(2), np.kron(gates.XY(0.15).to_matrix(), np.eye(2))),
        ),
        (
            Circuit().cphaseshift(2, 1, 0.15).si(3),
            np.kron(
                gates.Si().to_matrix(), np.kron(gates.CPhaseShift(0.15).to_matrix(), np.eye(2))
            ),
        ),
        (Circuit().ccnot(3, 2, 1), np.kron(gates.CCNot().to_matrix(), np.eye(2))),
        (Circuit().ccnot(2, 3, 1), np.kron(gates.CCNot().to_matrix(), np.eye(2))),
        (
            Circuit().cswap(3, 2, 1).i(4),
            np.kron(np.eye(2), np.kron(gates.CSwap().to_matrix(), np.eye(2))),
        ),
        (
            Circuit().cswap(3, 1, 2).i(4),
            np.kron(np.eye(2), np.kron(gates.CSwap().to_matrix(), np.eye(2))),
        ),
        (
            Circuit().cswap(3, 2, 1).t(4),
            np.kron(gates.T().to_matrix(), np.kron(gates.CSwap().to_matrix(), np.eye(2))),
        ),
        (
            Circuit().cswap(3, 1, 2).t(4),
            np.kron(gates.T().to_matrix(), np.kron(gates.CSwap().to_matrix(), np.eye(2))),
        ),
        (Circuit().h(0).h(0), gates.I().to_matrix()),
        (Circuit().h(0).x(0), np.dot(gates.X().to_matrix(), gates.H().to_matrix())),
        (Circuit().x(0).h(0), np.dot(gates.H().to_matrix(), gates.X().to_matrix())),
        (
            Circuit().y(0).z(1).cnot(1, 0),
            np.dot(gates.CNot().to_matrix(), np.kron(gates.Z().to_matrix(), gates.Y().to_matrix())),
        ),
        (
            Circuit().z(0).y(1).cnot(1, 0),
            np.dot(gates.CNot().to_matrix(), np.kron(gates.Y().to_matrix(), gates.Z().to_matrix())),
        ),
        (
            Circuit().z(0).y(1).cnot(1, 0).cnot(2, 1),
            np.dot(
                np.dot(
                    np.dot(
                        np.kron(gates.CNot().to_matrix(), np.eye(2)),
                        np.kron(np.eye(2), gates.CNot().to_matrix()),
                    ),
                    np.kron(np.kron(np.eye(2), gates.Y().to_matrix()), np.eye(2)),
                ),
                np.kron(np.eye(4), gates.Z().to_matrix()),
            ),
        ),
        (
            Circuit().z(0).y(1).cnot(1, 0).ccnot(2, 1, 0),
            np.dot(
                np.dot(
                    np.dot(
                        gates.CCNot().to_matrix(),
                        np.kron(np.eye(2), gates.CNot().to_matrix()),
                    ),
                    np.kron(np.kron(np.eye(2), gates.Y().to_matrix()), np.eye(2)),
                ),
                np.kron(np.eye(4), gates.Z().to_matrix()),
            ),
        ),
        (
            Circuit().cnot(0, 1),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(0, 1, 2),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(1, 0, 2),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(0, 2, 1),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().ccnot(2, 0, 1),
            np.array(
                [
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                ],
                dtype=complex,
            ),
        ),
        (
            Circuit().s(0).v(1).cnot(0, 1).cnot(1, 2),
            np.dot(
                np.dot(
                    np.dot(
                        np.kron(
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                            np.eye(2),
                        ),
                        np.kron(
                            np.eye(2),
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                        ),
                    ),
                    np.kron(np.kron(np.eye(2), gates.V().to_matrix()), np.eye(2)),
                ),
                np.kron(np.eye(4), gates.S().to_matrix()),
            ),
        ),
        (
            Circuit().z(0).y(1).cnot(0, 1).ccnot(0, 1, 2),
            np.dot(
                np.dot(
                    np.dot(
                        np.array(
                            [
                                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                                [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                            ],
                            dtype=complex,
                        ),
                        np.kron(
                            np.eye(2),
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                        ),
                    ),
                    np.kron(np.kron(np.eye(2), gates.Y().to_matrix()), np.eye(2)),
                ),
                np.kron(np.eye(4), gates.Z().to_matrix()),
            ),
        ),
        (
            Circuit().z(0).y(1).cnot(0, 1).ccnot(2, 0, 1),
            np.dot(
                np.dot(
                    np.dot(
                        np.array(
                            [
                                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                            ],
                            dtype=complex,
                        ),
                        np.kron(
                            np.eye(2),
                            np.array(
                                [
                                    [1.0, 0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0, 1.0],
                                    [0.0, 0.0, 1.0, 0.0],
                                    [0.0, 1.0, 0.0, 0.0],
                                ],
                                dtype=complex,
                            ),
                        ),
                    ),
                    np.kron(np.kron(np.eye(2), gates.Y().to_matrix()), np.eye(2)),
                ),
                np.kron(np.eye(4), gates.Z().to_matrix()),
            ),
        ),
    ],
)
def test_as_unitary_circuit_returns_expected_unitary(circuit, expected_unitary):
    assert np.allclose(as_unitary(circuit), expected_unitary)
