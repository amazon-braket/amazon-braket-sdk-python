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

from braket.experimental_capabilities import EnableExperimentalCapability
from braket.experimental_capabilities.experimental_capability_context import (
    GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT,
)


def test_enable_experimental_capability_context():
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled

    with EnableExperimentalCapability():
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled

    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled


def test_nested_capability_contexts():
    # Test that nested contexts work correctly
    with EnableExperimentalCapability():
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled

        # Nested context - should preserve state on exit
        with EnableExperimentalCapability():
            assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled

        # After inner context, the capability should still be enabled
        assert GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled

    # After nested context, the capability should be disabled
    assert not GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled
