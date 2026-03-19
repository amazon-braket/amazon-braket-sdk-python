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

import pytest

from braket.circuits import Circuit
from braket.emulation.pass_manager import EmulatorValidationError, PassManager
from braket.emulation.passes import ValidationPass


class MockPass(ValidationPass):
    """Mock pass for testing"""

    _supported_specifications = Circuit

    def validate(self, task_specification):
        pass


class FailingPass(ValidationPass):
    """Mock pass that raises an exception"""

    _supported_specifications = Circuit

    def validate(self, task_specification):
        raise ValueError("Test validation error")


def test_pass_manager_iadd_with_pass_manager():
    """Test __iadd__ with PassManager (line 75)"""
    pm1 = PassManager(MockPass())
    pm2 = PassManager(MockPass())
    pm1 += pm2
    assert len(pm1._passes) == 2


def test_pass_manager_iadd_with_iterable():
    """Test __iadd__ with iterable (lines 77-78)"""
    pm = PassManager()
    passes = [MockPass(), MockPass()]
    pm += passes
    assert len(pm) == 2


def test_pass_manager_iadd_with_single_pass():
    """Test __iadd__ with single pass (line 80)"""
    pm = PassManager()
    pm += MockPass()
    assert len(pm) == 1


def test_pass_manager_add_with_pass_manager():
    """Test __add__ with PassManager (lines 85-86, 94)"""
    pm1 = PassManager(MockPass())
    pm2 = PassManager(MockPass())
    result = pm1 + pm2
    assert isinstance(result, PassManager)
    assert len(result) == 2


def test_pass_manager_add_with_single_pass():
    """Test __add__ with single EmulatorPass (lines 87-88, 94)"""
    pm = PassManager(MockPass())
    result = pm + MockPass()
    assert isinstance(result, PassManager)
    assert len(result) == 2


def test_pass_manager_add_with_iterable():
    """Test __add__ with iterable (lines 89-90, 94)"""
    pm = PassManager(MockPass())
    passes = [MockPass(), MockPass()]
    result = pm + passes
    assert isinstance(result, PassManager)
    assert len(result) == 3


def test_pass_manager_validate_with_exception():
    """Test validate method raises EmulatorValidationError"""
    pm = PassManager(FailingPass())
    circuit = Circuit().h(0)
    with pytest.raises(EmulatorValidationError, match="Test validation error"):
        pm.validate(circuit)


def test_pass_manager_len():
    """Test __len__ method (line 94)"""
    pm = PassManager([MockPass(), MockPass(), MockPass()])
    result = len(pm)
    assert result == 3

    pm_empty = PassManager()
    result_empty = len(pm_empty)
    assert result_empty == 0

    # Also test with single pass
    pm_single = PassManager(MockPass())
    assert len(pm_single) == 1
