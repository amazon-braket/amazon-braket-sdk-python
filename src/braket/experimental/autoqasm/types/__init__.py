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

"""This module implements types used by AutoQASM programs, as well as utilities and converters
for type handling.
"""

from .conversions import map_parameter_type, var_type_from_oqpy, wrap_value  # noqa: F401
from .types import (  # noqa: F401
    ArrayVar,
    BitVar,
    BoolVar,
    FloatVar,
    IntVar,
    QubitIdentifierType,
    Range,
    is_qasm_type,
    is_qubit_identifier_type,
    make_annotations_list,
)
