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

"""The local emulator allows you to emulate quantum programs locally before running
them on actual quantum hardware. This module provides Emulator and LocalEmulator
for device emulation, PassManager for applying transformation passes,
DeviceEmulatorProperties for calibration data, and ValidationPass and
TransformationPass base classes for custom passes.
"""

from braket.emulation.emulator import Emulator  # noqa: F401
from braket.emulation.pass_manager import PassManager  # noqa: F401
