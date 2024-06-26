import networkx as nx
import numpy as np
import pytest
from networkx.utils import graphs_equal

from braket.circuits import Circuit
from braket.emulators.emulator_passes.criteria import ConnectivityCriterion


@pytest.fixture
def basic_2_node_complete_graph():
    return nx.complete_graph(2, create_using=nx.DiGraph())


@pytest.fixture
def basic_noncontig_qubits_2_node_complete_graph():
    return nx.complete_graph([1, 10], create_using=nx.DiGraph())


@pytest.fixture
def five_node_digraph():
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
    ConnectivityGateCriterion should not raise any errors when validating these circuits.
    """
    ConnectivityCriterion(basic_2_node_complete_graph).validate(circuit)


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
    ConnectivityGateCriterion should not raise any errors when validating these circuits.
    """
    ConnectivityCriterion(basic_noncontig_qubits_2_node_complete_graph).validate(circuit)


def test_complete_graph_instantation_with_num_qubits():
    """
    Tests that, if fully_connected is True and num_qubits are passed into the
    ConnectivityCriterion constructor, a fully connected graph is created.
    """
    num_qubits = 5
    criterion = ConnectivityCriterion(num_qubits=num_qubits, fully_connected=True)
    vb = Circuit()
    for i in range(num_qubits):
        for j in range(num_qubits):
            if i != j:
                vb.cnot(i, j)
            else:
                vb.i(i)
    circuit = Circuit().add_verbatim_box(vb)
    criterion.validate(circuit)
    assert nx.utils.graphs_equal(
        criterion._connectivity_graph, nx.complete_graph(num_qubits, create_using=nx.DiGraph())
    )


def test_complete_graph_instantation_with_qubit_labels():
    """
    Tests that, if fully_connected is True and num_qubits are passed into the
    ConnectivityCriterion constructor, a fully connected graph is created.
    """
    qubit_labels = [0, 1, 10, 11, 110, 111, 112, 113]
    criterion = ConnectivityCriterion(qubit_labels=qubit_labels, fully_connected=True)
    vb = Circuit()
    for i in qubit_labels:
        for j in qubit_labels:
            if i != j:
                vb.cnot(i, j)
            else:
                vb.i(i)
    circuit = Circuit().add_verbatim_box(vb)
    criterion.validate(circuit)
    assert nx.utils.graphs_equal(
        criterion._connectivity_graph, nx.complete_graph(qubit_labels, create_using=nx.DiGraph())
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
def test_invalid_2_qubit_gates(five_node_digraph, circuit):
    with pytest.raises(ValueError):
        ConnectivityCriterion(five_node_digraph).validate(circuit)


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
def test_invalid_1_qubit_gates(five_node_digraph, circuit):
    with pytest.raises(ValueError):
        ConnectivityCriterion(five_node_digraph).validate(circuit)


def test_equality_graph_created_with_dict(five_node_digraph):
    graph = {0: [1, 3], 1: [0, 2, 10], 2: [1, 3, 11], 10: [1, 11], 11: [2, 10]}
    criteria_from_digraph = ConnectivityCriterion(five_node_digraph)
    criteria_from_dict = ConnectivityCriterion(graph)
    assert criteria_from_dict == criteria_from_digraph


@pytest.mark.parametrize(
    "connectivity_graph, fully_connected, num_qubits, qubit_labels",
    [(None, True, None, None), (nx.DiGraph(), True, None, None), (None, True, 5, [0, 1])],
)
def test_invalid_constructors(connectivity_graph, fully_connected, num_qubits, qubit_labels):
    with pytest.raises(ValueError):
        ConnectivityCriterion(connectivity_graph, fully_connected, num_qubits, qubit_labels)


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
    cc = ConnectivityCriterion(representation, directed=False)
    assert graphs_equal(cc._connectivity_graph, expected_digraph)
