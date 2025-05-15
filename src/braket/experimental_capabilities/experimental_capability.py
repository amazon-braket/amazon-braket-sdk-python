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


class ExperimentalCapability:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._extended_name = name

    @property
    def __doc__(self):
        return f"{self.name}: {self.description}"

    @property
    def extended_name(self):
        return self._extended_name

    def set_extended_name(self, extended_name: str):
        self._extended_name = extended_name


# Global registry of experimental capabilities
EXPERIMENTAL_CAPABILITIES: dict[str, ExperimentalCapability] = {}


def register_capabilities(enum_cls):
    for member in enum_cls:
        extended_name = member.__str__()
        member.value.set_extended_name(extended_name)
        EXPERIMENTAL_CAPABILITIES[extended_name] = member.value
    return enum_cls


def list_capabilities() -> str:
    lines = ["Available Experimental Capabilities:"]
    for cap in EXPERIMENTAL_CAPABILITIES.values():
        lines.append(f" - {cap.name}: {cap.description}")
    return "\n".join(lines)
