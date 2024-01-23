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

# Operators below are imported directly from core autograph implementation
from braket.experimental.autoqasm.autograph.impl.api_core import autograph_artifact  # noqa: F401
from braket.experimental.autoqasm.autograph.operators.variables import (  # noqa: F401
    Undefined,
    UndefinedReturnValue,
    ld,
    ldu,
)

from .assignments import assign_stmt  # noqa: F401
from .comparisons import gt_, gteq_, lt_, lteq_  # noqa: F401
from .conditional_expressions import if_exp  # noqa: F401
from .control_flow import for_stmt, if_stmt, while_stmt  # noqa: F401
from .data_structures import ListPopOpts  # noqa: F401
from .data_structures import ListStackOpts  # noqa: F401
from .data_structures import list_append  # noqa: F401
from .data_structures import list_pop  # noqa: F401
from .data_structures import list_stack  # noqa: F401
from .data_structures import new_list  # noqa: F401
from .exceptions import assert_stmt  # noqa: F401
from .logical import and_  # noqa: F401
from .logical import eq  # noqa: F401
from .logical import not_  # noqa: F401
from .logical import not_eq  # noqa: F401
from .logical import or_  # noqa: F401
from .return_statements import return_output_from_main_  # noqa: F401
from .slices import GetItemOpts, get_item, set_item  # noqa: F401
