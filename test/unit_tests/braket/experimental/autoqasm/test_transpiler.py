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

"""Tests for transpiler."""

import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.autograph.core.ag_ctx import ControlStatusCtx, Status
from braket.experimental.autoqasm.gates import h, measure, x


def test_convert_invalid_object() -> None:
    """Tests the aq.function decorator on something that is not a function."""

    @aq.function
    class MyClass:
        pass

    with pytest.raises(ValueError):
        MyClass()


def test_autograph_disabled() -> None:
    """Tests the aq.function decorator with autograph disabled by control status,
    and verifies that the function is not converted."""

    @aq.function
    def my_program():
        h(0)
        if measure(0):
            x(0)

    with ControlStatusCtx(Status.DISABLED):
        with pytest.raises(RuntimeError):
            my_program()
