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
from braket.emulation.passes.generic.program_set_validator import ProgramSetValidator
from braket.program_sets import ProgramSet
from braket.circuits import Circuit


def test_program_set_validator_supported():
    device_action = {
        "braket.ir.openqasm.program_set": {"maximumTotalShots": 1000, "maximumExecutables": 10}
    }
    validator = ProgramSetValidator(device_action)
    program_set = ProgramSet([Circuit().h(0)], shots_per_executable=100)
    validator.validate(program_set)  # Should not raise


def test_program_set_validator_too_many_executables():
    device_action = {
        "braket.ir.openqasm.program_set": {"maximumTotalShots": 1000, "maximumExecutables": 2}
    }
    validator = ProgramSetValidator(device_action)
    program_set = ProgramSet(
        [Circuit().h(0), Circuit().x(0), Circuit().z(0)], shots_per_executable=100
    )
    with pytest.raises(ValueError):
        validator.validate(program_set)


def test_program_set_validator_too_many_shots():
    device_action = {
        "braket.ir.openqasm.program_set": {"maximumTotalShots": 100, "maximumExecutables": 10}
    }
    validator = ProgramSetValidator(device_action)
    program_set = ProgramSet([Circuit().h(0).cnot(0, 1)], shots_per_executable=200)
    with pytest.raises(ValueError):
        validator.validate(program_set)
