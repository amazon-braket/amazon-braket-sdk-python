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


def test_split_already_fits(circuit_rx_parametrized):
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=[{"theta": 1.23}, {"theta": 3.21}])
    program_set = ProgramSet(binding)
    subs, mapping = program_set.split(10)
    assert subs == [program_set]
    assert subs[0] is program_set
    assert mapping == [[0, 1]]


def test_split_exact_fit(circuit_rx_parametrized):
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=[{"theta": 1.23}, {"theta": 3.21}])
    program_set = ProgramSet(binding)
    subs, mapping = program_set.split(2)
    assert subs == [program_set]
    assert subs[0] is program_set
    assert mapping == [[0, 1]]


def test_split_plain_circuits():
    circs = [ghz(1), ghz(2), ghz(3), ghz(1), ghz(2)]
    program_set = ProgramSet(circs, shots_per_executable=10)
    subs, mapping = program_set.split(2)
    assert [s.total_executables for s in subs] == [2, 2, 1]
    assert subs[0].entries == circs[0:2]
    assert subs[1].entries == circs[2:4]
    assert subs[2].entries == circs[4:5]
    assert mapping == [[0, 1], [2, 3], [4]]


def test_split_single_binding_packed(circuit_rx_parametrized):
    inputs = {"theta": [float(i) for i in range(10)]}
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=inputs)
    program_set = ProgramSet(binding)
    subs, mapping = program_set.split(3)
    assert [s.total_executables for s in subs] == [3, 3, 3, 1]
    # Each sub-program-set is a single coalesced binding over a contiguous slice.
    for s in subs:
        assert len(s) == 1
        assert s.entries[0].circuit == circuit_rx_parametrized
        assert s.entries[0].observables is None
    thetas = []
    for s in subs:
        thetas.extend(s.entries[0].input_sets.as_dict()["theta"])
    assert thetas == inputs["theta"]
    assert mapping == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


def test_split_with_observables(circuit_rx_parametrized):
    # 5 parameter-set indices, 4 observables => 5 classes of size 4.
    inputs = {"theta": [float(i) for i in range(5)]}
    observables = [X(0), Y(0), Z(0), X(0) @ Y(1)]
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=inputs, observables=observables)
    program_set = ProgramSet(binding)
    subs, mapping = program_set.split(8)
    assert [s.total_executables for s in subs] == [8, 8, 4]
    # Observables propagate unchanged (never split across sub-program-sets).
    for s in subs:
        assert s.entries[0].observables == observables
    assert sum(mapping, []) == list(range(20))


def test_split_with_sum_hamiltonian(circuit_rx_parametrized):
    # Sum with 3 summands => class size = 3 per parameter-set index.
    inputs = {"theta": [float(i) for i in range(4)]}
    hamiltonian = 1.0 * X(0) + 2.0 * Y(0) + 3.0 * Z(0)
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=inputs, observables=hamiltonian)
    program_set = ProgramSet(binding)
    subs, mapping = program_set.split(6)
    assert [s.total_executables for s in subs] == [6, 6]
    # Sum preserved intact (no observable-splitting needed at max=6).
    for s in subs:
        assert s.entries[0].observables is hamiltonian
    assert sum(mapping, []) == list(range(12))


def test_split_worked_example(circuit_rx_parametrized):
    # Two bindings: c1 with 100 param sets × 4 obs, c2 with 50 param sets × 2 obs.
    c1 = circuit_rx_parametrized
    c2 = Circuit().rx(0, FreeParameter("phi"))
    obs1 = [X(0), Y(0), Z(0), X(0) @ Y(1)]
    obs2 = [X(0), Z(0)]
    binding1 = CircuitBinding(c1, {"theta": [float(i) for i in range(100)]}, obs1)
    binding2 = CircuitBinding(c2, {"phi": [float(i) for i in range(50)]}, obs2)
    program_set = ProgramSet([binding1, binding2])

    subs, mapping = program_set.split(120)
    # Greedy packing fills each bucket up to the budget before flushing.
    assert [s.total_executables for s in subs] == [120, 120, 120, 120, 20]
    assert sum(s.total_executables for s in subs) == program_set.total_executables
    # First three buckets are pure c1 (30 × 4 each).
    for i in range(3):
        assert len(subs[i]) == 1
        assert subs[i].entries[0].circuit == c1
        assert len(subs[i].entries[0].input_sets) == 30
    # Bucket 3 straddles both bindings (10 × 4 + 40 × 2 = 120); coalesced per binding.
    assert len(subs[3]) == 2
    assert subs[3].entries[0].circuit == c1
    assert len(subs[3].entries[0].input_sets) == 10
    assert subs[3].entries[1].circuit == c2
    assert len(subs[3].entries[1].input_sets) == 40
    # Last bucket is pure c2 remainder (10 × 2 = 20).
    assert len(subs[4]) == 1
    assert subs[4].entries[0].circuit == c2
    assert len(subs[4].entries[0].input_sets) == 10
    # Mapping covers every original executable exactly once, in order.
    assert sum(mapping, []) == list(range(500))


