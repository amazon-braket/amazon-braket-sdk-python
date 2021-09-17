import math

import numpy as np
import pytest

from braket.circuits import Circuit, CompositeOperator, Instruction

invalid_unitary_matrices = [
    (np.array([[1]])),
    (np.array([1])),
    (np.array([0, 1, 2])),
    (np.array([[0, 1], [1, 2], [3, 4]])),
    (np.array([[0, 1, 2], [2, 3]])),
    (np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]])),
    (np.array([[0, 1], [1, 1]])),
]


def two_dimensional_matrix_valid_input(i=3):
    unitary = np.array([[complex(0), complex(1)], [complex(1), complex(0)]])
    matrix = unitary
    for _ in range(i - 1):
        matrix = np.kron(matrix, unitary)
    return matrix


@pytest.mark.parametrize(
    "operator,subroutine_name,subroutine_inputs,targets",
    [
        (CompositeOperator.GHZ(3), "ghz", [[0, 1, 2]], [0, 1, 2]),
        (CompositeOperator.QFT(3, "default"), "qft", [[0, 1, 2], "default"], [0, 1, 2]),
        (CompositeOperator.QFT(3, "recursive"), "qft", [[0, 1, 2], "recursive"], [0, 1, 2]),
        (CompositeOperator.mQFT(3), "mqft", [[0, 1, 2]], [0, 1, 2]),
        (CompositeOperator.iQFT(3), "iqft", [[0, 1, 2]], [0, 1, 2]),
        (
            CompositeOperator.QPE(3, 3, two_dimensional_matrix_valid_input(), True),
            "qpe",
            [[0, 1, 2], [3, 4, 5], two_dimensional_matrix_valid_input(), True],
            list(range(6)),
        ),
        (
            CompositeOperator.QPE(3, 3, two_dimensional_matrix_valid_input(), False),
            "qpe",
            [[0, 1, 2], [3, 4, 5], two_dimensional_matrix_valid_input(), False],
            list(range(6)),
        ),
    ],
)
def test_composite_operator_subroutine(operator, subroutine_name, subroutine_inputs, targets):
    subroutine = getattr(Circuit(), subroutine_name)
    assert subroutine(*subroutine_inputs) == Circuit(Instruction(operator, targets))


@pytest.mark.parametrize(
    "operator, targets",
    [
        (CompositeOperator.GHZ(3), [0, 1, 2]),
        (CompositeOperator.QFT(3, "default"), [0, 1, 2]),
        (CompositeOperator.QFT(3, "recursive"), [0, 1, 2]),
        (CompositeOperator.mQFT(3), [0, 1, 2]),
        (CompositeOperator.iQFT(3), [0, 1, 2]),
        (CompositeOperator.QPE(3, 3, two_dimensional_matrix_valid_input(), True), list(range(6))),
        (CompositeOperator.QPE(3, 3, two_dimensional_matrix_valid_input(), False), list(range(6))),
    ],
)
def test_to_ir(operator, targets):
    assert operator.to_ir(targets) == [instr.to_ir() for instr in operator.decompose(targets)]


@pytest.mark.parametrize(
    "operator,ascii_symbols,qubit_count",
    [
        (CompositeOperator.GHZ(3), ["GHZ"], 3),
        (CompositeOperator.QFT(3, "default"), ["QFT"], 3),
        (CompositeOperator.QFT(3, "recursive"), ["QFT"], 3),
        (CompositeOperator.mQFT(3), ["mQFT"], 3),
        (CompositeOperator.iQFT(3), ["iQFT"], 3),
        (CompositeOperator.QPE(3, 3, two_dimensional_matrix_valid_input(), True), ["QPE"], 6),
        (CompositeOperator.QPE(3, 3, two_dimensional_matrix_valid_input(), False), ["QPE"], 6),
    ],
)
def test_constructor_properties(operator, ascii_symbols, qubit_count):
    assert list(operator.ascii_symbols) == ascii_symbols
    assert operator.qubit_count == qubit_count


def test_ghz_decompose():
    targets = [0, 1, 2]
    ghzcirc = Circuit().h(targets[0])
    for i in range(0, len(targets) - 1):
        ghzcirc.cnot(targets[i], targets[i + 1])

    assert Circuit(CompositeOperator.GHZ(3).decompose(targets)) == ghzcirc


def test_qft_default_decompose():
    targets = [0, 1, 2]
    qftcirc = Circuit()
    num_qubits = len(targets)
    for k in range(num_qubits):
        qftcirc.h(targets[k])

        for j in range(1, num_qubits - k):
            angle = 2 * math.pi / (2 ** (j + 1))
            qftcirc.cphaseshift(targets[k + j], targets[k], angle)

    qftcirc.swap(targets[0], targets[-1])

    assert Circuit(CompositeOperator.QFT(3).decompose(targets)) == qftcirc


