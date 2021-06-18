import unittest
from typing import Iterable

import numpy as np
import math
import pytest
from braket.ir.jaqcd.shared_models import (
    Angle,
    DoubleControl,
    DoubleTarget,
    MultiTarget,
    MultiControl,
    SingleControl,
    SingleTarget,
    TwoDimensionalMatrix,
)

from braket.circuits import Circuit, CompositeOperator, Instruction, QubitSet

testdata = [
    (CompositeOperator.GHZ, "ghz", [MultiTarget], {}),
    (CompositeOperator.QFT, "qft", [MultiTarget], {}),
    (CompositeOperator.iQFT, "iqft", [MultiTarget], {}),
    (CompositeOperator.QPE, "qpe", [MultiTarget, MultiTarget, TwoDimensionalMatrix], {
        "input_type": complex, "option": True}),
    (CompositeOperator.QPE, "qpe", [MultiTarget, MultiTarget, TwoDimensionalMatrix], {
        "input_type": complex, "option": False}),
]


def single_target_valid_input(**kwargs):
    return {"target": 2}


def double_target_valid_ir_input(**kwargs):
    return {"targets": [2, 3]}


def double_target_valid_input(**kwargs):
    return {"target1": 2, "target2": 3}


def angle_valid_input(**kwargs):
    return {"angle": 0.123}


def single_control_valid_input(**kwargs):
    return {"control": 0}


def double_control_valid_ir_input(**kwargs):
    return {"controls": [0, 1]}


def double_control_valid_input(**kwargs):
    return {"control1": 0, "control2": 1}


def multi_target_valid_input(i=-1, **kwargs):
    if i >= 0:
        return {f"targets{i+1}": list(range(3 * i + 30, 3 * i + 33))}
    return {"targets": list(range(30, 33))}


def multi_control_valid_input(**kwargs):
    return {"controls": list(range(4, 7))}


def two_dimensional_matrix_valid_ir_input(**kwargs):
    return {"matrix": [[[0, 0], [1, 0]], [[1, 0], [0, 0]]]}


def two_dimensional_matrix_valid_input(**kwargs):
    input_type = kwargs.get("input_type")
    unitary = np.array([[input_type(0), input_type(1)], [input_type(1), input_type(0)]])
    return {"matrix": np.kron(np.kron(unitary, unitary), unitary)}


def calculate_qubit_count(irsubclasses, multi_test_value):
    qubit_count = 0
    for subclass in irsubclasses:
        if subclass == SingleTarget:
            qubit_count += 1
        elif subclass == DoubleTarget:
            qubit_count += 2
        elif subclass == SingleControl:
            qubit_count += 1
        elif subclass == DoubleControl:
            qubit_count += 2
        elif subclass == MultiTarget:
            qubit_count += multi_test_value
        elif subclass == MultiControl:
            qubit_count += multi_test_value
        elif subclass == Angle or subclass == TwoDimensionalMatrix:
            pass
        else:
            raise ValueError("Invalid subclass")
    return qubit_count


valid_ir_switcher = {
    "SingleTarget": single_target_valid_input,
    "DoubleTarget": double_target_valid_ir_input,
    "SingleControl": single_control_valid_input,
    "DoubleControl": double_control_valid_ir_input,
    "MultiTarget": multi_target_valid_input,
    "MultiControl": multi_control_valid_input,
    "TwoDimensionalMatrix": two_dimensional_matrix_valid_ir_input,
}

valid_subroutine_switcher = dict(
    valid_ir_switcher,
    **{
        "TwoDimensionalMatrix": two_dimensional_matrix_valid_input,
        "DoubleTarget": double_target_valid_input,
        "DoubleControl": double_control_valid_input,
    }
)


def create_valid_subroutine_input(irsubclasses, **kwargs):
    input = {}
    num_multi_target = 0
    for subclass in irsubclasses:
        if subclass is MultiTarget:
            num_multi_target += 1
        else:
            input.update(
                valid_subroutine_switcher.get(subclass.__name__, lambda: "Invalid subclass")(**kwargs)
            )
    if num_multi_target == 1:
        input.update(
            valid_subroutine_switcher.get(MultiTarget.__name__, lambda: "Invalid subclass")(**kwargs)
        )
    elif num_multi_target > 1:
        for i in range(num_multi_target):
            input.update(multi_target_valid_input(i))
    return input


def create_valid_target_input(irsubclasses):
    input = {}
    qubit_set = []
    multi_target_counter = 0
    # based on the concept that control goes first in target input
    for subclass in irsubclasses:
        if subclass == SingleTarget:
            qubit_set.extend(list(single_target_valid_input().values()))
        elif subclass == DoubleTarget:
            qubit_set.extend(list(double_target_valid_ir_input().values()))
        elif subclass == MultiTarget:
            qubit_set.extend(list(multi_target_valid_input(multi_target_counter).values()))
            multi_target_counter += 1
        elif subclass == SingleControl:
            qubit_set = list(single_control_valid_input().values()) + qubit_set
        elif subclass == DoubleControl:
            qubit_set = list(double_control_valid_ir_input().values()) + qubit_set
        elif subclass == Angle or subclass == TwoDimensionalMatrix:
            pass
        else:
            raise ValueError("Invalid subclass")
    input["target"] = QubitSet(qubit_set)
    return input


