import pytest
from enum import Enum
from unittest.mock import patch, MagicMock

from braket.experimental_capabilities import (
    ExperimentalCapability,
    EnableExperimentalCapability,
    list_capabilities,
    IqmExperimentalCapabilities,
)
from braket.experimental_capabilities.experimental_capability_context import (
    GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT,
    ExperimentalCapabilityContextError,
)
from braket.experimental_capabilities.experimental_capability import register_capabilities
from braket.experimental_capabilities.iqm.classical_control import CCPRx, MeasureFF
from braket.circuits import Circuit
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.serialization import IRType, OpenQASMSerializationProperties

from braket.experimental_capabilities.experimental_capability_context import GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT


def reset_capabilities_context():
    """Reset the experimental capabilities context."""
    for cap_name in GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.capabilities:
        GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT._capabilities[cap_name] = False


@register_capabilities
class MockDeviceExperimentalCapabilities(Enum):
    feature1 = ExperimentalCapability(
        "feature1", description="Mock experimental capability 1"
    )
    feature2 = ExperimentalCapability(
        "feature2", description="Mock experimental capability 2"
)
GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.register_capability(MockDeviceExperimentalCapabilities.feature1.value)
GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.register_capability(MockDeviceExperimentalCapabilities.feature2.value)


# Tests for basic ExperimentalCapability functionality
def test_experimental_capability_creation():
    cap = ExperimentalCapability("test_cap", "This is a test capability")
    assert cap.name == "test_cap"
    assert cap.description == "This is a test capability"
    assert cap.__doc__ == "test_cap: This is a test capability"


# Tests for capability registration
def test_register_capabilities():
    class TestCapabilities(Enum):
        test_cap = ExperimentalCapability("test_cap", "Test capability")

    register_capabilities(TestCapabilities)
    assert TestCapabilities.test_cap.value.extended_name == "TestCapabilities.test_cap"

    capabilities_list = list_capabilities()
    assert "test_cap: Test capability" in capabilities_list


# Tests for EnableExperimentalCapability context manager
def test_enable_experimental_capability_context():
    reset_capabilities_context()

    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
        MockDeviceExperimentalCapabilities.feature1
    )

    with EnableExperimentalCapability(MockDeviceExperimentalCapabilities.feature1):
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
            MockDeviceExperimentalCapabilities.feature1
        )

    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
        MockDeviceExperimentalCapabilities.feature1
    )


def test_enable_multiple_capabilities():
    reset_capabilities_context()

    # Check both capabilities are disabled
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
        MockDeviceExperimentalCapabilities.feature1
    )
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
        MockDeviceExperimentalCapabilities.feature2
    )

    # Enable both capabilities
    with EnableExperimentalCapability(
        MockDeviceExperimentalCapabilities.feature1,
        MockDeviceExperimentalCapabilities.feature2,
    ):
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
            MockDeviceExperimentalCapabilities.feature1
        )
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
            MockDeviceExperimentalCapabilities.feature2
        )

    # Check both are disabled again
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
        MockDeviceExperimentalCapabilities.feature1
    )
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
        MockDeviceExperimentalCapabilities.feature2
    )


def test_nested_capability_contexts():
    reset_capabilities_context()

    # Test that nested contexts work correctly
    with EnableExperimentalCapability(MockDeviceExperimentalCapabilities.feature1):
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
            MockDeviceExperimentalCapabilities.feature1
        )

        # Nested context - should preserve state on exit
        with EnableExperimentalCapability(MockDeviceExperimentalCapabilities.feature2):
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
                MockDeviceExperimentalCapabilities.feature1
            )
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
                MockDeviceExperimentalCapabilities.feature2
            )

        # After inner context, first capability should still be enabled
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
            MockDeviceExperimentalCapabilities.feature1
        )
        assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(
            MockDeviceExperimentalCapabilities.feature2
        )


def test_invalid_capability_error():
    # Create a dummy capability that isn't registered
    dummy_cap = ExperimentalCapability("dummy", "Not registered")

    with pytest.raises(ExperimentalCapabilityContextError):
        with EnableExperimentalCapability(dummy_cap):
            pass


def test_check_enabled_with_unknown_capability():
    dummy_cap = ExperimentalCapability("dummy", "Not registered")

    with pytest.raises(ExperimentalCapabilityContextError):
        GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.check_enabled(dummy_cap)
