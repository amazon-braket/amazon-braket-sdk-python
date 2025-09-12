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

from braket.circuits import Circuit, Gate, Instruction
from braket.circuits.compiler_directives import EndVerbatimBox, StartVerbatimBox
from braket.circuits.noises import BitFlip
from braket.emulation.passes.circuit_passes import GateConnectivityValidator


@pytest.fixture
def basic_4_node_graph():
    G = nx.DiGraph()
    G.add_edges_from([
        (0, 1, {"supported_gates": ["CNot", "CZ"]}),
        (1, 2, {"supported_gates": ["Swap", "CNot"]}),
        (0, 3, {"supported_gates": ["XX", "XY"]}),
    ])
    return G


@pytest.fixture
def basic_discontiguous_4_node_graph():
    G = nx.DiGraph()
    G.add_edges_from([
        (0, 5, {"supported_gates": ["CNot", "CZ"]}),
        (2, 4, {"supported_gates": ["Swap", "CNot"]}),
        (3, 0, {"supported_gates": ["XX", "XY"]}),
    ])
    return G


@pytest.fixture
def basic_4_node_graph_as_dict():
    return {
        (0, 1): ["CNot", "Swap", "CX", "XX"],
        (1, 2): ["CNot", "CZ", "ISwap", "XY"],
        (0, 3): ["PSwap", "CNot", "XY"],
    }


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit(),
        Circuit().add_verbatim_box(Circuit().cnot(0, 1).h(range(4))),
        Circuit()
        .add_verbatim_box(Circuit().cnot(0, 1).cz(0, 1).swap(1, 2).xx(0, 3, np.pi / 2))
        .add_verbatim_box(Circuit().xy(0, 3, np.pi / 2).cnot(1, 2).cz(0, 1)),
        Circuit()
        .i(range(10))
        .cnot(0, 2)
        .yy(8, 9, np.pi / 2)
        .h(7)
        .add_verbatim_box(Circuit().cnot(0, 1).cz(0, 1))
        .cnot(0, 2)
        .swap(4, 6),
        Circuit().add_verbatim_box(
            Circuit().h(0).apply_gate_noise(BitFlip(0.1), target_gates=Gate.H)
        ),
    ],
)
def test_valid_basic_contiguous_circuits(basic_4_node_graph, circuit):
    """
    GateConnectivityValidator should not raise any errors when validating these circuits.
    """
    gate_connectivity_validator = GateConnectivityValidator(basic_4_node_graph)
    gate_connectivity_validator.validate(circuit)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit(),
        Circuit().add_verbatim_box(Circuit().cnot(0, 5)),
        Circuit()
        .add_verbatim_box(Circuit().cnot(2, 4).cz(0, 5).swap(2, 4).xx(3, 0, np.pi / 2))
        .add_verbatim_box(Circuit().xy(3, 0, np.pi / 2).cnot(2, 4).cz(0, 5)),
        Circuit()
        .i(range(10))
        .cnot(0, 2)
        .yy(8, 9, np.pi / 2)
        .h(7)
        .add_verbatim_box(Circuit().cnot(0, 5).swap(2, 4))
        .cnot(0, 2)
        .swap(4, 6),
    ],
)
def test_valid_basic_discontiguous_circuits(basic_discontiguous_4_node_graph, circuit):
    """
    GateConnectivityValidator should not raise any errors when validating these circuits.
    """
    gate_connectivity_validator = GateConnectivityValidator(basic_discontiguous_4_node_graph)
    gate_connectivity_validator.validate(circuit)


def test_directed_graph_construction_from_dict():
    """
    GateConnectivityValidator should correctly construct a graph from a dictionary
    representation of the connectivity.
    """
    dict_representation = {
        (0, 1): ["CNot", "CZ"],
        (1, 2): ["Swap", "CNot", "YY"],
        (0, 2): ["XX", "XY", "CNot", "CZ"],
        (2, 5): ["XX", "XY", "CNot", "CZ"],
    }
    digraph_representation = nx.DiGraph()
    digraph_representation.add_edges_from([
        (0, 1, {"supported_gates": ["CNot", "CZ"]}),
        (1, 2, {"supported_gates": ["Swap", "CNot", "YY"]}),
        (0, 2, {"supported_gates": ["XX", "XY", "CNot", "CZ"]}),
        (2, 5, {"supported_gates": ["XX", "XY", "CNot", "CZ"]}),
    ])
    gcc = GateConnectivityValidator(dict_representation)
    assert graphs_equal(gcc._gate_connectivity_graph, digraph_representation)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit(),
        Circuit().add_verbatim_box(Circuit().cnot(0, 1)),
        Circuit()
        .swap(0, 1)
        .add_verbatim_box(Circuit().iswap(2, 1).pswap(3, 0, np.pi / 2).pswap(0, 3, np.pi / 2)),
        Circuit()
        .cnot(2, 3)
        .h(5)
        .pswap(0, 6, np.pi / 2)
        .add_verbatim_box(Circuit().xy(2, 1, np.pi / 2).cnot(0, 1).cnot(1, 0))
        .add_verbatim_box(Circuit().cnot(0, 3).cnot(3, 0).xy(0, 3, np.pi / 2)),
    ],
)
def test_undirected_criteria_from_dict_with_valid_circuits(basic_4_node_graph_as_dict, circuit):
    """
    GateConnectivityValidator should not raise any errors when validating these circuits.
    """
    gate_connectivity_validator = GateConnectivityValidator(
        basic_4_node_graph_as_dict, directed=False
    )
    gate_connectivity_validator.validate(circuit)


