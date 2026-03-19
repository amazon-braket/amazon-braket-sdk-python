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

"""Provides classes for representing time-dependent data used in pulse
sequences and analog Hamiltonian simulations. It provides TimeSeries for defining
values that vary over time and TimeSeriesItem for individual time-value pairs.
"""

from braket.timings.time_series import TimeSeries, TimeSeriesItem  # noqa: F401
