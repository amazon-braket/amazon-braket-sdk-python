import pytest

from braket.emulators.emulator_passes.criteria import GateConnectivityCriterion
from braket.circuits import Circuit
import networkx as nx
from networkx.utils import graphs_equal
import numpy as np


@pytest.fixture
def basic_4_node_graph():
    G = nx.DiGraph()
    G.add_edges_from(
        [
            (0, 1, {"supported_gates": ["CNot", "CZ"]}), 
            (1, 2, {"supported_gates": ["Swap", "CNot"]}),
            (0, 3, {"supported_gates": ["XX", "XY"]})
        ]
    )
    return G


@pytest.fixture
def basic_discontiguous_4_node_graph():
    G = nx.DiGraph()
    G.add_edges_from(
        [
            (0, 5, {"supported_gates": ["CNot", "CZ"]}), 
            (2, 4, {"supported_gates": ["Swap", "CNot"]}),
            (3, 0, {"supported_gates": ["XX", "XY"]})
        ]
    )
    return G
    
@pytest.fixture
def basic_undirected_4_node_graph_as_dict():
    return {
        (0, 1): ["CNot", "Swap", "CX", "XX"], 
        (1, 2): ["CNot", "CZ", "ISwap", "XY"], 
        (0, 3): ["PSwap", "CNot", "XY"]
    }
    
    
@pytest.mark.parametrize(
    "circuit", 
    [
        Circuit(), 
        Circuit().add_verbatim_box(
            Circuit().cnot(0, 1).h(range(4))
        ), 
        Circuit().add_verbatim_box(
            Circuit().cnot(0, 1).cz(0, 1).swap(1, 2).xx(0, 3, np.pi/2)
        ).add_verbatim_box(
            Circuit().xy(0, 3, np.pi/2).cnot(1, 2).cz(0, 1)
        ),
        Circuit().i(range(10)).cnot(0, 2).yy(8, 9, np.pi/2).h(7).add_verbatim_box(
            Circuit().cnot(0, 1).cz(0, 1)
        ).cnot(0, 2).swap(4, 6)
    ]
)
def test_valid_basic_contiguous_circuits(basic_4_node_graph, circuit):
    """
        ConnectivityGateCriterion should not raise any errors when validating these circuits.
    """
    gate_connectivity_criterion = GateConnectivityCriterion(basic_4_node_graph)
    gate_connectivity_criterion.validate(circuit)
    
    
@pytest.mark.parametrize(
    "circuit", 
    [
        Circuit(), 
        Circuit().add_verbatim_box(
            Circuit().cnot(0, 5)
        ), 
        Circuit().add_verbatim_box(
            Circuit().cnot(2, 4).cz(0, 5).swap(2, 4).xx(3, 0, np.pi/2)
        ).add_verbatim_box(
            Circuit().xy(3, 0, np.pi/2).cnot(2, 4).cz(0, 5)
        ),
        Circuit().i(range(10)).cnot(0, 2).yy(8, 9, np.pi/2).h(7).add_verbatim_box(
            Circuit().cnot(0, 5).swap(2, 4)
        ).cnot(0, 2).swap(4, 6)
    ]
)
def test_valid_basic_discontiguous_circuits(basic_discontiguous_4_node_graph, circuit):
    """
        ConnectivityGateCriterion should not raise any errors when validating these circuits.
    """
    gate_connectivity_criterion = GateConnectivityCriterion(basic_discontiguous_4_node_graph)
    gate_connectivity_criterion.validate(circuit)
    
    
    
def test_directed_graph_construction_from_dict():
    """
        ConnectivityGateCriterion should correctly construct a graph from a dictionary
        representation of the connectivity.
    """
    dict_representation = {
        (0, 1): ["CNot", "CZ"],
        (1, 2): ["Swap", "CNot", "YY"],
        (0, 2): ["XX", "XY", "CNot", "CZ"],
        (2, 5): ["XX", "XY", "CNot", "CZ"]
    }
    digraph_representation = nx.DiGraph()
    digraph_representation.add_edges_from([
        (0, 1, {"supported_gates": ["CNot", "CZ"]}),
        (1, 2, {"supported_gates": ["Swap", "CNot", "YY"]}),
        (0, 2, {"supported_gates": ["XX", "XY", "CNot", "CZ"]}),
        (2, 5, {"supported_gates": ["XX", "XY", "CNot", "CZ"]})
    ])
    gcc = GateConnectivityCriterion(dict_representation, directed=True)
    assert graphs_equal(gcc._gate_connectivity_graph, digraph_representation)
    
    
    
