import pytest

from braket.circuits import Circuit

# Diagram


@pytest.mark.xfail(raises=ValueError)
def test_unknown_gate():
    diag_inp = """
T  : | 0 |

q0 : --W--

T  : | 0 |
"""
    Circuit().from_diagram(diag_inp)


@pytest.mark.xfail(raises=ValueError)
def test_gate_syntax_error():
    diag_inp = """
T  : | 0 |

q0 : --#--

T  : | 0 |
"""
    Circuit().from_diagram(diag_inp)


@pytest.mark.xfail(raises=ValueError)
def test_unknown_observable():
    diag_inp = """
T  : |0|1|2|3|4|                  Result Types                  |

q0 : -H-C-------Sample(W@Y@Z)-Expectation(X@Y@Z)-Variance(X@Y@Z)-
        |       |             |                  |
q1 : ---X-------Sample()------Expectation(X@Y@Z)-Variance(X@Y@Z)-

T  : |0|1|2|3|4|                  Result Types                  |
"""
    Circuit().from_diagram(diag_inp)


# repr

# A good repr_inpt
# repr_inp = "Circuit('instructions': [Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(0)])), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(0), Qubit(1)]))])"  # noqa: E501


@pytest.mark.xfail(raises=ValueError)
def test_token_not_terminated():
    repr_inp = "Circuit('instructions)"
    Circuit().from_repr(repr_inp)


@pytest.mark.xfail(raises=ValueError)
def test_name_not_followed_by_a_colon():
    repr_inp = "Circuit('instructions')"
    Circuit().from_repr(repr_inp)


@pytest.mark.xfail(raises=ValueError)
def test_invalid_scalar():
    repr_inp = "Circuit('instructions': [Instruction('operator': H('qubit_count': 1.2.3), 'target': QubitSet([Qubit(0)])), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(0), Qubit(1)]))])"  # noqa: E501
    Circuit().from_repr(repr_inp)


@pytest.mark.xfail(raises=ValueError)
def test_array_not_closed():
    repr_inp = "Circuit('instructions': [Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(0)])), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(0), Qubit(1)]))_)"  # noqa: E501
    Circuit().from_repr(repr_inp)


@pytest.mark.xfail(raises=ValueError)
def test_unknown_operator():
    repr_inp = "Circuit('instructions': [Instruction('operator': HH('qubit_count': 1), 'target': QubitSet([Qubit(0)])), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(0), Qubit(1)]))])"  # noqa: E501
    Circuit().from_repr(repr_inp)


@pytest.mark.xfail(raises=ValueError)
def test_qubit_name_error():
    repr_inp = "Circuit('instructions': [Instruction('operator': H('qubit_count': 1), 'target': QubitSet([QBIT(0)])), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(0), Qubit(1)]))])"  # noqa: E501
    Circuit().from_repr(repr_inp)


@pytest.mark.xfail(raises=ValueError)
def test_qubitset_array_name_error():
    repr_inp = "Circuit('instructions': [Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(0)])), Instruction('operator': CNot('qubit_count': 2), 'target': QBITSET([Qubit(0), Qubit(1)]))])"  # noqa: E501
    Circuit().from_repr(repr_inp)


@pytest.mark.xfail(raises=ValueError)
def test_qubitset_array_not_closed():
    repr_inp = "Circuit('instr': [Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(0)])), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(0), Qubit(1)_))_)"  # noqa: E501
    Circuit().from_repr(repr_inp)


@pytest.mark.xfail(raises=ValueError)
def test_tensorproduct_name_error():
    repr_inp = "Circuit('instructions': [Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(0)])), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(0), Qubit(1)])), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(1), Qubit(2)])), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(2), Qubit(3)])), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(3), Qubit(4)]))], 'result_types': [Sample(observable=TensorProduct(X('qubit_count': 1), Y('qubit_count': 1), Z('qubit_count': 1)), target=QubitSet([Qubit(0), Qubit(1), Qubit(2)])), Probability(target=QubitSet([Qubit(3), Qubit(4)])), Expectation(observable=TensorProduct(X('qubit_count': 1), Y('qubit_count': 1), Z('qubit_count': 1)), target=QubitSet([Qubit(0), Qubit(1), Qubit(2)])), Variance(observable=TensorPROD(X('qubit_count': 1), Y('qubit_count': 1), Z('qubit_count': 1)), target=QubitSet([Qubit(0), Qubit(1), Qubit(2)]))])"  # noqa: E501
    Circuit().from_repr(repr_inp)


@pytest.mark.xfail(raises=ValueError)
def test_typed_value_not_closed():
    repr_inp = "Circuit('instructions': [Instruction('operator': H('qubit_count': 1), 'target': QubitSet([Qubit(0)]x)), Instruction('operator': CNot('qubit_count': 2), 'target': QubitSet([Qubit(0), Qubit(1)]))])"  # noqa: E501
    Circuit().from_repr(repr_inp)
