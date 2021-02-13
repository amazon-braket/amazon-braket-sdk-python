# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from typing import Iterable
import braket.ir.jaqcd as ir
from braket.circuits import circuit
from braket.circuits.instruction import Instruction
from braket.circuits.classical_operation import ClassicalOperation

class PreservedRegionEnd(ClassicalOperation):

    def __init__(self):
        super().__init__()

    def to_ir(self, target):
        return ir.PreservedRegionEnd.construct()

    @staticmethod
    @circuit.subroutine(register=True)
    def end_preserved_region() -> Iterable[Instruction]:

        return [Instruction(ClassicalOperation.PreservedRegionEnd())]

ClassicalOperation.register_operation(PreservedRegionEnd)

class PreservedRegionStart(ClassicalOperation):

    def __init__(self):
        super().__init__()

    def to_ir(self, target):
        return ir.PreservedRegionStart.construct()

    @staticmethod
    @circuit.subroutine(register=True)
    def start_preserved_region() -> Iterable[Instruction]:

        return [Instruction(ClassicalOperation.PreservedRegionStart())]

ClassicalOperation.register_operation(PreservedRegionStart)


