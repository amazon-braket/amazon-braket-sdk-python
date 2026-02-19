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

"""Program sets efficiently run multiple quantum circuits in a single quantum task,
reducing overhead and enabling up to 24x faster execution. This module provides
ProgramSet for bundling circuits or parameter sets, CircuitBinding for circuit
configuration, and ParameterSets for managing parameter values.
"""

from braket.program_sets.circuit_binding import CircuitBinding  # noqa: F401
from braket.program_sets.parameter_sets import ParameterSets, ParameterSetsLike  # noqa: F401
from braket.program_sets.program_set import ProgramSet  # noqa: F401
