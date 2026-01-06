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
from collections.abc import Iterable
from enum import Enum
from typing import Literal

ExperimentalCapabilitiesEnabled = Literal["ALL"]
ALL_EXPERIMENTAL_CAPABILITIES: ExperimentalCapabilitiesEnabled = "ALL"


class ExperimentalCapabilities(str, Enum):
    "Valid Experimental Capability Options"


class ExperimentalCapabilityContextError(Exception):
    """Exception raised for errors related to experimental capability contexts."""


class GlobalExperimentalCapabilityContext:
    def __init__(self) -> None:
        """A global singleton that tracks whether experimental capabilities are enabled."""
        self._all_enabled = False
        self._currently_enabled_capabilities = set()

    def is_enabled(
        self,
        experimental_capabilities: ExperimentalCapabilitiesEnabled
        | ExperimentalCapabilities
        | Iterable[ExperimentalCapabilities] = ALL_EXPERIMENTAL_CAPABILITIES,
    ) -> bool:
        """Check if experimental capabilities are enabled, either for all or a specific
        set of experimental capabilities. Defaults to checking for all enabled.

        Returns:
            bool: True if experimental capabilities are enabled, False otherwise.
        """
        if experimental_capabilities == ALL_EXPERIMENTAL_CAPABILITIES:
            return self._all_enabled
        if isinstance(experimental_capabilities, ExperimentalCapabilities):
            return (
                self._all_enabled
                or experimental_capabilities in self._currently_enabled_capabilities
            )
        if isinstance(experimental_capabilities, Iterable):
            return self._all_enabled or set(experimental_capabilities).issubset(
                self._currently_enabled_capabilities
            )
        raise TypeError("Invalid experimental_capabilities value provided.")

    def enable(
        self,
        experimental_capabilities: ExperimentalCapabilitiesEnabled
        | Iterable[ExperimentalCapabilities] = ALL_EXPERIMENTAL_CAPABILITIES,
    ) -> None:
        """Enable specified experimental capabilities; defaults to enabling all.

        Args:
            experimental_capabilities: the experimental capabilities to enable.
        """
        if experimental_capabilities == ALL_EXPERIMENTAL_CAPABILITIES:
            self._all_enabled = True
        else:
            capabilities_set = set(experimental_capabilities)
            self._currently_enabled_capabilities.update(capabilities_set)

    def disable(
        self,
        experimental_capabilities: ExperimentalCapabilitiesEnabled
        | Iterable[ExperimentalCapabilities]
        | None = None,
    ) -> None:
        """Disable all specified experimental capabilities; defaults to disabling all.

        Args:
            experimental_capabilities: the experimental capabilities to disable.
        """
        if experimental_capabilities is None:
            self._all_enabled = False
            self._currently_enabled_capabilities.clear()
        elif experimental_capabilities == ALL_EXPERIMENTAL_CAPABILITIES:
            self._all_enabled = False
        else:
            self._currently_enabled_capabilities.difference_update(experimental_capabilities)

    def get_enabled_capabilities(
        self,
    ) -> ExperimentalCapabilitiesEnabled | list[ExperimentalCapabilities]:
        """Get the set of currently enabled experimental capabilities.

        Returns:
            set[ExperimentalCapabilities]: The set of currently enabled experimental capabilities.
        """
        if self._all_enabled:
            return ALL_EXPERIMENTAL_CAPABILITIES
        return list(self._currently_enabled_capabilities)


# Global singleton instance
GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT = GlobalExperimentalCapabilityContext()


class EnableExperimentalCapability:
    def __init__(
        self,
        enabled_capabilities: ExperimentalCapabilitiesEnabled
        | Iterable[ExperimentalCapabilities] = ALL_EXPERIMENTAL_CAPABILITIES,
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

        Args:
            enabled_capabilities: List of experimental capability strings to enable.
                        If empty, defaults to "ALL".
        Examples:
            >>> with EnableExperimentalCapability():
            ...     circuit = Circuit()
            ...     circuit.cc_prx(0, 0.1, 0.2, 0)

        """
        self._previous_enabled_capabilities = (
            GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.get_enabled_capabilities()
        )
        self._current_enabled_capabilities = enabled_capabilities

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
        GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.disable(self._current_enabled_capabilities)
        GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.enable(self._previous_enabled_capabilities)
