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

import numpy as np
import pytest
from program_set_test_utils import get_circuit_source, ghz

from braket.circuits import Circuit
from braket.circuits.observable import euler_angle_parameter_names
from braket.circuits.observables import X, Y, Z
from braket.ir.openqasm.program_set_v1 import ProgramSet as IrProgramSet
from braket.ir.openqasm.program_v1 import Program
from braket.parametric import FreeParameter
from braket.program_sets.circuit_binding import CircuitBinding
from braket.program_sets.program_set import ProgramSet


def test_single_circuit_binding(circuit_rx_parametrized):
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=[{"theta": 1.23}, {"theta": 3.21}])
    program_set = ProgramSet(binding)
    assert len(program_set) == 1
    assert program_set.total_executables == 2
    assert program_set[0] == program_set.entries[0] == binding
    assert program_set.to_ir() == IrProgramSet(
        programs=[
            Program(
                source=get_circuit_source(circuit_rx_parametrized), inputs={"theta": [1.23, 3.21]}
            )
        ]
    )
    assert program_set == ProgramSet([binding])
    with pytest.raises(ValueError):
        program_set.total_shots


def test_multiple_programs(circuit_rx_parametrized):
    circ1 = Circuit().rx(0, 1.23)
    circ2 = Circuit().rx(0, 3.21)
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=[{"theta": 1.23}, {"theta": 3.21}])
    program_set = ProgramSet([circ1, binding, circ2], 100)
    assert len(program_set) == 3
    assert program_set.total_executables == 4
    assert program_set[0] == program_set.entries[0] == circ1
    assert program_set[1] == program_set.entries[1] == binding
    assert program_set[2] == program_set.entries[2] == circ2
    inputs = {"theta": [1.23, 3.21]}
    assert program_set.to_ir() == IrProgramSet(
        programs=[
            Program(source=get_circuit_source(circ1), inputs={}),
            Program(source=get_circuit_source(circuit_rx_parametrized), inputs=inputs),
            Program(source=get_circuit_source(circ2), inputs={}),
        ]
    )
    assert program_set.total_shots == 400
    assert program_set == ProgramSet([circ1, binding, circ2], shots_per_executable=100)
    assert str(program_set) == (
        f"ProgramSet(programs=[{repr(circ1)}, "
        f"CircuitBinding(circuit={repr(circuit_rx_parametrized)}, "
        f"input_sets={inputs}, "
        f"observables=None), "
        f"{repr(circ2)}], "
        f"shots_per_executable=100)"
    )


def test_add(circuit_rx_parametrized):
    circuit_h = ghz(1)
    circuit_bell = ghz(2)
    ghz3 = ghz(3)
    program_set = (
        ProgramSet([circuit_h, circuit_bell], 100)
        + [CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [3.21, 2.31]}), ghz3]
        + ProgramSet(CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [1.23, 0.12]}))
    )
    assert len(program_set) == 5
    assert program_set.total_executables == 7
    assert program_set.total_shots == 700
    assert program_set.to_ir() == IrProgramSet(
        programs=[
            Program(source=get_circuit_source(circuit_h), inputs={}),
            Program(source=get_circuit_source(circuit_bell), inputs={}),
            Program(
                source=get_circuit_source(circuit_rx_parametrized), inputs={"theta": [3.21, 2.31]}
            ),
            Program(source=get_circuit_source(ghz3), inputs={}),
            Program(
                source=get_circuit_source(circuit_rx_parametrized), inputs={"theta": [1.23, 0.12]}
            ),
        ]
    )


def test_add_other_shots(circuit_rx_parametrized):
    circuit_h = ghz(1)
    circuit_bell = ghz(2)
    ghz3 = ghz(3)
    program_set = (
        ProgramSet([circuit_h, circuit_bell])
        + [CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [3.21, 2.31]}), ghz3]
        + ProgramSet(
            CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [1.23, 0.12]}), 100
        )
    )
    assert program_set.total_shots == 700


