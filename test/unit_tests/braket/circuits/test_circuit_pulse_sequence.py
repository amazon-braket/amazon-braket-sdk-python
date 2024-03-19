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

import io
import json
from unittest.mock import Mock, patch

import numpy as np
import pytest

from braket.aws import AwsDevice
from braket.circuits import (
    Circuit,
    CircuitPulseSequenceBuilder,
    FreeParameter,
    Gate,
    Instruction,
    Observable,
    Operator,
)
from braket.pulse import Frame, Port, PulseSequence

from ..aws.common_test_utils import RIGETTI_ARN
from ..aws.test_aws_device import MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_1, get_pulse_model

# from braket.circuits.gate_calibrations import GateCalibrations


# @patch("urllib.request.urlopen")
# @pytest.fixture
# def device(mock_url_request):
#     response_data_content = {
#         "gates": {
#             "0_1": {
#                 "cphaseshift": [
#                     {
#                         "name": "cphaseshift",
#                         "qubits": ["0", "1"],
#                         "arguments": ["-1.5707963267948966"],
#                         "calibrations": [
#                             {
#                                 "name": "play",
#                                 "arguments": [
#                                     {
#                                         "name": "waveform",
#                                         "value": "wf_drag_gaussian_0",
#                                         "type": "waveform",
#                                     },
#                                     {
#                                         "name": "frame",
#                                         "value": "q0_q1_cphase_frame",
#                                         "type": "frame",
#                                     },
#                                 ],
#                             },
#                         ],
#                     }
#                 ],
#                 "rx_12": [{"name": "rx_12", "qubits": ["0"]}],
#             },
#         },
#         "waveforms": {
#             "wf_drag_gaussian_0": {
#                 "waveformId": "wf_drag_gaussian_0",
#                 "name": "drag_gaussian",
#                 "arguments": [
#                     {"name": "length", "value": 6.000000000000001e-8, "type": "float"},
#                     {"name": "sigma", "value": 6.369913502160144e-9, "type": "float"},
#                     {"name": "amplitude", "value": -0.4549282253548838, "type": "float"},
#                     {"name": "beta", "value": 7.494904522022295e-10, "type": "float"},
#                 ],
#             },
#         },
#     }

#     response_data_stream = io.BytesIO(json.dumps(response_data_content).encode("utf-8"))
#     mock_url_request.return_value.__enter__.return_value = response_data_stream
#     mock_session = Mock()
#     mock_session.get_device.return_value = get_pulse_model(
#         MOCK_PULSE_MODEL_QPU_PULSE_CAPABILITIES_JSON_1
#     )
#     device = AwsDevice(RIGETTI_ARN, mock_session)
#     return device


@pytest.fixture()
def gate_calibrations(device):
    return device.gate_calibrations


def test_empty_circuit():
    assert CircuitPulseSequenceBuilder(None).build_pulse_sequence(Circuit()) == PulseSequence()


def test_non_parametric_defcal(gate_calibrations):
    circ = Circuit().rx(0, np.pi)
    expected = (
        "OPENQASM 3.0;",
        "cal {",
        "    bit[1] psb;",
        "    waveform wf_drag_gaussian_3 = drag_gaussian(24.0ns, 2.547965400864ns, 2.3223415460834803e-10, 0.606950905462208, false);",
        "    barrier $0;",
        "    shift_frequency(q0_rf_frame, -321047.14178613486);",
        "    play(q0_rf_frame, wf_drag_gaussian_3);",
        "    shift_frequency(q0_rf_frame, 321047.14178613486);",
        "    barrier $0;",
        "    psb[0] = capture_v0(q0_ro_rx_frame);",
        "}",
    )

    assert circ.pulse_sequence(gate_calibrations).to_ir() == expected


def test_parametric_defcal(gate_calibrations):
    circ = Circuit().xy(0, 1, 0.1)
    expected = (
        "OPENQASM 3.0;",
        "cal {",
        "    bit[1] psb;",
        "    waveform wf_drag_gaussian_3 = drag_gaussian(24.0ns, 2.547965400864ns, 2.3223415460834803e-10, 0.606950905462208, false);",
        "    barrier $0;",
        "    shift_frequency(q0_rf_frame, -321047.14178613486);",
        "    play(q0_rf_frame, wf_drag_gaussian_3);",
        "    shift_frequency(q0_rf_frame, 321047.14178613486);",
        "    barrier $0;",
        "    psb[0] = capture_v0(q0_ro_rx_frame);",
        "}",
    )

    assert circ.pulse_sequence(gate_calibrations).to_ir() == expected
