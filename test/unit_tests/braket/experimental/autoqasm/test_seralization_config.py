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

"""Tests for serialization configuration."""

import textwrap

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.program import OpenqasmSerializationConfig
from braket.experimental.autoqasm.pulse import barrier, play
from braket.pulse import Frame, GaussianWaveform, Port

PORT = Port(port_id="device_port_x0", dt=1e-9, properties={})
FRAME = Frame(frame_id="predefined_frame_1", frequency=2e9, port=PORT, phase=0, is_predefined=True)
WAVEFORM = GaussianWaveform(4e-3, 0.3, 0.7, True, "wf_dg")


def test_openqasm_serialization_config_auto_defcalgrammar() -> None:
    """Tests serializing with defcalgrammar on top."""

    @aq.main
    def my_program():
        barrier("$0")

    expected_true = textwrap.dedent(
        """
        OPENQASM 3.0;
        defcalgrammar "openpulse";
        cal {
            barrier $0;
        }
        """
    ).strip()
    qasm = my_program().to_ir(
        serialization_config=OpenqasmSerializationConfig(auto_defcalgrammar=True)
    )
    assert qasm == expected_true

    expected_false = textwrap.dedent(
        """
        OPENQASM 3.0;
        cal {
            barrier $0;
        }
        """
    ).strip()
    qasm = my_program().to_ir(
        serialization_config=OpenqasmSerializationConfig(auto_defcalgrammar=False)
    )
    assert qasm == expected_false


def test_openqasm_serialization_config_include_externs() -> None:
    """Tests serializing with extern definition."""

    @aq.main
    def my_program():
        play(FRAME, WAVEFORM)

    expected_true = textwrap.dedent(
        """
        OPENQASM 3.0;
        cal {
            extern gaussian(duration, duration, float[64], bool) -> waveform;
            waveform wf_dg = gaussian(4.0ms, 300.0ms, 0.7, true);
            play(predefined_frame_1, wf_dg);
        }
        """
    ).strip()
    qasm = my_program().to_ir(
        serialization_config=OpenqasmSerializationConfig(include_externs=True)
    )
    assert qasm == expected_true

    expected_false = textwrap.dedent(
        """
        OPENQASM 3.0;
        cal {
            waveform wf_dg = gaussian(4.0ms, 300.0ms, 0.7, true);
            play(predefined_frame_1, wf_dg);
        }
        """
    ).strip()
    qasm = my_program().to_ir(
        serialization_config=OpenqasmSerializationConfig(include_externs=False)
    )
    assert qasm == expected_false
