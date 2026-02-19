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

"""The Braket SDK offers near real-time cost tracking for quantum workloads. This
module provides Tracker for monitoring quantum task costs and usage as a context
manager, Pricing for retrieving AWS pricing data, and TrackingContext for managing
tracker registration and event broadcasting.
"""

from braket.tracking.tracker import Tracker  # noqa: F401