def test_undirected_graph_construction_from_dict():
    """
    GateConnectivityValidator should correctly construct an undirected graph from a dictionary
    representation of the connectivity.
    """
    dict_representation = {
        (0, 1): ["CNot", "CZ"],
        (1, 0): ["CNot", "CZ"],
        (1, 2): ["Swap", "CNot", "YY"],
        (0, 2): ["XX", "XY", "CNot", "CZ"],
        (2, 5): ["XX", "XY", "CNot", "CZ"],
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
    gcc = GateConnectivityValidator(dict_representation, directed=False)
    assert graphs_equal(gcc._gate_connectivity_graph, digraph_representation)


@pytest.mark.parametrize(
    "representation",
    [
        {(0, 1): ["CNot", "CZ"], (1, 0): ["CZ, XX"], (2, 0): ["CNot, YY"]},
        nx.from_dict_of_dicts({
            0: {1: {"supported_gates": ["CNot", "CZ"]}},
            1: {0: {"supported_gates": ["CZ", "XX"]}},
            2: {2: {"supported_gates": ["CNot", "YY"]}},
        }),
    ],
)
def create_undirected_graph_with_exisiting_back_edges(representation):
    """
    Check that creating an undirected graph with a graph that
    contains forwards and backwards edges with different constraints
    is created properly.
    """

    gcc = GateConnectivityValidator(representation, directed=False)
    expected_digraph_representation = nx.DiGraph()
    expected_digraph_representation.add_edges_from([
        (0, 1, {"supported_gates": ["CNot", "CZ"]}),
        (1, 0, {"supported_gates": ["CZ", "XX"]}),
        (2, 0, {"supported_gates": ["CNot", "YY"]}),
        (0, 2, {"supported_gates": ["CNot", "YY"]}),
    ])

    assert graphs_equal(gcc._gate_connectivity_graph, expected_digraph_representation)


@pytest.mark.parametrize(
    "circuit",
    [
        Circuit().add_verbatim_box(Circuit().cnot(1, 0)),
        Circuit().add_verbatim_box(Circuit().h(4)),
        Circuit().add_verbatim_box(Circuit().swap(1, 2).xx(0, 3, np.pi / 2).iswap(0, 1)),
        Circuit().add_verbatim_box(Circuit().cnot(0, 3)),
        Circuit().add_instruction(Instruction(StartVerbatimBox())),
        Circuit()
        .add_instruction(Instruction(StartVerbatimBox()))
        .add_instruction(Instruction(StartVerbatimBox())),
        Circuit().add_instruction(Instruction(EndVerbatimBox())),
    ],
)
def test_invalid_circuits(basic_4_node_graph, circuit):
    with pytest.raises(ValueError):
        gate_connectivity_validator = GateConnectivityValidator(basic_4_node_graph)
        gate_connectivity_validator.validate(circuit)


def test_invalid_connectivity_graph():
    bad_graph = nx.complete_graph(5, create_using=nx.Graph())
    with pytest.raises(TypeError):
        GateConnectivityValidator(bad_graph)


@pytest.mark.parametrize(
    "gate_name,controls,targets,is_valid",
    [
        ("CZ", [0], [1], True),
        ("CNot", [], [0, 1], True),
        ("XY", [3], [0], True),
        ("CZ", [0, 2], [], False),
        ("Swap", [0], [1, 2], False),
        ("ZZ", [3], [0], False),
    ],
)
def test_validate_instruction_method(gate_name, controls, targets, is_valid, basic_4_node_graph):
    gcc = GateConnectivityValidator(basic_4_node_graph, directed=False)
    if is_valid:
        gcc._validate_instruction_connectivity(gate_name, controls, targets)
    else:
        with pytest.raises(ValueError):
            gcc._validate_instruction_connectivity(gate_name, controls, targets)


@pytest.mark.parametrize(
    "graph",
    [
        (
            nx.from_dict_of_dicts(
                {
                    0: {1: {"supported_gates": ["cnot", "cz"]}},
                    1: {0: {"supported_gates": ["cz", "cnot", "xx"]}},
                },
                create_using=nx.DiGraph(),
            )
        ),
        ({(0, 1): ["cnot", "cz"], (1, 0): ["cz", "cnot", "xx"]}),
        ({(0, 1): ["xx", "yy"], (1, 0): ["yy", "xx"]}),
    ],
)
def test_invalid_undirected_graph(graph):
    with pytest.raises(ValueError):
        GateConnectivityValidator(graph, directed=False)
