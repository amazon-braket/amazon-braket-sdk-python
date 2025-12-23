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

import pytest
import warnings

from braket.experimental_capabilities import EnableExperimentalCapability
from braket.experimental_capabilities.experimental_capability_context import (
    GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT,
    ExperimentalCapability,
)


def test_enable_experimental_capability_context():
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

    with EnableExperimentalCapability():
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled([ExperimentalCapability.ALL])
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(ExperimentalCapability.ALL)
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities() == [
            ExperimentalCapability.ALL
        ]
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()


def test_nested_capability_contexts():
    # Test that nested contexts work correctly
    with EnableExperimentalCapability():
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

        # Nested context - should preserve state on exit
        with EnableExperimentalCapability():
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

        # After inner context, the capability should still be enabled
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

    # After nested context, the capability should be disabled
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()


def test_multiple_capabilities():
    """Test enabling multiple explicit capabilities."""
    # Initially no capabilities enabled
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

    with EnableExperimentalCapability(["CapA", "CapB", "CapC"]):
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA"])
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA", "CapB"])
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA", "CapB", "CapC"])

        assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapD"])
        assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA", "CapD"])
        assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

        enabled = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
        assert set(enabled) == {"CapA", "CapB", "CapC"}

    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA"])


def test_all_capability_explicit():
    """Test explicitly passing 'ALL' capability."""
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

    with EnableExperimentalCapability(["ALL"]):
        # ALL should enable everything
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["ALL"])
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(ExperimentalCapability.ALL)
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA", "CapB", "CapC"])

        # get_enabled_capabilities should return [ALL]
        enabled = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
        assert enabled == [ExperimentalCapability.ALL]

    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()


def test_all_with_other_capabilities():
    """Test passing 'ALL' with other capabilities - should trigger warning and enable ALL."""
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

    with EnableExperimentalCapability(["ALL", "CapA", "CapB"]):
        # Should enable ALL despite other capabilities being specified
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["ALL"])
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA", "CapB", "CapC", "CapD"])

        # get_enabled_capabilities should return [ALL]
        enabled = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
        assert enabled == [ExperimentalCapability.ALL]

    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()


def test_nested_contexts_explicit_outer_all_inner():
    """Test nested contexts: explicit capabilities at outer level, ALL at inner level."""
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

    with EnableExperimentalCapability(["CapA", "CapB", "CapC"]):
        with EnableExperimentalCapability(["ALL"]):
            # Inner context: ALL should enable everything
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["ALL"])
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled([
                "CapA",
                "CapB",
                "CapC",
                "CapD",
                "CapE",
            ])
            enabled_inner = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
            assert enabled_inner == [ExperimentalCapability.ALL]

        # After inner context exits, should return to outer context state
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA", "CapB", "CapC"])
        assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapD"])
        assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()
        enabled_back_to_outer = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
        assert set(enabled_back_to_outer) == {"CapA", "CapB", "CapC"}

    # After outer context exits, no capabilities should be enabled
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()


def test_nested_contexts_all_outer_explicit_inner():
    """Test nested contexts: ALL at outer level, explicit capabilities at inner level."""
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

    with EnableExperimentalCapability(["ALL"]):
        # Outer context: ALL capabilities enabled
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA", "CapB", "CapC", "CapD"])
        enabled_outer = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
        assert enabled_outer == [ExperimentalCapability.ALL]

        with EnableExperimentalCapability(["CapX", "CapY"]):
            # Inner context: picks up the "ALL" from the outer context
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapX", "CapY"])
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapZ"])
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["ALL"])
            enabled_inner = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
            assert set(enabled_inner) == {ExperimentalCapability.ALL}

        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA", "CapB", "CapC", "CapD"])
        enabled_back_to_outer = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
        assert enabled_back_to_outer == [ExperimentalCapability.ALL]

    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()


def test_nested_contexts_explicit_both_levels():
    """Test nested contexts: different explicit capabilities at both levels."""
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()

    with EnableExperimentalCapability(["CapA", "CapB"]):
        with EnableExperimentalCapability(["CapA", "CapC", "CapD"]):
            # Inner context: CapA, CapC and CapD enabled and CapB picked up from outer
            print(GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities())
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled([
                "CapA",
                "CapB",
                "CapC",
                "CapD",
            ])
            enabled_inner = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
            assert set(enabled_inner) == {"CapA", "CapB", "CapC", "CapD"}

        # After inner context exits, should return to outer context state
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapA", "CapB"])
        assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(["CapC"])
        enabled_back_to_outer = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
        assert set(enabled_back_to_outer) == {"CapA", "CapB"}

    # After outer context exits, no capabilities should be enabled
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled()


@pytest.mark.parametrize("invalid_input", [None, 12345])
def test_is_enabled_invalid_input(invalid_input):
    with pytest.raises(TypeError) as exception:
        with EnableExperimentalCapability():
            GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled(invalid_input)
    assert (
        str(exception.value)
        == "If provided, Experimental capabilities must be a single \
                or list of ExperimentalCapability strings"
    )