def test_qft_recursive_decompose():
    targets = [0, 1, 2]
    qftcirc1 = Circuit().h(targets[0])
    qftcirc2 = Circuit().h([0])

    for k, qubit in enumerate(targets[1:]):
        qftcirc1.cphaseshift(qubit, targets[0], 2 * math.pi / (2 ** (k + 2)))

    qftcirc1.mqft(targets[1:])

    qftcirc1.swap(targets[0], targets[-1])

    assert Circuit(CompositeOperator.QFT(3, method="recursive").decompose(targets)) == qftcirc1
    assert Circuit(CompositeOperator.QFT(1, method="recursive").decompose([0])) == qftcirc2


@pytest.mark.xfail(raises=TypeError)
def test_qft_nonexistant_method():
    CompositeOperator.QFT(3, method="foo")


def test_mqft_decompose():
    targets = [0, 1, 2]
    mqftcirc1 = Circuit().h(targets[0])
    mqftcirc2 = Circuit().h([0])

    for k, qubit in enumerate(targets[1:]):
        mqftcirc1.cphaseshift(qubit, targets[0], 2 * math.pi / (2 ** (k + 2)))

    mqftcirc1.mqft(targets[1:])

    assert Circuit(CompositeOperator.mQFT(3).decompose(targets)) == mqftcirc1
    assert Circuit(CompositeOperator.mQFT(1).decompose([0])) == mqftcirc2


def test_iqft_decompose():
    targets = [0, 1, 2]
    iqftcirc = Circuit().swap(targets[0], targets[-1])
    num_qubits = len(targets)

    for k in reversed(range(num_qubits)):

        for j in reversed(range(1, num_qubits - k)):
            angle = -2 * math.pi / (2 ** (j + 1))
            iqftcirc.cphaseshift(targets[k + j], targets[k], angle)

        iqftcirc.h(targets[k])

    assert Circuit(CompositeOperator.iQFT(3).decompose(targets)) == iqftcirc


def controlled_unitary(control, target_qubits, unitary):
    p0 = np.array([[1.0, 0.0], [0.0, 0.0]])

    p1 = np.array([[0.0, 0.0], [0.0, 1.0]])

    circ = Circuit()
    id_matrix = np.eye(len(unitary))
    controlled_matrix = np.kron(p0, id_matrix) + np.kron(p1, unitary)

    targets = [control] + target_qubits

    circ.unitary(matrix=controlled_matrix, targets=targets)

    return circ


def test_qpe_control_decompose():
    precision_qubits = [0, 1, 2]
    query_qubits = [3, 4, 5]
    matrix = two_dimensional_matrix_valid_input()
    qpe_circ = Circuit().h(precision_qubits)

    for ii, qubit in enumerate(reversed(precision_qubits)):
        Uexp = np.linalg.matrix_power(matrix, 2 ** ii)
        qpe_circ.add_circuit(controlled_unitary(qubit, query_qubits, Uexp))

    qpe_circ.add(Circuit().iqft(precision_qubits))

    assert (
        Circuit(CompositeOperator.QPE(3, 3, matrix).decompose(precision_qubits + query_qubits))
        == qpe_circ
    )


def test_qpe_no_control_decompose():
    precision_qubits = [0, 1, 2]
    query_qubits = [3, 4, 5]
    matrix = two_dimensional_matrix_valid_input()
    qpe_circ = Circuit().h(precision_qubits)

    for ii, qubit in enumerate(reversed(precision_qubits)):
        for _ in range(2 ** ii):
            qpe_circ.add_circuit(controlled_unitary(qubit, query_qubits, matrix))

    qpe_circ.add(Circuit().iqft(precision_qubits))

    assert (
        Circuit(
            CompositeOperator.QPE(3, 3, matrix, control=False).decompose(
                precision_qubits + query_qubits
            )
        )
        == qpe_circ
    )


def test_qpe_qubit_count():
    matrix = two_dimensional_matrix_valid_input()
    operator1 = CompositeOperator.QPE(2, 3, matrix)
    operator2 = CompositeOperator.QPE(1, 3, matrix)

    assert operator1.qubit_count == 5
    assert operator2.qubit_count == 4


@pytest.mark.xfail(raises=ValueError)
def test_qpe_matrix_dim_mismatch():
    matrix = two_dimensional_matrix_valid_input()
    CompositeOperator.QPE(3, 2, matrix)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("matrix", invalid_unitary_matrices)
def test_qpe_unitary_invalid_matrix(matrix):
    query_qubit_count = np.log2(len(matrix))
    CompositeOperator.QPE(3, query_qubit_count, matrix)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize(
    "operator, target",
    [
        (CompositeOperator.GHZ(3), [0, 1]),
        (CompositeOperator.QFT(3, "default"), [0, 1]),
        (CompositeOperator.QFT(3, "recursive"), [0, 1]),
        (CompositeOperator.mQFT(3), [0, 1]),
        (CompositeOperator.iQFT(3), [0, 1]),
        (CompositeOperator.QPE(3, 3, two_dimensional_matrix_valid_input(), True), list(range(5))),
        (CompositeOperator.QPE(3, 3, two_dimensional_matrix_valid_input(), False), list(range(5))),
    ],
)
def test_decompose_with_mismatched_target(operator, target):
    operator.decompose(target)
