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

from __future__ import annotations
from enum import Enum

import pytest

from braket.experimental_capabilities import (
    EnableExperimentalCapability,
    ExperimentalCapability,
    list_capabilities,
)
from braket.experimental_capabilities.experimental_capability import register_capabilities
from braket.experimental_capabilities.experimental_capability_context import (
    GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT,
    ExperimentalCapabilityContextError,
)


@register_capabilities
class MockDeviceExperimentalCapabilities(Enum):
    feature1 = ExperimentalCapability("feature1", description="Mock experimental capability 1")
    feature2 = ExperimentalCapability("feature2", description="Mock experimental capability 2")


GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.register_capability(
    MockDeviceExperimentalCapabilities.feature1.value
)
GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.register_capability(
    MockDeviceExperimentalCapabilities.feature2.value
)


def test_experimental_capability_creation():
    cap = ExperimentalCapability("test_cap", "This is a test capability")
    assert cap.name == "test_cap"
    assert cap.description == "This is a test capability"
    assert cap.__doc__ == "test_cap: This is a test capability"


def test_register_capabilities():
    class TestCapabilities(Enum):
        test_cap = ExperimentalCapability("test_cap", "Test capability")

    register_capabilities(TestCapabilities)
    assert TestCapabilities.test_cap.value.extended_name == "TestCapabilities.test_cap"

    capabilities_list = list_capabilities()
    assert "test_cap: Test capability" in capabilities_list


def test_enable_experimental_capability_context():
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