def test_split_preserves_shots(circuit_rx_parametrized):
    inputs = {"theta": [float(i) for i in range(5)]}
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=inputs)
    program_set = ProgramSet(binding, shots_per_executable=100)
    subs, _ = program_set.split(2)
    assert all(s.shots_per_executable == 100 for s in subs)
    assert sum(s.total_shots for s in subs) == program_set.total_shots


def test_split_coalesces_adjacent_same_binding(circuit_rx_parametrized):
    # 6 parameter-set indices, class size 1, max_executables=4 => buckets of 4, 2.
    # Each bucket should contain one coalesced multi-parameter-set binding,
    # not four (resp. two) separate single-parameter-set bindings.
    inputs = {"theta": [float(i) for i in range(6)]}
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=inputs)
    program_set = ProgramSet(binding)
    subs, _ = program_set.split(4)
    assert [len(s) for s in subs] == [1, 1]
    assert len(subs[0].entries[0].input_sets) == 4
    assert len(subs[1].entries[0].input_sets) == 2


def test_split_binding_without_input_sets(circuit_rx_parametrized):
    # A binding with only observables is a single class of size len(observables).
    c1 = circuit_rx_parametrized
    c2 = Circuit().rx(0, FreeParameter("phi"))
    binding_a = CircuitBinding(c1, observables=[X(0), Y(0)])  # size 2
    binding_b = CircuitBinding(c2, observables=[X(0), Y(0), Z(0)])  # size 3
    program_set = ProgramSet([binding_a, binding_b])
    subs, mapping = program_set.split(3)
    assert [s.total_executables for s in subs] == [2, 3]
    assert subs[0].entries == [binding_a]
    assert subs[1].entries == [binding_b]
    assert mapping == [[0, 1], [2, 3, 4]]


def test_split_non_positive_raises(circuit_rx_parametrized):
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=[{"theta": 1.23}])
    program_set = ProgramSet(binding)
    with pytest.raises(ValueError, match="must be positive"):
        program_set.split(0)
    with pytest.raises(ValueError, match="must be positive"):
        program_set.split(-3)


def test_split_oversize_list_observables_are_chunked(circuit_rx_parametrized):
    # A single class of 10 observables with max_executables=3 becomes 4 sub-program-sets
    # of sizes 3, 3, 3, 1, each with a sliced observable list.
    observables = [X(0), Y(0), Z(0), X(0), Y(0), Z(0), X(0), Y(0), Z(0), X(0)]
    binding = CircuitBinding(circuit_rx_parametrized, observables=observables)
    program_set = ProgramSet(binding)
    subs, mapping = program_set.split(3)
    assert [s.total_executables for s in subs] == [3, 3, 3, 1]
    assert mapping == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    slices = [list(s.entries[0].observables) for s in subs]
    assert slices == [observables[0:3], observables[3:6], observables[6:9], observables[9:10]]


def test_split_oversize_sum_hamiltonian_is_chunked(circuit_rx_parametrized):
    # Sum with 7 summands, max_executables=3 → sub-Sums of sizes 3, 3, 1 with
    # coefficients preserved on each summand.
    ham = 1.0 * X(0) + 2.0 * Y(0) + 3.0 * Z(0) + 4.0 * X(0) + 5.0 * Y(0) + 6.0 * Z(0) + 7.0 * X(0)
    binding = CircuitBinding(circuit_rx_parametrized, observables=ham)
    program_set = ProgramSet(binding)
    subs, mapping = program_set.split(3)
    assert [s.total_executables for s in subs] == [3, 3, 1]
    assert mapping == [[0, 1, 2], [3, 4, 5], [6]]
    # Each sub-observable is a Sum whose summands come from the original in order.
    expected_summands = list(ham.summands)
    got_summands: list = []
    for s in subs:
        sub_obs = s.entries[0].observables
        assert isinstance(sub_obs, type(ham))
        got_summands.extend(sub_obs.summands)
    assert got_summands == expected_summands