@pytest.mark.parametrize(
    "circuit", 
    [
        Circuit(),
        Circuit().add_verbatim_box(
            Circuit().cnot(0, 1).cnot(1, 0)
        ), 
        Circuit().swap(0, 1).add_verbatim_box(
            Circuit().iswap(2, 1).pswap(3, 0, np.pi/2).pswap(0, 3, np.pi/2)
        ), 
        Circuit().cnot(2, 3).h(5).pswap(0, 6, np.pi/2).add_verbatim_box(
            Circuit().xy(2, 1, np.pi/2).cnot(0, 1).cnot(1, 0)
        ).add_verbatim_box(
            Circuit().cnot(0, 3).cnot(3, 0).xy(0, 3, np.pi/2)
        )
    ]
)    
def test_undirected_criteria_with_valid_circuits(basic_undirected_4_node_graph_as_dict, circuit):
    """
        ConnectivityGateCriterion should not raise any errors when validating these circuits.
    """
    gate_connectivity_criterion = GateConnectivityCriterion(basic_undirected_4_node_graph_as_dict, directed=False)
    gate_connectivity_criterion.validate(circuit)


    
def test_undirected_graph_construction_from_dict():
    """
        ConnectivityGateCriterion should correctly construct an undirected graph from a dictionary
        representation of the connectivity.
    """
    dict_representation = {
        (0, 1): ["CNot", "CZ"],
        (1, 2): ["Swap", "CNot", "YY"],
        (0, 2): ["XX", "XY", "CNot", "CZ"],
        (2, 5): ["XX", "XY", "CNot", "CZ"]
    }
    digraph_representation = nx.DiGraph()
    digraph_representation.add_edges_from([
        (0, 1, {"supported_gates": ["CNot", "CZ"]}),
        (1, 2, {"supported_gates": ["Swap", "CNot", "YY"]}),
        (0, 2, {"supported_gates": ["XX", "XY", "CNot", "CZ"]}),
        (2, 5, {"supported_gates": ["XX", "XY", "CNot", "CZ"]}), 
        (1, 0, {"supported_gates": ["CNot", "CZ"]}),
        (2, 1, {"supported_gates": ["Swap", "CNot", "YY"]}),
        (2, 0, {"supported_gates": ["XX", "XY", "CNot", "CZ"]}),
        (5, 2, {"supported_gates": ["XX", "XY", "CNot", "CZ"]}), 
    ])
    gcc = GateConnectivityCriterion(dict_representation)
    assert graphs_equal(gcc._gate_connectivity_graph, digraph_representation)
    


    # G.add_edges_from(
    #     [
    #         (0, 1, {"supported_gates": ["CNot", "CZ"]}), 
    #         (1, 2, {"supported_gates": ["Swap", "CNot"]}),
    #         (0, 3, {"supported_gates": ["XX", "XY"]})
    #     ]
    # )
@pytest.mark.parametrize(
    "circuit", 
    [
        Circuit().add_verbatim_box(
            Circuit().cnot(1, 0)
        ),
        Circuit().add_verbatim_box(
            Circuit().h(4)
        ), 
        Circuit().add_verbatim_box(
            Circuit().swap(1, 2).xx(0, 3, np.pi/2).iswap(0, 1)
        ), 
        Circuit().add_verbatim_box(
            Circuit().cnot(0, 3)
        )
    ]
)
def test_invalid_circuits(basic_4_node_graph, circuit): 
    with pytest.raises(ValueError):
        gate_connectivity_criterion = GateConnectivityCriterion(basic_4_node_graph)
        gate_connectivity_criterion.validate(circuit)