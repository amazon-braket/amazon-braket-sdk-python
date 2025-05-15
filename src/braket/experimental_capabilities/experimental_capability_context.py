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

from braket.experimental_capabilities.experimental_capability import (
    ExperimentalCapability,
    EXPERIMENTAL_CAPABILITIES,
)


class ExperimentalCapabilityContextError(Exception):
    """Exception raised for errors related to experimental capability contexts."""
    pass


class GlobalExperimentalCapabilityContext:
    def __init__(self):
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
            Dict[str, bool]: Dictionary mapping capability extended names to boolean values
                indicating whether the capability is enabled.
        """
        return self._capabilities

    def check_enabled(self, capability: ExperimentalCapability | Enum):
        if isinstance(capability, Enum):
            capability = capability.value

        if capability.extended_name not in self._capabilities:
            raise ExperimentalCapabilityContextError(f"Unknown capability flag: {capability.name}")
        return self.capabilities[capability.extended_name]
    
    def register_capability(self, cap: ExperimentalCapability):
        self._capabilities[cap.extended_name] = False


# Global singleton instance
GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT = GlobalExperimentalCapabilityContext()


class EnableExperimentalCapability:
    def __init__(self, *capabilities: ExperimentalCapability | Enum):
        self.capabilities: list[ExperimentalCapability] = list([
            cap.value if isinstance(cap, Enum) else cap for cap in capabilities
        ])
        self._previous_values: dict[str, bool] = {}

        for capability in self.capabilities:
            if capability.extended_name not in GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.capabilities:
                raise ExperimentalCapabilityContextError(
                    f"Unknown capability flag: {capability.extended_name}"
                )

    def __enter__(self):
        for capability in self.capabilities:
            self._previous_values[capability.extended_name] = (
                GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT.capabilities[capability.extended_name]
            )
            GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT._capabilities[capability.extended_name] = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        for cap_extended_name, old_value in self._previous_values.items():
            GLOBAL_EXPERIMENTAL_CAPABILITY_CONTEXT._capabilities[cap_extended_name] = old_value
