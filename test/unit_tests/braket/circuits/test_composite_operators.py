
import math
from typing import Iterable

import numpy as np
import pytest

from braket.circuits import Circuit, CompositeOperator, Instruction, QubitSet

testdata = [
    (CompositeOperator.GHZ, "ghz", ["MultiTarget"], {}),
    (CompositeOperator.QFT, "qft", ["MultiTarget"], {"option": "recursive"}),
    (CompositeOperator.QFT, "qft", ["MultiTarget"], {"option": "default"}),
    (CompositeOperator.mQFT, "mqft", ["MultiTarget"], {}),
    (CompositeOperator.iQFT, "iqft", ["MultiTarget"], {}),
    (CompositeOperator.QPE, "qpe", ["MultiTarget", "MultiTarget", "TwoDimensionalMatrix"], {
        "input_type": complex, "option": True}),
    (CompositeOperator.QPE, "qpe", ["MultiTarget", "MultiTarget", "TwoDimensionalMatrix"], {
        "input_type": complex, "option": False}),
]


invalid_unitary_matrices = [
    (np.array([[1]])),
    (np.array([1])),
    (np.array([0, 1, 2])),
    (np.array([[0, 1], [1, 2], [3, 4]])),
    (np.array([[0, 1, 2], [2, 3]])),
    (np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]])),
    (np.array([[0, 1], [1, 1]])),
]


ascii_symbols = {
    "ghz": "GHZ",
    "qft": "QFT",
    "iqft": "iQFT",
    "mqft": "mQFT",
    "qpe": "QPE"
}


def single_target_valid_input(**kwargs):
    return {"target": 2}


def double_target_valid_input(**kwargs):
    return {"target1": 2, "target2": 3}


def angle_valid_input(**kwargs):
    return {"angle": 0.123}


def single_control_valid_input(**kwargs):
    return {"control": 0}


def double_control_valid_input(**kwargs):
    return {"control1": 0, "control2": 1}


def multi_target_valid_input(i=-1, **kwargs):
    if i >= 0:
        return {f"targets{i + 1}": list(range(3 * i + 30, 3 * i + 33))}
    return {"targets": list(range(30, 33))}


def multi_control_valid_input(**kwargs):
    return {"controls": list(range(4, 7))}


def two_dimensional_matrix_valid_input(i=3, **kwargs):
    input_type = kwargs.get("input_type")
    unitary = np.array([[input_type(0), input_type(1)], [input_type(1), input_type(0)]])
    matrix = unitary
    for _ in range(i - 1):
        matrix = np.kron(matrix, unitary)
    return {"matrix": matrix}


valid_subroutine_input = {
    "SingleTarget": single_target_valid_input,
    "DoubleTarget": double_target_valid_input,
    "SingleControl": single_control_valid_input,
    "DoubleControl": double_control_valid_input,
    "MultiTarget": multi_target_valid_input,
    "MultiControl": multi_control_valid_input,
    "TwoDimensionalMatrix": two_dimensional_matrix_valid_input,
}


def create_valid_subroutine_input(input_types, **kwargs):
    input = {}
    num_multi_target = 0
    for input_type in input_types:
        if input_type is "MultiTarget":
            num_multi_target += 1
        else:
            input.update(
                valid_subroutine_input.get(input_type, lambda: "Invalid input_type")(**kwargs)
            )
    if num_multi_target == 1:
        input.update(
            valid_subroutine_input.get("MultiTarget", lambda: "Invalid input_type")(**kwargs)
        )
    elif num_multi_target > 1:
        for i in range(num_multi_target):
            input.update(multi_target_valid_input(i))
    return input


def create_valid_target_input(input_types):
    input = {}
    qubit_set = []
    multi_target_counter = 0
    # based on the concept that control goes first in target input
    for input_type in input_types:
        if input_type == "SingleTarget":
            qubit_set.extend(list(single_target_valid_input().values()))
        elif input_type == "DoubleTarget":
            qubit_set.extend(list(double_target_valid_input().values()))
        elif input_type == "MultiTarget":
            qubit_set.extend(list(multi_target_valid_input(multi_target_counter).values()))
            multi_target_counter += 1
        elif input_type == "SingleControl":
            qubit_set = list(single_control_valid_input().values()) + qubit_set
        elif input_type == "DoubleControl":
            qubit_set = list(double_control_valid_input().values()) + qubit_set
        elif input_type == "Angle" or input_type == "TwoDimensionalMatrix":
            pass
        else:
            raise ValueError("Invalid input_type")
    input["target"] = QubitSet(qubit_set)
    return input


