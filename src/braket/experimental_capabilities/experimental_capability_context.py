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


class ExperimentalCapabilityContextError(Exception):
    """Exception raised for errors related to experimental capability contexts."""


class GlobalExperimentalCapabilityContext:
    def __init__(self) -> None:
        """A global singleton that tracks whether experimental capabilities are enabled."""
        self._is_enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if experimental capabilities are enabled.

        Returns:
            bool: True if experimental capabilities are enabled, False otherwise.
        """
        return self._is_enabled

    def enable(self) -> None:
        """Enable all experimental capabilities."""
        self._is_enabled = True

    def disable(self) -> None:
        """Disable all experimental capabilities."""
        self._is_enabled = False

    def set_state(self, state: bool) -> None:
        """Set the state of all experimental capabilities.

        Args:
            state: The state to set. True to enable all capabilities, False to disable all.
        """
        self._is_enabled = bool(state)


# Global singleton instance
GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT = GlobalExperimentalCapabilityContext()


class EnableExperimentalCapability:
    def __init__(self) -> None:
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

        Examples:
            >>> with EnableExperimentalCapability():
            ...     circuit = Circuit()
            ...     circuit.cc_prx(0, 0.1, 0.2, 0)

        """
        self._previous_state = GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.is_enabled

    def __enter__(self) -> None:
        """Enter the context, enabling all specified capabilities.
        This method saves the current state of each capability and then enables them.
        """
        GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.enable()

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
        GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.set_state(self._previous_state)
