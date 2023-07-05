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


"""Python program-level transformations for objects, operations and logical controls that relate
to AutoQASM types. Generally, operators are only used in the code template in AutoQASM converters.
This module implements operators that AutoQASM overloads or adds on top of AutoGraph.
"""

# TODO: Commented out operators below are not yet implemented.
# We need to either implement these, or determine they are not needed and remove them.

# Operators below are imported directly from core autograph implementation
from braket.experimental.autoqasm.autograph.operators.variables import (  # noqa: F401
    Undefined,
    UndefinedReturnValue,
    ld,
    ldu,
)

from .assignments import assign_stmt  # noqa: F401
from .conditional_expressions import if_exp  # noqa: F401
from .control_flow import for_stmt, if_stmt, while_stmt  # noqa: F401

# from .data_structures import list_append
# from .data_structures import list_pop
# from .data_structures import list_stack
# from .data_structures import ListPopOpts
# from .data_structures import ListStackOpts
from .data_structures import new_list  # noqa: F401

# from .exceptions import assert_stmt
# from .logical import and_
from .logical import eq  # noqa: F401

# from .logical import not_
# from .logical import not_eq
# from .logical import or_
# from .py_builtins import float_
# from .py_builtins import int_
# from .py_builtins import len_
# from .py_builtins import print_
# from .py_builtins import range_
from .slices import GetItemOpts, get_item, set_item  # noqa: F401
