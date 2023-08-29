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

"""AutoQASM tests exercising device-specific targeting functionality.
"""

from typing import Any

import pytest

import braket.experimental.autoqasm as aq
from braket.aws import AwsDevice
from braket.devices import Devices
from braket.experimental.autoqasm import errors
from braket.experimental.autoqasm.instructions import h


@pytest.mark.parametrize(
    "device_parameter", [None, Devices.Amazon.SV1, AwsDevice(Devices.Amazon.SV1)]
)
def test_device_parameter(device_parameter: Any) -> None:
    @aq.main(device=device_parameter)
    def my_program():
        h(0)

    program = my_program()
    assert program.to_ir()


def test_insufficient_qubits() -> None:
    @aq.main(device=Devices.Amazon.SV1, num_qubits=35)
    def my_program():
        pass

    with pytest.raises(errors.InsufficientQubitCountError):
        my_program()
