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

"""Tests for the pulse control module."""

import textwrap

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm import pulse
from braket.experimental.autoqasm.instructions import h


def test_gate_calibrations():
    """test multiple gate calibrations"""

    @aq.calibration("h", (0,))
    def cal_1():
        pulse.barrier(0)

    @aq.calibration("h", (1,))
    def cal_2():
        pulse.delay(1, 0.123)

    @aq.main
    def my_program():
        h(0)
        h(1)

    expected = textwrap.dedent(
        """
        OPENQASM 3.0;
        defcal h __qubits__[0] {
            barrier $0;
        }
        defcal h __qubits__[1] {
            delay[123.0ms] $1;
        }
        qubit[2] __qubits__;
        h __qubits__[0];
        h __qubits__[1];
        """
    ).strip()
    qasm = my_program().bind_calibrations([cal_1(), cal_2()]).to_ir()
    assert qasm == expected
