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

"""Constants used in the output conversion of AutoQASM programs. When we output programs to
to OpenQASM, we must declare variables and thus associate them with a string name.
"""

ARRAY_NAME_TEMPLATE = "__arr_{0}__"
"""String template for auto-generated array names."""

BIT_NAME_TEMPLATE = "__bit_{0}__"
"""String template for auto-generated bit variable names."""

BOOL_NAME_TEMPLATE = "__bool_{0}__"
"""String template for auto-generated boolean variable names."""

FLOAT_NAME_TEMPLATE = "__float_{0}__"
"""String template for auto-generated float names."""

INT_NAME_TEMPLATE = "__int_{0}__"
"""String template for auto-generated integer names."""

QUBIT_REGISTER = "__qubits__"
"""Qubits are globally addressed, and so we can specify a single qubit register name."""

AUTOGRAPH_RETVAL_VARIABLE_NAME = "retval_"
"""A special name for variables assigned to the return values of AutoGraph function calls."""

AUTOQASM_RETVAL_VARIABLE_NAME = "__retval__"
"""A special name for variables assigned to the return values of AutoQASM function calls."""
