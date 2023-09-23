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


from dataclasses import dataclass
from typing import Optional


@dataclass
class SerializationConfig:
    """Abstract class for serialization configuration."""

    pass


@dataclass
class OpenQASMSerializationConfig(SerializationConfig):
    auto_defcalgrammar: Optional[bool] = False
    """Whether to automatically include defcalgrammar when pulses are used. Default to False."""

    include_externs: Optional[bool] = False
    """Whether to include externs. Default to False."""
