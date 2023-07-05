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

"""AutoQASM types and type utilities."""

from typing import Any, Optional

import oqpy.base


def is_qasm_type(val: Any) -> bool:
    """Returns whether the provided object is of a QASM type or is itself a QASM type
    which receives special treatment by AutoQASM.

    Args:
        val (Any): The object of which to check the type.

    Returns:
        bool: Whether the object is a QASM type.
    """
    try:
        if issubclass(val, (oqpy.Range, oqpy._ClassicalVar, oqpy.base.OQPyExpression)):
            return True
    except TypeError:
        # `val` is not a class
        pass

    return isinstance(val, (oqpy.Range, oqpy._ClassicalVar, oqpy.base.OQPyExpression))


def qasm_range(start: int, stop: Optional[int] = None, step: Optional[int] = 1) -> oqpy.Range:
    """Range definition.

    Args:
        start (int): Start of the range
        stop (Optional[int]): End of the range. Defaults to None.
        step (Optional[int]): Step of the range. Defaults to 1.

    Returns:
        oqpy.Range: oqpy range definition.
    """
    if stop is None:
        stop = start
        start = 0
    return oqpy.Range(start, stop, step)
