# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from braket.emulation.passes.generic.specification_validator import SpecificationValidator
from braket.program_sets import ProgramSet


def test_specification_validator_supported():
    validator = SpecificationValidator(Circuit | ProgramSet)
    circuit = Circuit().h(0)
    validator.validate(circuit)  # Should not raise
    ps = ProgramSet([Circuit().h(0)], shots_per_executable=100)
    validator.validate(ps)


def test_specification_validator_unsupported():
    validator = SpecificationValidator(Circuit)
    ps = ProgramSet([Circuit().h(0)], shots_per_executable=100)

    with pytest.raises(ValueError):
        validator.validate(ps)
