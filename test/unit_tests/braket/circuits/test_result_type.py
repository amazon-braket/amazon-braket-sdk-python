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
import re

import pytest

from braket.circuits import Observable, ObservableResultType, ResultType
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.result_type import ObservableParameterResultType
from braket.circuits.serialization import IRType
from braket.registers import QubitSet


@pytest.fixture
def result_type():
    return ResultType(ascii_symbols=["foo"])


@pytest.fixture
def prob():
    return ResultType.Probability([0, 1])


@pytest.fixture
def sv():
    return ResultType.StateVector()


def test_none_ascii():
    with pytest.raises(ValueError):
        ResultType(ascii_symbols=None)


def test_name(result_type):
    expected = result_type.__class__.__name__
    assert result_type.name == expected


def test_ascii_symbol():
    ascii_symbols = ["foo"]
    result_type = ResultType(ascii_symbols=ascii_symbols)
    assert result_type.ascii_symbols == ascii_symbols


def test_equality_statevector():
    result1 = ResultType.StateVector()
    result2 = ResultType.StateVector()
    result3 = ResultType.Probability([1])
    result4 = "hi"
    assert result1 == result2
    assert result1 != result3
    assert result1 != result4


def test_equality_densitymatrix():
    result1 = ResultType.DensityMatrix()
    result2 = ResultType.DensityMatrix()
    result3 = ResultType.StateVector()
    result4 = "foo"
    assert result1 == result2
    assert result1 != result3
    assert result1 != result4


def test_ascii_symbol_setter(result_type):
    with pytest.raises(AttributeError):
        result_type.ascii_symbols = ["bar"]


def test_name_setter(result_type):
    with pytest.raises(AttributeError):
        result_type.name = "hi"


def test_register_result():
    class _FooResultType(ResultType):
        def __init__(self):
            super().__init__(ascii_symbols=["foo"])

    ResultType.register_result_type(_FooResultType)
    assert ResultType._FooResultType().name == _FooResultType().name


def test_copy_creates_new_object(prob):
    copy = prob.copy()
    assert copy == prob
    assert copy is not prob


def test_copy_with_mapping_target(sv):
    target_mapping = {0: 10, 1: 11}
    expected = ResultType.StateVector()
    assert sv.copy(target_mapping=target_mapping) == expected


def test_copy_with_mapping_target_hasattr(prob):
    target_mapping = {0: 10, 1: 11}
    expected = ResultType.Probability([10, 11])
    assert prob.copy(target_mapping=target_mapping) == expected


def test_copy_with_target_hasattr(prob):
    target = [10, 11]
    expected = ResultType.Probability(target)
    assert prob.copy(target=target) == expected


def test_copy_with_target(sv):
    target = [10, 11]
    expected = ResultType.StateVector()
    assert sv.copy(target=target) == expected


def test_copy_with_target_and_mapping(prob):
    with pytest.raises(TypeError):
        prob.copy(target=[10], target_mapping={0: 10})


# ObservableResultType


def test_expectation_init_value_error_target():
    with pytest.raises(ValueError):
        ObservableResultType(
            ascii_symbols=["Obs", "Obs"], observable=Observable.X() @ Observable.Y(), target=[]
        )


def test_expectation_init_value_error_ascii_symbols():
    with pytest.raises(ValueError):
        ObservableResultType(
            ascii_symbols=["Obs"], observable=Observable.X() @ Observable.Y(), target=[1, 2]
        )


def test_obs_rt_init_value_error_qubit_count():
    with pytest.raises(ValueError):
        ObservableResultType(ascii_symbols=["Obs"], observable=Observable.X(), target=[0, 1])


def test_obs_rt_equality():
    a1 = ObservableResultType(ascii_symbols=["Obs"], observable=Observable.X(), target=0)
    a2 = ObservableResultType(ascii_symbols=["Obs"], observable=Observable.X(), target=0)
    a3 = ObservableResultType(ascii_symbols=["Obs"], observable=Observable.X(), target=1)
    a4 = "hi"
    assert a1 == a2
    assert a1 != a3
    assert a1 != a4
    assert ResultType.Variance(observable=Observable.Y(), target=0) != ResultType.Expectation(
        observable=Observable.Y(), target=0
    )


