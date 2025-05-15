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

import enum


class ExperimentalCapability:
    def __init__(self, name: str, description: str = "") -> None:
        """A class representing an experimental capability in Amazon Braket.

        Experimental capabilities are features that are not yet part of the stable API
        and need to be explicitly enabled to be used.

        Args:
            name: The name of the capability.
            description: A description of the capability. Defaults to an empty string.
        """
        self.name = name
        self.description = description
        self._extended_name = name

    @property
    def __doc__(self) -> str:
        """Get the documentation string for the capability.

        Returns:
            str: A string containing the name and description of the capability.
        """
        return f"{self.name}: {self.description}"

    @property
    def extended_name(self) -> str:
        """Get the extended name of the capability.
        The extended name includes the enum class name and is set when the
        capability is registered.

        Returns:
            str: The extended name if set, None otherwise.
        """
        return self._extended_name

    def set_extended_name(self, extended_name: str) -> None:
        """Set the extended name of the capability.
        This method is called internally when registering the capability.

        Args:
            extended_name: The extended name to set.
        """
        self._extended_name = extended_name


# Global registry of experimental capabilities
EXPERIMENTAL_CAPABILITIES: dict[str, ExperimentalCapability] = {}


def register_capabilities(enum_cls: type[enum.Enum]) -> type[enum.Enum]:
    """Register all capabilities defined in an Enum class.
    This decorator function registers all ExperimentalCapability instances
    contained in Enum members into the global registry.

    Args:
        enum_cls: The Enum class containing ExperimentalCapability instances.

    Returns:
        Type[enum.Enum]: The same Enum class, allowing this function to be used as a decorator.

    Example:
        >>> @register_capabilities
        >>> class MyCapabilities(enum.Enum):
        ...     my_cap = ExperimentalCapability("my_cap", "My experimental capability")
    """
    for member in enum_cls:
        extended_name = str(member)
        member.value.set_extended_name(extended_name)
        EXPERIMENTAL_CAPABILITIES[extended_name] = member.value
    return enum_cls


def list_capabilities() -> str:
    """Get a formatted string listing all registered capabilities.

    Returns:
        str: A formatted string listing all registered experimental capabilities
            with their names and descriptions.
    """
    lines = ["Available Experimental Capabilities:"]
    lines.extend(f" - {cap.name}: {cap.description}" for cap in EXPERIMENTAL_CAPABILITIES.values())
    return "\n".join(lines)