def calculate_qubit_count(input_types, multi_test_value=3):
    qubit_count = 0
    for input_type in input_types:
        if input_type == "SingleTarget":
            qubit_count += 1
        elif input_type == "DoubleTarget":
            qubit_count += 2
        elif input_type == "SingleControl":
            qubit_count += 1
        elif input_type == "DoubleControl":
            qubit_count += 2
        elif input_type == "MultiTarget":
            qubit_count += multi_test_value
        elif input_type == "MultiControl":
            qubit_count += multi_test_value
        elif input_type == "Angle" or input_type == "TwoDimensionalMatrix":
            pass
        else:
            raise ValueError("Invalid input type")
    return qubit_count


def create_valid_composite_operator_class_input(subroutine_name, input_types, multi_test_value=3, **kwargs):
    input = {}
    num_multi_target = input_types.count("MultiTarget")
    if num_multi_target > 1:
        if subroutine_name == 'qpe':
            input.update({
                'precision_qubit_count': multi_test_value,
                'query_qubit_count': multi_test_value,
                'control': kwargs.get('option')
            })
    elif num_multi_target == 1:
        if subroutine_name == 'qft':
            input.update({
                'method': kwargs.get('option')
            })
        input.update({
            'qubit_count': multi_test_value
        })
    if "Angle" in input_types:
        input.update(angle_valid_input())
    if "TwoDimensionalMatrix" in input_types:
        input.update(two_dimensional_matrix_valid_input(multi_test_value, **kwargs))
    return input


def create_valid_instruction_input(testclass, subroutine_name, input_types, **kwargs):
    input = create_valid_target_input(input_types)
    input["operator"] = testclass(**create_valid_composite_operator_class_input(subroutine_name, input_types, **kwargs))
    return input


@pytest.mark.parametrize("testclass,subroutine_name,input_types,kwargs", testdata)
def test_composite_operator_subroutine(testclass, subroutine_name, input_types, kwargs):
    subroutine = getattr(Circuit(), subroutine_name)
    assert subroutine(**create_valid_subroutine_input(input_types, **kwargs)) == Circuit(
        Instruction(**create_valid_instruction_input(testclass, subroutine_name, input_types, **kwargs))
    )


@pytest.mark.parametrize("testclass,subroutine_name,input_types,kwargs", testdata)
def test_to_ir(testclass, subroutine_name, input_types, kwargs):
    operator = testclass(**create_valid_composite_operator_class_input(subroutine_name, input_types, **kwargs))
    target = QubitSet(create_valid_target_input(input_types).values())
    assert operator.to_ir(target) == [instr.to_ir() for instr in operator.decompose(target)]


@pytest.mark.parametrize("testclass,subroutine_name,input_types,kwargs", testdata)
def test_correct_ascii_symbols(testclass, subroutine_name, input_types, kwargs):
    operator = testclass(**create_valid_composite_operator_class_input(subroutine_name, input_types, **kwargs))
    assert operator.ascii_symbols[0] == ascii_symbols[subroutine_name]


@pytest.mark.parametrize("testclass,subroutine_name,input_types,kwargs", testdata)
def test_correct_qubit_count(testclass, subroutine_name, input_types, kwargs):
    operator1 = testclass(**create_valid_composite_operator_class_input(subroutine_name, input_types, **kwargs))
    operator2 = testclass(**create_valid_composite_operator_class_input(subroutine_name, input_types, 4, **kwargs))

    assert operator1.qubit_count == calculate_qubit_count(input_types)
    assert operator2.qubit_count == calculate_qubit_count(input_types, 4)


def test_ghz_decompose():
    targets = create_valid_subroutine_input(["MultiTarget"])['targets']
    ghzcirc = Circuit().h(targets[0])
    for i in range(0, len(targets) - 1):
        ghzcirc.cnot(targets[i], targets[i + 1])

    assert Circuit(CompositeOperator.GHZ(3).decompose(targets)) == ghzcirc


