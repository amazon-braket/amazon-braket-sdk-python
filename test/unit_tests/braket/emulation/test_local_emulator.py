import json
from unittest.mock import Mock, patch

import networkx as nx
import pytest

from braket.device_schema import DeviceCapabilities, DeviceParadigm, GateModelParadigmProperties
from braket.device_schema.device_connectivity import DeviceConnectivity
from braket.emulation.local_emulator import LocalEmulator
from braket.passes import (
    QubitCountValidator,
    GateValidator,
    ConnectivityValidator,
    GateConnectivityValidator,
)


@pytest.fixture
def mock_device_properties():
    """Create a mock device properties object for testing"""
    return DeviceCapabilities(
        paradigm=DeviceParadigmProperties(
            qubitCount=4,
            connectivity=DeviceConnectivity(
                fullyConnected=False,
                connectivityGraph={
                    "0": ["1", "2"],
                    "1": ["0", "3"],
                    "2": ["0", "3"],
                    "3": ["1", "2"],
                },
            ),
        ),
        provider={"providerName": "Test Provider"},
        service={"braketSchemaHeader": {"name": "device-schema", "version": "1"}},
        action={
            "braket.ir.jaqcd.program": {
                "actionType": "braket.ir.jaqcd.program",
                "version": ["1"],
                "supportedOperations": ["h", "cnot"],
            }
        },
    )


@pytest.fixture
def mock_fully_connected_device_properties(mock_device_properties):
    """Create a mock device properties object with full connectivity"""
    props = mock_device_properties
    props.paradigm.connectivity.fullyConnected = True
    props.paradigm.connectivity.connectivityGraph = {}
    return props


def test_from_device_properties(mock_device_properties):
    """Test creating LocalEmulator from device properties"""
    emulator = LocalEmulator.from_device_properties(mock_device_properties)

    # Verify backend is set correctly
    assert emulator._backend.name == "DensityMatrixSimulator"

    # Verify noise model is created
    assert emulator.noise_model is not None

    # Verify validation passes are added
    passes = emulator._emulator_passes
    assert any(isinstance(p, QubitCountValidator) for p in passes)
    assert any(isinstance(p, GateValidator) for p in passes)
    assert any(isinstance(p, ConnectivityValidator) for p in passes)
    assert any(isinstance(p, GateConnectivityValidator) for p in passes)


def test_from_json(mock_device_properties):
    """Test creating LocalEmulator from JSON string"""
    json_str = mock_device_properties.json()
    emulator = LocalEmulator.from_json(json_str)

    # Verify backend is set correctly
    assert emulator._backend.name == "DensityMatrixSimulator"

    # Verify validation passes are added
    passes = emulator._emulator_passes
    assert any(isinstance(p, QubitCountValidator) for p in passes)
    assert any(isinstance(p, GateValidator) for p in passes)


def test_from_device_properties_with_custom_backend(mock_device_properties):
    """Test creating LocalEmulator with custom backend"""
    emulator = LocalEmulator.from_device_properties(
        mock_device_properties, backend="custom_backend"
    )
    assert emulator._backend == "custom_backend"


def test_from_device_properties_with_custom_arn(mock_device_properties):
    """Test creating LocalEmulator with custom device ARN"""
    custom_arn = "arn:aws:braket:::device/test/custom"
    emulator = LocalEmulator.from_device_properties(mock_device_properties, device_arn=custom_arn)
    assert emulator.noise_model is not None


def test_add_validation_passes_fully_connected(mock_fully_connected_device_properties):
    """Test adding validation passes for fully connected device"""
    emulator = LocalEmulator()
    emulator._add_validation_passes(mock_fully_connected_device_properties)

    # Verify validation passes are added
    passes = emulator._emulator_passes
    assert any(isinstance(p, QubitCountValidator) for p in passes)
    assert any(isinstance(p, GateValidator) for p in passes)
    assert any(isinstance(p, ConnectivityValidator) for p in passes)
    assert any(isinstance(p, GateConnectivityValidator) for p in passes)

    # Verify topology graph is complete
    connectivity_validator = next(p for p in passes if isinstance(p, ConnectivityValidator))
    assert nx.is_strongly_connected(connectivity_validator._topology_graph)
    assert (
        len(connectivity_validator._topology_graph.edges) == 12
    )  # Complete directed graph with 4 vertices


def test_add_validation_passes_partial_connectivity(mock_device_properties):
    """Test adding validation passes for partially connected device"""
    emulator = LocalEmulator()
    emulator._add_validation_passes(mock_device_properties)

    # Verify validation passes are added
    passes = emulator._emulator_passes
    assert any(isinstance(p, QubitCountValidator) for p in passes)
    assert any(isinstance(p, GateValidator) for p in passes)
    assert any(isinstance(p, ConnectivityValidator) for p in passes)
    assert any(isinstance(p, GateConnectivityValidator) for p in passes)

    # Verify topology graph matches connectivity graph
    connectivity_validator = next(p for p in passes if isinstance(p, ConnectivityValidator))
    expected_edges = {(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)}
    actual_edges = set(connectivity_validator._topology_graph.edges)
    assert actual_edges == expected_edges


def test_from_json_invalid_json():
    """Test creating LocalEmulator with invalid JSON"""
    with pytest.raises(json.JSONDecodeError):
        LocalEmulator.from_json("invalid json")


def test_from_device_properties_no_paradigm():
    """Test creating LocalEmulator with device properties missing paradigm"""
    props = DeviceCapabilities(
        provider={"providerName": "Test Provider"},
        service={"braketSchemaHeader": {"name": "device-schema", "version": "1"}},
        action={
            "braket.ir.jaqcd.program": {
                "actionType": "braket.ir.jaqcd.program",
                "version": ["1"],
                "supportedOperations": ["h", "cnot"],
            }
        },
    )

    emulator = LocalEmulator.from_device_properties(props)

    # Verify basic validation passes are still added
    passes = emulator._emulator_passes
    assert any(isinstance(p, QubitCountValidator) for p in passes)
    assert any(isinstance(p, GateValidator) for p in passes)
    # But no connectivity validators
    assert not any(isinstance(p, ConnectivityValidator) for p in passes)
    assert not any(isinstance(p, GateConnectivityValidator) for p in passes)
