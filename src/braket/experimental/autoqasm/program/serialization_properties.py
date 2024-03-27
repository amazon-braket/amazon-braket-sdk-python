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

from dataclasses import dataclass


@dataclass
class OpenQASMSerializationProperties:
    auto_defcalgrammar: bool | None = False
    """Whether to automatically include defcalgrammar when pulses are used. Default to False."""

    include_externs: bool | None = False
    """Whether to include externs. Default to False."""


# Type alias to refer to possible serialization properties. Can be expanded once
# new properties are added.
SerializationProperties = OpenQASMSerializationProperties
