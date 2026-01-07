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

import types
import warnings
from typing import Literal

ExperimentalCapabilitiesEnabled = Literal["ALL"]
EXPERIMENTAL_CAPABILITIES_ALL: ExperimentalCapabilitiesEnabled = "ALL"


class ExperimentalCapabilityContextError(Exception):
    """Exception raised for errors related to experimental capability contexts."""


class GlobalExperimentalCapabilityContext:
    def __init__(self) -> None:
        """A global singleton that tracks whether experimental capabilities are enabled."""
        self._all_enabled = False

    def is_enabled(self) -> bool:
        """Check if experimental capabilities are enabled.

        Returns:
            bool: True if experimental capabilities are enabled, False otherwise.
        """
        return self._all_enabled

    def enable(
        self,
        experimental_capabilities: ExperimentalCapabilitiesEnabled = EXPERIMENTAL_CAPABILITIES_ALL,
    ) -> None:
        """Enable all experimental capabilities. Default behavior is to enable all.

        Args:
            experimental_capabilities (ExperimentalCapabilitiesEnabled | None):
            The experimental capabilities to enable. Defaults to all capabilities.
        Raises:
            ExperimentalCapabilityContextError: If the experimental capabilities are not valid.
        """
        if experimental_capabilities != EXPERIMENTAL_CAPABILITIES_ALL:
            raise ExperimentalCapabilityContextError(
                "Invalid experimental capabilities options provided."
            )
        self._all_enabled = True

    def disable(self) -> None:
        """Disable all experimental capabilities."""
        self._all_enabled = False

    def get_enabled_capabilities(self) -> ExperimentalCapabilitiesEnabled | None:
        """Get the set of currently enabled experimental capabilities.
        Returns:
            ExperimentalCapabilitiesEnabled | None: The currently enabled
                experimental capabilities.
        """
        if self._all_enabled:
            return EXPERIMENTAL_CAPABILITIES_ALL
        return None

    def set_state(self, experimental_capabilities: ExperimentalCapabilitiesEnabled | None) -> None:
        """Set the state of experimental capabilities.
        Args:
            experimental_capabilities (ExperimentalCapabilitiesEnabled | None):
                The state of enabled experimental capabilities.
        """
        if experimental_capabilities == EXPERIMENTAL_CAPABILITIES_ALL:
            self.enable()
        else:
            self.disable()


# Global singleton instance
GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT = GlobalExperimentalCapabilityContext()


class EnableExperimentalCapability:
    def __init__(
        self,
        experimental_capabilities: ExperimentalCapabilitiesEnabled = EXPERIMENTAL_CAPABILITIES_ALL,
    ) -> None:
        """This context manager temporarily enables experimental capabilities
        for the duration of a code block, after which the capabilities are
        returned to their previous states.

        Experimental capabilities are those that hardware providers are rapidly
        developing. As hardware improve and the support on the capabilities are expanded,
        the behavior may change, including becoming less restrictive, more performant
        and having higher quality. See the developer guide [1] to learn more about
        experimental capabilities on Amazon Braket.
        [1] https://docs.aws.amazon.com/braket/latest/developerguide/
        braket-experimental-capabilities.html

        Args: experimental_capabilities (ExperimentalCapabilitiesEnabled | None):
            The experimental capabilities to enable. Defaults to all capabilities.

        Examples:
            >>> with EnableExperimentalCapability():
            ...     circuit = Circuit()
            ...     circuit.cc_prx(0, 0.1, 0.2, 0)

        """
        self._previous_enabled_capabilities = (
            GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
        )
        self._current_enabled_capabilities = experimental_capabilities

    def __enter__(self) -> None:
        """Enter the context, enabling all specified capabilities.
        This method saves the current state of each capability and then enables them.
        """
        GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.enable(self._current_enabled_capabilities)

        warnings.warn(
            (
                "You are enabling experimental capabilities. To view descriptions and "
                "restrictions of experimental capabilities, please review Amazon Braket "
                "Developer Guide ("
                "https://docs.aws.amazon.com/braket/latest/developerguide/braket-experimental-capabilities.html"
                ")."
            ),
            category=UserWarning,
            stacklevel=1,
        )

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit the context, restoring each capability to its previous state.

        Args:
            exc_type: The exception type if an exception was raised in the context, else None.
            exc_val: The exception value if an exception was raised in the context, else None.
            exc_tb: The exception traceback if an exception was raised in the context, else None.
        """
        GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.set_state(self._previous_enabled_capabilities)
