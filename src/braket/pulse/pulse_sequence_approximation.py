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

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from braket.timings.time_series import TimeSeries


@dataclass
class PulseSequenceApproximation:
    """This class represents an approximation of a PulseSequence.

    Args:
        amplitudes (dict): A dictionary of frame ID to a TimeSeries of complex values specifying
            the waveform amplitude.
        frequencies (dict):A dictionary of frame ID to a TimeSeries of float values specifying
            the waveform frequency.
        phases (dict):A dictionary of frame ID to a TimeSeries of float values specifying
            the waveform phase.
    """

    amplitudes: Dict[str, TimeSeries]
    frequencies: Dict[str, TimeSeries]
    phases: Dict[str, TimeSeries]