def test_result_type(circuit_rx_parametrized):
    with pytest.raises(ValueError):
        ProgramSet([
            CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [3.21, 2.31]}),
            ghz(2).expectation(X(0)),
        ])


def test_add_mismatched_shots():
    circuit_h = ghz(1)
    circuit_bell = ghz(2)
    with pytest.raises(ValueError):
        ProgramSet([circuit_h, circuit_bell], 100) + ProgramSet([circuit_h, circuit_bell], 1000)


def test_add_wrong_type():
    with pytest.raises(TypeError):
        ProgramSet([Circuit().h(0), Circuit().rx(0, 1.23)]) + 3


def test_zip_binding_observables(circuit_rx_parametrized):
    obs1 = Y(1)
    obs2 = Z(0) @ X(1)
    program_set = ProgramSet.zip(
        CircuitBinding(circuit_rx_parametrized, observables=[obs1, obs2]),
        input_sets=[{"theta": 1.23}, {"theta": 3.21}],
        shots_per_executable=100,
    )
    assert len(program_set) == 2
    assert program_set.total_executables == 2
    assert program_set.total_shots == 200
    euler_0 = euler_angle_parameter_names(0)
    euler_1 = euler_angle_parameter_names(1)
    assert program_set.to_ir() == IrProgramSet(
        programs=[
            Program(
                source=get_circuit_source(circuit_rx_parametrized.with_euler_angles([obs1])),
                inputs={
                    "theta": [1.23],
                    euler_1[0]: [0],
                    euler_1[1]: [np.pi / 2],
                    euler_1[2]: [np.pi / 2],
                },
            ),
            Program(
                source=get_circuit_source(circuit_rx_parametrized.with_euler_angles([obs2])),
                inputs={
                    "theta": [3.21],
                    euler_0[0]: [0],
                    euler_0[1]: [0],
                    euler_0[2]: [0],
                    euler_1[0]: [np.pi / 2],
                    euler_1[1]: [np.pi / 2],
                    euler_1[2]: [np.pi / 2],
                },
            ),
        ]
    )


def test_zip_binding_observables_sum(circuit_rx_parametrized):
    with pytest.raises(TypeError):
        ProgramSet.zip(CircuitBinding(circuit_rx_parametrized, observables=Y(1) + Z(0) @ X(1)))


def test_zip_binding_observables_and_ps_observables(circuit_rx_parametrized):
    with pytest.raises(ValueError):
        ProgramSet.zip(
            CircuitBinding(circuit_rx_parametrized, observables=[X(0), Y(0), Z(0)]),
            observables=[X(0) @ Y(1), Y(0), Z(0) @ X(1)],
        )


def test_zip_binding_observables_no_inputs(circuit_rx_parametrized):
    with pytest.raises(ValueError):
        ProgramSet.zip(
            CircuitBinding(circuit_rx_parametrized, observables=[X(0), Y(0), Z(0)]),
        )


def test_zip_binding_observables_input_sets_mismatch(circuit_rx_parametrized):
    with pytest.raises(ValueError):
        ProgramSet.zip(
            CircuitBinding(circuit_rx_parametrized, observables=[X(0) @ Y(1), Y(0), Z(0) @ X(1)]),
            input_sets=[{"theta": 1.23}, {"theta": 3.21}],
        )


