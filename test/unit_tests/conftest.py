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

"""Shared pytest configuration for unit tests.

Forces matplotlib to use the non-interactive ``Agg`` backend before any
test imports matplotlib. This avoids failures on CI runners (notably
Windows hosted runners) where the default ``TkAgg`` backend cannot
initialise because Tcl/Tk is not properly installed in the Python
distribution used by the runner.
"""

import matplotlib

matplotlib.use("Agg")
