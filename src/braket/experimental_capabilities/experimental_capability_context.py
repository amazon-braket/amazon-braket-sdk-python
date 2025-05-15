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

from enum import Enum
from typing import Any, Optional

from braket.experimental_capabilities.experimental_capability import (
    EXPERIMENTAL_CAPABILITIES,
    ExperimentalCapability,
)


class ExperimentalCapabilityContextError(Exception):
    """Exception raised for errors related to experimental capability contexts."""


class GlobalExperimentalCapabilityContext:
    def __init__(self) -> None:
        """A global singleton that tracks which experimental capabilities are enabled.
        This class stores the state of all registered experimental capabilities
        and provides methods to check whether specific capabilities are enabled.
        """
        self._capabilities = {
            cap.extended_name: False for cap in EXPERIMENTAL_CAPABILITIES.values()
        }

    @property
    def capabilities(self) -> dict[str, bool]:
        """Get a dictionary of all capabilities and their enabled status.

        Returns:
            dict[str, bool]: Dictionary mapping capability extended names to boolean values
                indicating whether the capability is enabled.
        """
        return self._capabilities

    def check_enabled(self, capability: ExperimentalCapability | Enum) -> bool:
        """Check if a specific capability is enabled.

        Args:
            capability: The capability to check. Can be an ExperimentalCapability
                instance or an Enum member containing one.

        Returns:
            bool: True if the capability is enabled, False otherwise.
        """
        if isinstance(capability, Enum):
            capability = capability.value

        if capability.extended_name not in self._capabilities:
            raise ExperimentalCapabilityContextError(f"Unknown capability flag: {capability.name}")
        return self.capabilities[capability.extended_name]

    def register_capability(self, cap: ExperimentalCapability):
        """Register a new experimental capability to the global capability context.

        Args:
            cap: The experimental capability to register.
        """
        self._capabilities[cap.extended_name] = False


# Global singleton instance
GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT = GlobalExperimentalCapabilityContext()


class EnableExperimentalCapability:
    def __init__(self, *capabilities: ExperimentalCapability | Enum) -> None:
        """Context manager for temporarily enabling experimental capabilities.
        This context manager allows enabling one or more experimental capabilities
        for the duration of a code block, after which the capabilities are
        returned to their previous states.

        Examples:
            >>> with EnableExperimentalCapability(IqmExperimentalCapabilities.classical_control):
            ...     circuit = Circuit()
            ...     circuit.cc_prx(0, 0.1, 0.2, 0)

        Args:
            *capabilities: One or more capabilities to enable.
                Can be ExperimentalCapability instances or Enum members containing them.
        """
        self.capabilities: list[ExperimentalCapability] = list([
            cap.value if isinstance(cap, Enum) else cap for cap in capabilities
        ])
        self._previous_values: dict[str, bool] = {}

        for capability in self.capabilities:
            if capability.extended_name not in GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.capabilities:
                raise ExperimentalCapabilityContextError(
                    f"Unknown capability flag: {capability.extended_name}"
                )

    def __enter__(self) -> None:
        """Enter the context, enabling all specified capabilities.
        This method saves the current state of each capability and then enables them.
        """
        for capability in self.capabilities:
            self._previous_values[capability.extended_name] = (
                GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.capabilities[capability.extended_name]
            )
            GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT._capabilities[capability.extended_name] = True

    def __exit__(
        self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]
    ) -> None:
        """Exit the context, restoring each capability to its previous state.

        Args:
            exc_type: The exception type if an exception was raised in the context, else None.
            exc_val: The exception value if an exception was raised in the context, else None.
            exc_tb: The exception traceback if an exception was raised in the context, else None.
        """
        for cap_extended_name, old_value in self._previous_values.items():
            GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT._capabilities[cap_extended_name] = old_value