def test_zip_binding_input_sets(circuit_rx_parametrized):
    obs1 = Y(1)
    obs2 = Z(0) @ X(1)
    program_set = ProgramSet.zip(
        CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [1.23, 3.21]}),
        observables=[obs1, obs2],
        shots_per_executable=100,
    )
    assert len(program_set) == 2
    assert program_set.total_executables == 2
    assert program_set.total_shots == 200
    euler_0 = euler_angle_parameter_names(0)
    euler_1 = euler_angle_parameter_names(1)
    assert program_set.to_ir() == IrProgramSet(
        programs=[
            Program(
                source=get_circuit_source(circuit_rx_parametrized.with_euler_angles([obs1])),
                inputs={
                    "theta": [1.23],
                    euler_1[0]: [0],
                    euler_1[1]: [np.pi / 2],
                    euler_1[2]: [np.pi / 2],
                },
            ),
            Program(
                source=get_circuit_source(circuit_rx_parametrized.with_euler_angles([obs2])),
                inputs={
                    "theta": [3.21],
                    euler_0[0]: [0],
                    euler_0[1]: [0],
                    euler_0[2]: [0],
                    euler_1[0]: [np.pi / 2],
                    euler_1[1]: [np.pi / 2],
                    euler_1[2]: [np.pi / 2],
                },
            ),
        ]
    )


def test_zip_binding_input_sets_and_ps_input_sets(circuit_rx_parametrized):
    with pytest.raises(ValueError):
        ProgramSet.zip(
            CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [1.23, 0.12]}),
            input_sets=[{"theta": 1.23}, {"theta": 3.21}],
        )


def test_zip_binding_input_sets_no_observables(circuit_rx_parametrized):
    with pytest.raises(ValueError):
        ProgramSet.zip(CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [1.23, 0.12]}))


def test_zip_binding_input_sets_sum_in_observables(circuit_rx_parametrized):
    with pytest.raises(TypeError):
        ProgramSet.zip(
            CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [1.23, 0.12]}),
            observables=[X(0) @ Y(1) + Y(0), Z(0) @ X(1)],
        )


def test_zip_binding_input_sets_observables_mismatch(circuit_rx_parametrized):
    with pytest.raises(ValueError):
        ProgramSet.zip(
            CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [1.23, 0.12]}),
            observables=[X(0) @ Y(1), Y(0), Z(0) @ X(1)],
        )


def test_zip_circuits_input_sets_observables():
    circ1 = Circuit().rx(0, FreeParameter("theta"))
    circ2 = Circuit().ry(0, FreeParameter("phi"))
    input_sets = [{"theta": 1.23}, {"phi": 3.21}]
    obs1 = Y(1)
    obs2 = Z(0) @ X(1)
    program_set = ProgramSet.zip(
        [circ1, circ2],
        input_sets=input_sets,
        observables=[obs1, obs2],
        shots_per_executable=100,
    )
    assert len(program_set) == 2
    assert program_set.total_executables == 2
    assert program_set.total_shots == 200
    euler_0 = euler_angle_parameter_names(0)
    euler_1 = euler_angle_parameter_names(1)
    assert program_set.to_ir() == IrProgramSet(
        programs=[
            Program(
                source=get_circuit_source(circ1.with_euler_angles([obs1])),
                inputs={
                    "theta": [1.23],
                    euler_1[0]: [0],
                    euler_1[1]: [np.pi / 2],
                    euler_1[2]: [np.pi / 2],
                },
            ),
            Program(
                source=get_circuit_source(circ2.with_euler_angles([obs2])),
                inputs={
                    "phi": [3.21],
                    euler_0[0]: [0],
                    euler_0[1]: [0],
                    euler_0[2]: [0],
                    euler_1[0]: [np.pi / 2],
                    euler_1[1]: [np.pi / 2],
                    euler_1[2]: [np.pi / 2],
                },
            ),
        ]
    )


def test_zip_circuits_input_sets_observables_mismatch():
    with pytest.raises(ValueError):
        ProgramSet.zip(
            [ghz(1), ghz(2)],
            input_sets=[{"theta": 1.23}, {"theta": 3.21}],
            observables=[X(0) @ Y(1), Y(0), Z(0) @ X(1)],
        )
    with pytest.raises(ValueError):
        ProgramSet.zip(
            [ghz(1), ghz(2), ghz(3)],
            input_sets=[{"theta": 1.23}, {"theta": 3.21}],
            observables=[X(0) @ Y(1), Y(0), Z(0) @ X(1)],
        )


