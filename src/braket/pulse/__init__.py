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

"""Pulses are the analog signals that control the qubits in a quantum computer.
With pulse control, you can submit circuits using pulses for fine-grained
control over qubit operations. This module provides Frame and Port for
defining control channels, PulseSequence for building pulse programs,
waveform classes for signal envelopes, and PulseSequenceTrace for
execution trace data.
"""

from braket.pulse.frame import Frame  # noqa: F401
from braket.pulse.port import Port  # noqa: F401
from braket.pulse.pulse_sequence import PulseSequence  # noqa: F401
from braket.pulse.waveforms import (
    ArbitraryWaveform,  # noqa: F401
    ConstantWaveform,  # noqa: F401
    DragGaussianWaveform,  # noqa: F401
    ErfSquareWaveform,  # noqa: F401
    GaussianWaveform,  # noqa: F401
)
