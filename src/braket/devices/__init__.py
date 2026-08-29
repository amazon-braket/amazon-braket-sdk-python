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

"""Provides a unified interface for interacting with quantum devices. It
includes the abstract Device base class, LocalSimulator for running circuits locally,
and the Devices enumeration for convenient access to available Amazon Braket devices.
"""

from braket.devices.device import Device  # ruff:ignore[unused-import]
from braket.devices.devices import Devices  # ruff:ignore[unused-import]
from braket.devices.local_simulator import LocalSimulator  # ruff:ignore[unused-import]
