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

"""Tests for the types module."""

from typing import Tuple

import oqpy
import pytest

from braket.experimental.autoqasm.types.types import qasm_range


@pytest.mark.parametrize(
    "range_params, expected_range_params",
    [
        ((0, 5, 1), (0, 5, 1)),
        ((5, None, 2), (0, 5, 2)),
    ],
)
def test_qasm_range(
    range_params: Tuple[int, int, int], expected_range_params: Tuple[int, int, int]
) -> None:
    """Test `qasm_range()` returning correct `Range` object.

    Args:
        range_params (Tuple[int, int, int]): Range parameters to instantiate `oqpy.Range`
        expected_range_params (Tuple[int, int, int]): Expected range parameters
    """
    start, stop, step = range_params
    qrange = qasm_range(start, stop, step)
    assert isinstance(qrange, oqpy.Range)
    assert (qrange.start, qrange.stop, qrange.step) == expected_range_params