def test_obs_rt_repr():
    a1 = ObservableResultType(ascii_symbols=["Obs"], observable=Observable.X(), target=0)
    assert (
        str(a1)
        == "ObservableResultType(observable=X('qubit_count': 1), target=QubitSet([Qubit(0)]))"
    )


def test_obs_rt_target():
    assert ObservableResultType(
        ascii_symbols=["Obs"], observable=Observable.X(), target=1
    ).target == QubitSet(1)
    assert ObservableResultType(
        ascii_symbols=["Obs"], observable=Observable.X(1)
    ).target == QubitSet(1)


@pytest.mark.parametrize(
    "ir_type, serialization_properties, expected_exception, expected_message",
    [
        (IRType.JAQCD, None, NotImplementedError, "to_jaqcd has not been implemented yet."),
        (IRType.OPENQASM, None, NotImplementedError, "to_openqasm has not been implemented yet."),
        ("invalid-ir-type", None, ValueError, "Supplied ir_type invalid-ir-type is not supported."),
        (
            IRType.OPENQASM,
            "invalid-serialization-properties",
            ValueError,
            "serialization_properties must be of type OpenQASMSerializationProperties for "
            "IRType.OPENQASM.",
        ),
    ],
)
def test_result_type_to_ir(
    ir_type, serialization_properties, expected_exception, expected_message, result_type
):
    with pytest.raises(expected_exception) as exc:
        result_type.to_ir(ir_type, serialization_properties=serialization_properties)
    assert exc.value.args[0] == expected_message


# Observable Result Type with Params


def test_expectation_init_value_error_target_adjoint_gradient():
    tensor_operation_error = re.escape(
        "Observable TensorProduct(X('qubit_count': 1), "
        "Y('qubit_count': 1)) must only operate on 1 qubit for target=None"
    )
    with pytest.raises(ValueError, match=tensor_operation_error):
        ObservableParameterResultType(
            ascii_symbols=["Obs", "Obs"],
            observable=Observable.X() @ Observable.Y(),
            target=[],
            parameters=["alpha"],
        )


def test_expectation_init_value_error_ascii_symbols_adjoint_gradient():
    ascii_and_obs_qubit_count_mismatch = (
        "Observable's qubit count and the number of ASCII symbols must be equal"
    )
    with pytest.raises(ValueError, match=ascii_and_obs_qubit_count_mismatch):
        ObservableParameterResultType(
            ascii_symbols=["Obs"],
            observable=Observable.X() @ Observable.Y(),
            target=[1, 2],
            parameters=[],
        )


def test_obs_rt_init_value_error_qubit_count_adjoint_gradient():
    obs_and_target_count_mismatch = re.escape(
        "Observable's qubit count 1 and the size of the target "
        "qubit set QubitSet([Qubit(0), Qubit(1)]) must be equal"
    )
    with pytest.raises(ValueError, match=obs_and_target_count_mismatch):
        ObservableParameterResultType(
            ascii_symbols=["Obs"], observable=Observable.X(), target=[0, 1]
        )


def test_valid_result_type_for__adjoint_gradient():
    ObservableParameterResultType(
        ascii_symbols=["Obs", "Obs"],
        observable=Observable.X() @ Observable.Y(),
        target=[0, 1],
        parameters=["alpha", FreeParameter("beta")],
    )


def test_obs_rt_repr_adjoint_gradient():
    a1 = ObservableParameterResultType(
        ascii_symbols=["Obs"], observable=Observable.X(), target=0, parameters=["alpha"]
    )
    assert (
        str(a1) == "ObservableParameterResultType(observable=X('qubit_count': 1), "
        "target=QubitSet([Qubit(0)]), parameters=['alpha'])"
    )