def test_zip_circuits_observables():
    circ1 = ghz(2)
    circ2 = ghz(3)
    obs1 = Y(1)
    obs2 = Z(0) @ X(1)
    program_set = ProgramSet.zip(
        [circ1, circ2],
        observables=[obs1, obs2],
        shots_per_executable=100,
    )
    assert len(program_set) == 2
    assert program_set.total_executables == 2
    assert program_set.total_shots == 200
    euler_0 = euler_angle_parameter_names(0)
    euler_1 = euler_angle_parameter_names(1)
    assert program_set.to_ir() == IrProgramSet(
        programs=[
            Program(
                source=get_circuit_source(circ1.with_euler_angles([obs1])),
                inputs={euler_1[0]: [0], euler_1[1]: [np.pi / 2], euler_1[2]: [np.pi / 2]},
            ),
            Program(
                source=get_circuit_source(circ2.with_euler_angles([obs2])),
                inputs={
                    euler_0[0]: [0],
                    euler_0[1]: [0],
                    euler_0[2]: [0],
                    euler_1[0]: [np.pi / 2],
                    euler_1[1]: [np.pi / 2],
                    euler_1[2]: [np.pi / 2],
                },
            ),
        ]
    )


def test_zip_circuits_observables_mismatch():
    with pytest.raises(ValueError):
        ProgramSet.zip([ghz(1), ghz(2)], observables=[X(0) @ Y(1), Y(0), Z(0) @ X(1)])


def test_zip_circuits_input_sets():
    circ1 = Circuit().rx(0, FreeParameter("theta"))
    circ2 = Circuit().ry(0, FreeParameter("phi"))
    input_sets = [{"theta": 1.23}, {"phi": 3.21}]
    program_set = ProgramSet.zip([circ1, circ2], input_sets=input_sets, shots_per_executable=100)
    assert len(program_set) == 2
    assert program_set.total_executables == 2
    assert program_set.total_shots == 200
    assert program_set.to_ir() == IrProgramSet(
        programs=[
            Program(source=get_circuit_source(circ1), inputs={"theta": [1.23]}),
            Program(source=get_circuit_source(circ2), inputs={"phi": [3.21]}),
        ]
    )


def test_zip_circuits_input_sets_mismatch():
    with pytest.raises(ValueError):
        ProgramSet.zip([ghz(1), ghz(2), ghz(3)], input_sets=[{"theta": 1.23}, {"theta": 3.21}])


def test_zip_circuits_only():
    with pytest.raises(ValueError):
        ProgramSet.zip([ghz(1), ghz(2), ghz(3)])


def test_product_observables(circuit_rx_parametrized):
    ghz2 = ghz(2)
    ghz3 = ghz(3)
    observables = [Y(1), Z(0) @ X(1)]
    program_set = ProgramSet.product(
        [ghz2, CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [1.23, 3.21]}), ghz3],
        observables=observables,
        shots_per_executable=100,
    )
    assert len(program_set) == 3
    assert program_set.total_executables == 8
    assert program_set.total_shots == 800
    euler_0 = euler_angle_parameter_names(0)
    euler_1 = euler_angle_parameter_names(1)
    assert program_set.to_ir() == IrProgramSet(
        programs=[
            Program(
                source=get_circuit_source(ghz2.with_euler_angles(observables)),
                inputs={
                    euler_0[0]: [0, 0],
                    euler_0[1]: [0, 0],
                    euler_0[2]: [0, 0],
                    euler_1[0]: [0, np.pi / 2],
                    euler_1[1]: [np.pi / 2, np.pi / 2],
                    euler_1[2]: [np.pi / 2, np.pi / 2],
                },
            ),
            Program(
                source=get_circuit_source(circuit_rx_parametrized.with_euler_angles(observables)),
                inputs={
                    "theta": [1.23, 1.23, 3.21, 3.21],
                    euler_0[0]: [0, 0, 0, 0],
                    euler_0[1]: [0, 0, 0, 0],
                    euler_0[2]: [0, 0, 0, 0],
                    euler_1[0]: [0, np.pi / 2, 0, np.pi / 2],
                    euler_1[1]: [np.pi / 2, np.pi / 2, np.pi / 2, np.pi / 2],
                    euler_1[2]: [np.pi / 2, np.pi / 2, np.pi / 2, np.pi / 2],
                },
            ),
            Program(
                source=get_circuit_source(ghz3.with_euler_angles(observables)),
                inputs={
                    euler_0[0]: [0, 0],
                    euler_0[1]: [0, 0],
                    euler_0[2]: [0, 0],
                    euler_1[0]: [0, np.pi / 2],
                    euler_1[1]: [np.pi / 2, np.pi / 2],
                    euler_1[2]: [np.pi / 2, np.pi / 2],
                },
            ),
        ]
    )