def test_split_oversize_observables_with_multiple_param_sets(circuit_rx_parametrized):
    # 2 parameter sets x 5 observables, max_executables=3 ⇒ each parameter-set index
    # splits into two observable windows ((0,3) size 3 and (3,5) size 2). The packer
    # can't coalesce across parameter sets because they're interleaved by window, so we
    # end up with 4 sub-program-sets.
    inputs = {"theta": [1.0, 2.0]}
    observables = [X(0), Y(0), Z(0), X(0), Y(0)]
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=inputs, observables=observables)
    program_set = ProgramSet(binding)
    subs, mapping = program_set.split(3)
    assert [s.total_executables for s in subs] == [3, 2, 3, 2]
    # Mapping follows canonical ordering: ps=0,obs=0..4 = indices 0..4; ps=1,obs=0..4 = 5..9.
    assert mapping == [[0, 1, 2], [3, 4], [5, 6, 7], [8, 9]]
    assert sum(mapping, []) == list(range(program_set.total_executables))


def test_split_sub_program_sets_are_serializable(circuit_rx_parametrized):
    inputs = {"theta": [float(i) for i in range(10)]}
    observables = [X(0), Y(0)]
    binding = CircuitBinding(circuit_rx_parametrized, input_sets=inputs, observables=observables)
    program_set = ProgramSet(binding)
    subs, _ = program_set.split(6)
    # Each sub-program set is a fully formed ProgramSet: to_ir() works and returns a
    # single-program IR (one coalesced CircuitBinding per sub-program set here).
    for s in subs:
        ir = s.to_ir()
        assert len(ir.programs) == len(s)


def test_enumerate_executables_plain_circuits():
    ps = ProgramSet([ghz(1), ghz(2), ghz(3)])
    assert list(ps.enumerate_executables()) == [(0, 0, 0), (1, 0, 0), (2, 0, 0)]


def test_enumerate_executables_binding_with_input_sets_only(circuit_rx_parametrized):
    binding = CircuitBinding(circuit_rx_parametrized, input_sets={"theta": [0.1, 0.2, 0.3]})
    ps = ProgramSet(binding)
    assert list(ps.enumerate_executables()) == [(0, 0, 0), (0, 1, 0), (0, 2, 0)]


def test_enumerate_executables_binding_with_observables_only(circuit_rx_parametrized):
    binding = CircuitBinding(circuit_rx_parametrized, observables=[X(0), Y(0), Z(0)])
    ps = ProgramSet(binding)
    assert list(ps.enumerate_executables()) == [(0, 0, 0), (0, 0, 1), (0, 0, 2)]


def test_enumerate_executables_mixed():
    # circuit, binding with 2 ps x 3 obs, binding with 2 ps no obs, binding with 4 obs no ps.
    c0 = ghz(1)
    c1 = Circuit().rx(0, FreeParameter("t")).cnot(0, 1)
    c2 = Circuit().rx(0, FreeParameter("p"))
    c3 = Circuit().h(0)
    b1 = CircuitBinding(c1, {"t": [0.1, 0.2]}, [X(0), Y(0), Z(0)])
    b2 = CircuitBinding(c2, {"p": [0.3, 0.4]})
    b3 = CircuitBinding(c3, observables=[X(0), Y(0), Z(0), X(0) @ Y(1)])
    ps = ProgramSet([c0, b1, b2, b3])
    expected = [
        (0, 0, 0),
        (1, 0, 0),
        (1, 0, 1),
        (1, 0, 2),
        (1, 1, 0),
        (1, 1, 1),
        (1, 1, 2),
        (2, 0, 0),
        (2, 1, 0),
        (3, 0, 0),
        (3, 0, 1),
        (3, 0, 2),
        (3, 0, 3),
    ]
    assert list(ps.enumerate_executables()) == expected
    assert len(expected) == ps.total_executables
