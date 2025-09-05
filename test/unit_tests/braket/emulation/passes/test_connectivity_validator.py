# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import networkx as nx
import numpy as np
import pytest
from networkx.utils import graphs_equal

from braket.circuits import Circuit
from braket.emulation.passes.circuit_passes import ConnectivityValidator


@pytest.fixture
def basic_2_node_complete_graph():
    return nx.complete_graph(2, create_using=nx.DiGraph())


@pytest.fixture
def basic_noncontig_qubits_2_node_complete_graph():
    return nx.complete_graph([1, 10], create_using=nx.DiGraph())


@pytest.fixture
def six_node_digraph():
    edge_set = {0: [1, 3], 1: [0, 2, 10], 2: [1, 3, 11], 10: [1, 11], 11: [2, 10]}
    return nx.from_dict_of_lists(edge_set, create_using=nx.DiGraph())


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit(),
        Circuit().add_verbatim_box(Circuit()),
        Circuit().i(range(2)).cnot(3, 4),
        Circuit().add_verbatim_box(Circuit().h(0).h(1).cnot(0, 1).cnot(1, 0)),
        Circuit()
        .h(range(2))
        .add_verbatim_box(
            Circuit().swap(0, 1).phaseshift(1, np.pi / 4).cphaseshift01(1, 0, np.pi / 4)
        ),
    ],
)
def test_basic_contiguous_circuits(basic_2_node_complete_graph, circuit):
    """
    ConnectivityValidator should not raise any errors when validating these circuits.
    """
    ConnectivityValidator(basic_2_node_complete_graph).validate(circuit)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit(),
        Circuit().add_verbatim_box(Circuit()),
        Circuit().i(range(3)).cnot(3, 4).x(111),
        Circuit().add_verbatim_box(Circuit().h(1).h(10).cnot(1, 10).cnot(10, 1)),
        Circuit().add_verbatim_box(
            Circuit().swap(1, 10).phaseshift(10, np.pi / 4).cphaseshift01(10, 1, np.pi / 4)
        ),
    ],
)
def test_valid_discontiguous_circuits(basic_noncontig_qubits_2_node_complete_graph, circuit):
    """
    ConnectivityValidator should not raise any errors when validating these circuits.
    """
    ConnectivityValidator(basic_noncontig_qubits_2_node_complete_graph).validate(circuit)


def test_complete_graph_instantation_with_num_qubits():
    """
    Tests that, if fully_connected is True and num_qubits are passed into the
    ConnectivityValidator constructor, a fully connected graph is created.
    """
    num_qubits = 5
    validator = ConnectivityValidator(num_qubits=num_qubits, fully_connected=True)
    vb = Circuit()
    for i in range(num_qubits):
        for j in range(num_qubits):
            if i != j:
                vb.cnot(i, j)
            else:
                vb.i(i)
    circuit = Circuit().add_verbatim_box(vb)
    validator.validate(circuit)
    assert nx.utils.graphs_equal(
        validator._connectivity_graph, nx.complete_graph(num_qubits, create_using=nx.DiGraph())
    )


def test_complete_graph_instantation_with_qubit_labels():
    """
    Tests that, if fully_connected is True and num_qubits are passed into the
    ConnectivityValidator constructor, a fully connected graph is created.
    """
    qubit_labels = [0, 1, 10, 11, 110, 111, 112, 113]
    validator = ConnectivityValidator(qubit_labels=qubit_labels, fully_connected=True)
    vb = Circuit()
    for i in qubit_labels:
        for j in qubit_labels:
            if i != j:
                vb.cnot(i, j)
            else:
                vb.i(i)
    circuit = Circuit().add_verbatim_box(vb)
    validator.validate(circuit)
    assert nx.utils.graphs_equal(
        validator._connectivity_graph, nx.complete_graph(qubit_labels, create_using=nx.DiGraph())
    )


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit().add_verbatim_box(Circuit().cnot(0, 2)),
        Circuit().add_verbatim_box(Circuit().swap(1, 3)),
        Circuit()
        .add_verbatim_box(Circuit().cnot(1, 10).cphaseshift01(2, 11, np.pi / 4))
        .x(4)
        .add_verbatim_box(Circuit().swap(2, 10)),
    ],
)
def test_invalid_2_qubit_gates(six_node_digraph, circuit):
    with pytest.raises(ValueError):
        ConnectivityValidator(six_node_digraph).validate(circuit)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit().x(4).add_verbatim_box(Circuit().x(4)),
        Circuit().x(110).add_verbatim_box(Circuit().phaseshift(4, np.pi / 4)),
        Circuit()
        .add_verbatim_box(Circuit().cnot(1, 10).cphaseshift01(2, 11, np.pi / 4))
        .x(4)
        .add_verbatim_box(Circuit().h(111)),
    ],
)
def test_invalid_1_qubit_gates(six_node_digraph, circuit):
    with pytest.raises(ValueError):
        ConnectivityValidator(six_node_digraph).validate(circuit)


@pytest.mark.parametrize(
    "connectivity_graph, fully_connected, num_qubits, qubit_labels, directed",
    [
        (None, True, None, None, False),
        (nx.DiGraph(), True, None, None, False),
        (None, True, 5, [0, 1], False),
        (None, False, None, None, False),
        (nx.from_edgelist([(0, 1)], create_using=nx.Graph()), False, None, None, False),
    ],
)
def test_invalid_constructors(
    connectivity_graph, fully_connected, num_qubits, qubit_labels, directed
):
    with pytest.raises(ValueError):
        ConnectivityValidator(
            connectivity_graph, fully_connected, num_qubits, qubit_labels, directed
        )


@pytest.mark.parametrize(
    "representation",
    [
        {1: [0, 2, 3], 2: [3, 4], 3: [6]},
        nx.from_edgelist([(1, 0), (1, 2), (1, 3), (2, 3), (2, 4), (3, 6)], create_using=nx.DiGraph),
    ],
)
def test_undirected_graph_construction(representation):
    expected_digraph = nx.from_edgelist(
        [
            (1, 0),
            (0, 1),
            (1, 2),
            (2, 1),
            (1, 3),
            (3, 1),
            (2, 3),
            (3, 2),
            (2, 4),
            (4, 2),
            (3, 6),
            (6, 3),
        ],
        create_using=nx.DiGraph,
    )
    cc = ConnectivityValidator(representation, directed=False)
    assert graphs_equal(cc._connectivity_graph, expected_digraph)


# @pytest.fixture
# def six_node_digraph():
#     edge_set = {0: [1, 3], 1: [0, 2, 10], 2: [1, 3, 11], 10: [1, 11], 11: [2, 10]}
#     return nx.from_dict_of_lists(edge_set, create_using=nx.DiGraph())


@pytest.mark.parametrize(
    "controls,targets,is_valid",
    [
        ([0], [1], True),
        ([], [0, 1], True),
        ([3], [0], True),
        ([0, 2], [], False),
        ([0], [1, 2], False),
    ],
)
def test_validate_instruction_method(controls, targets, is_valid, six_node_digraph):
    gcc = ConnectivityValidator(six_node_digraph, directed=False)
    if is_valid:
        gcc._validate_instruction_connectivity(controls, targets)
    else:
        with pytest.raises(ValueError):
            gcc._validate_instruction_connectivity(controls, targets)