def test_product_sum(circuit_rx_parametrized):
    ghz2 = ghz(2)
    ghz3 = ghz(3)
    observables = 3 * Y(1) - 2 * Z(0) @ X(1)
    program_set = ProgramSet.product(
        [ghz2, CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [1.23, 3.21]}), ghz3],
        observables=observables,
        shots_per_executable=100,
    )
    assert len(program_set) == 3
    assert program_set.total_executables == 8
    assert program_set.total_shots == 800
    euler_0 = euler_angle_parameter_names(0)
    euler_1 = euler_angle_parameter_names(1)
    assert program_set.to_ir() == IrProgramSet(
        programs=[
            Program(
                source=get_circuit_source(ghz2.with_euler_angles(observables)),
                inputs={
                    euler_0[0]: [0, 0],
                    euler_0[1]: [0, 0],
                    euler_0[2]: [0, 0],
                    euler_1[0]: [0, np.pi / 2],
                    euler_1[1]: [np.pi / 2, np.pi / 2],
                    euler_1[2]: [np.pi / 2, np.pi / 2],
                },
            ),
            Program(
                source=get_circuit_source(circuit_rx_parametrized.with_euler_angles(observables)),
                inputs={
                    "theta": [1.23, 1.23, 3.21, 3.21],
                    euler_0[0]: [0, 0, 0, 0],
                    euler_0[1]: [0, 0, 0, 0],
                    euler_0[2]: [0, 0, 0, 0],
                    euler_1[0]: [0, np.pi / 2, 0, np.pi / 2],
                    euler_1[1]: [np.pi / 2, np.pi / 2, np.pi / 2, np.pi / 2],
                    euler_1[2]: [np.pi / 2, np.pi / 2, np.pi / 2, np.pi / 2],
                },
            ),
            Program(
                source=get_circuit_source(ghz3.with_euler_angles(observables)),
                inputs={
                    euler_0[0]: [0, 0],
                    euler_0[1]: [0, 0],
                    euler_0[2]: [0, 0],
                    euler_1[0]: [0, np.pi / 2],
                    euler_1[1]: [np.pi / 2, np.pi / 2],
                    euler_1[2]: [np.pi / 2, np.pi / 2],
                },
            ),
        ]
    )


def test_product_no_observables(circuit_rx_parametrized):
    with pytest.raises(ValueError):
        ProgramSet.product(
            [
                ghz(1),
                CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [1.23, 0.12]}),
                ghz(2),
            ],
            [],
        )


def test_product_binding_observables(circuit_rx_parametrized):
    with pytest.raises(ValueError):
        ProgramSet.product(
            [
                ghz(1),
                CircuitBinding(circuit_rx_parametrized, observables=X(0) @ Y(1) + Y(0) @ Z(1)),
                ghz(2),
            ],
            [X(0) @ Y(1), Y(0) @ Z(1)],
        )


def test_inequality(circuit_rx_parametrized):
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=[{"theta": 1.23}, {"theta": 3.21}])
    program_set = ProgramSet([binding, binding])
    assert program_set != ProgramSet([binding, circuit_rx_parametrized])
    assert program_set != circuit_rx_parametrized