def create_valid_composite_operator_class_input(subroutine_name, irsubclasses, **kwargs):
    input = {}
    num_multi_target = irsubclasses.count(MultiTarget)
    if num_multi_target > 1:
        if subroutine_name == 'qpe':
            input.update({
                'precision_qubit_count': 3,
                'query_qubit_count': 3,
                'condense': kwargs.get('option')
            })
    elif num_multi_target == 1:
        input.update({
            'qubit_count': 3
        })
    if Angle in irsubclasses:
        input.update(angle_valid_input())
    if TwoDimensionalMatrix in irsubclasses:
        input.update(two_dimensional_matrix_valid_input(**kwargs))
    return input


def create_valid_instruction_input(testclass, subroutine_name, irsubclasses, **kwargs):
    input = create_valid_target_input(irsubclasses)
    input["operator"] = testclass(**create_valid_composite_operator_class_input(subroutine_name, irsubclasses, **kwargs))
    return input


@pytest.mark.parametrize("testclass,subroutine_name,irsubclasses,kwargs", testdata)
def test_composite_operator_subroutine(testclass, subroutine_name, irsubclasses, kwargs):
    qubit_count = calculate_qubit_count(irsubclasses, 3)
    subroutine = getattr(Circuit(), subroutine_name)
    assert subroutine(**create_valid_subroutine_input(irsubclasses, **kwargs)) == Circuit(
        Instruction(**create_valid_instruction_input(testclass, subroutine_name, irsubclasses, **kwargs))
    )

def expected_ghz_circuit():
    targets = create_valid_subroutine_input([MultiTarget])['targets']
    ghzcirc = Circuit().h(targets[0])
    for i in range(0, len(targets)-1):
        ghzcirc.cnot(targets[i], targets[i+1])

    return ghzcirc

def expected_qft_circuit():
    targets = create_valid_subroutine_input([MultiTarget])['targets']
    qftcirc = Circuit()
    num_qubits = len(targets)

    for k in range(num_qubits):
        qftcirc.h(targets[k])

        for j in range(1,num_qubits - k):
            angle = 2*math.pi/(2**(j+1))
            qftcirc.cphaseshift(targets[k + j], targets[k], angle)

    for i in range(math.floor(num_qubits/2)):
        qftcirc.swap(targets[i], targets[-i - 1])

    return qftcirc

def expected_iqft_circuit():
    targets = create_valid_subroutine_input([MultiTarget])['targets']
    qftcirc = Circuit()
    num_qubits = len(targets)

    for i in range(math.floor(num_qubits/2)):
        qftcirc.swap(targets[i], targets[-i - 1])

    for k in reversed(range(num_qubits)):

        for j in reversed(range(1, num_qubits - k)):
            angle = -2*math.pi/(2**(j+1))
            qftcirc.cphaseshift(targets[k + j], targets[k], angle)

        qftcirc.h(targets[k])

    return qftcirc

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

def expected_qpe_circuit(control):
    input = create_valid_subroutine_input([MultiTarget, MultiTarget, TwoDimensionalMatrix], input_type=complex)
    precision_qubits = input['targets1']
    query_qubits = input['targets2']
    matrix = input['matrix']
    qpe_circ = Circuit()
    qpe_circ.h(precision_qubits)

    for ii, qubit in enumerate(reversed(precision_qubits)):
        power = ii

        if control:
            Uexp = np.linalg.matrix_power(matrix, 2 ** power)

            qpe_circ.add_circuit(controlled_unitary(qubit, query_qubits, Uexp))
        else:
            for _ in range(2**power):
                qpe_circ.add_circuit(controlled_unitary(qubit, query_qubits, matrix))

    qpe_circ.add(Circuit().iqft(precision_qubits))

    return qpe_circ

@pytest.mark.xfail(raises=ValueError)
@pytest.mark.parametrize("testclass,subroutine_name,irsubclasses,kwargs", testdata)
def test_decompose_with_mismatched_target(testclass, subroutine_name, irsubclasses, kwargs):
    testclass(**create_valid_composite_operator_class_input(subroutine_name, irsubclasses, **kwargs)).decompose(
        QubitSet(create_valid_target_input(irsubclasses).values())[:-1]
    )

def get_expected_circuit(**kwargs):
    if 'option' in kwargs.keys():
        return {
            "qpe": expected_qpe_circuit(kwargs.get('option'))
        }
    return {
        "ghz": expected_ghz_circuit(),
        "qft": expected_qft_circuit(),
        "iqft": expected_iqft_circuit(),
    }

@pytest.mark.parametrize("testclass,subroutine_name,irsubclasses,kwargs", testdata)
def test_decompose(testclass, subroutine_name, irsubclasses, kwargs):
    ret = testclass(**create_valid_composite_operator_class_input(subroutine_name, irsubclasses, **kwargs)).decompose(
        create_valid_target_input(irsubclasses)['target']
    )
    assert isinstance(ret, Iterable)
    for obj in ret:
        assert isinstance(obj, Instruction)
    assert get_expected_circuit(**kwargs)[subroutine_name] == Circuit().add(
        ret
    )
