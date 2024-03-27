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

"""Pulse programming is a level of programming that controls qubits or frames at a lower level than
gates, such as playing a waveform or shifting the frequency of a frame. This module includes
instructions for pulse programming. A program can have only pulse instructions, or mixed usage of
pulse and gate instructions, if the device supports it. Pulse programming can also be used to define
the calibration of gates in a program.

Example of a program that uses only pulse instructions:

.. code-block:: python

    @aq.main
    def my_pulse_program():
        pulse.shift_frequency(frame, 123)
        pulse.delay([3, 4], 0.34)
"""

from .pulse import *  # noqa: F401, F403