def test_qft_default_decompose():
    targets = create_valid_subroutine_input(["MultiTarget"])['targets']
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
    targets = create_valid_subroutine_input(["MultiTarget"])['targets']
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
    targets = create_valid_subroutine_input(["MultiTarget"])['targets']
    mqftcirc1 = Circuit().h(targets[0])
    mqftcirc2 = Circuit().h([0])

    for k, qubit in enumerate(targets[1:]):
        mqftcirc1.cphaseshift(qubit, targets[0], 2 * math.pi / (2 ** (k + 2)))

    mqftcirc1.mqft(targets[1:])

    assert Circuit(CompositeOperator.mQFT(3).decompose(targets)) == mqftcirc1
    assert Circuit(CompositeOperator.mQFT(1).decompose([0])) == mqftcirc2


def test_iqft_decompose():
    targets = create_valid_subroutine_input(["MultiTarget"])['targets']
    iqftcirc = Circuit().swap(targets[0], targets[-1])
    num_qubits = len(targets)

    for k in reversed(range(num_qubits)):

        for j in reversed(range(1, num_qubits - k)):
            angle = -2 * math.pi / (2 ** (j + 1))
            iqftcirc.cphaseshift(targets[k + j], targets[k], angle)

        iqftcirc.h(targets[k])

    assert Circuit(CompositeOperator.iQFT(3).decompose(targets)) == iqftcirc


def controlled_unitary(control, target_qubits, unitary):
    p0 = np.array([[1., 0.],
                   [0., 0.]])

    p1 = np.array([[0., 0.],
                   [0., 1.]])

    circ = Circuit()
    id_matrix = np.eye(len(unitary))
    controlled_matrix = np.kron(p0, id_matrix) + np.kron(p1, unitary)

    targets = [control] + target_qubits

    circ.unitary(matrix=controlled_matrix, targets=targets)

    return circ


def test_qpe_control_decompose():
    input = create_valid_subroutine_input(["MultiTarget", "MultiTarget", "TwoDimensionalMatrix"], input_type=complex)
    precision_qubits = input['targets1']
    query_qubits = input['targets2']
    matrix = input['matrix']
    qpe_circ = Circuit().h(precision_qubits)

    for ii, qubit in enumerate(reversed(precision_qubits)):
        Uexp = np.linalg.matrix_power(matrix, 2 ** ii)
        qpe_circ.add_circuit(controlled_unitary(qubit, query_qubits, Uexp))

    qpe_circ.add(Circuit().iqft(precision_qubits))

    assert Circuit(CompositeOperator.QPE(3, 3, matrix).decompose(precision_qubits + query_qubits)) == qpe_circ


def test_qpe_no_control_decompose():
    input = create_valid_subroutine_input(["MultiTarget", "MultiTarget", "TwoDimensionalMatrix"], input_type=complex)
    precision_qubits = input['targets1']
    query_qubits = input['targets2']
    matrix = input['matrix']
    qpe_circ = Circuit().h(precision_qubits)

    for ii, qubit in enumerate(reversed(precision_qubits)):
        for _ in range(2 ** ii):
            qpe_circ.add_circuit(controlled_unitary(qubit, query_qubits, matrix))

    qpe_circ.add(Circuit().iqft(precision_qubits))

    assert Circuit(CompositeOperator.QPE(3, 3, matrix, control=False).decompose(precision_qubits + query_qubits))\
           == qpe_circ


def test_qpe_qubit_count():
    matrix = create_valid_subroutine_input(["TwoDimensionalMatrix"], input_type=complex)['matrix']
    operator1 = CompositeOperator.QPE(2,3,matrix)
    operator2 = CompositeOperator.QPE(1,3,matrix)

    assert operator1.qubit_count == 5
    assert operator2.qubit_count == 4


@pytest.mark.xfail(raises=ValueError)
def test_qpe_matrix_dim_mismatch():
    matrix = create_valid_subroutine_input(["TwoDimensionalMatrix"], input_type=complex)['matrix']
    CompositeOperator.QPE(3,2,matrix)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("matrix", invalid_unitary_matrices)
def test_qpe_unitary_invalid_matrix(matrix):
    query_qubit_count = np.log2(len(matrix))
    CompositeOperator.QPE(3, query_qubit_count, matrix)


@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("testclass,subroutine_name,input_types,kwargs", testdata)
def test_decompose_with_mismatched_target(testclass, subroutine_name, input_types, kwargs):
    testclass(**create_valid_composite_operator_class_input(subroutine_name, input_types, **kwargs)).decompose(
        QubitSet(create_valid_target_input(input_types).values())[:-1]
    )
