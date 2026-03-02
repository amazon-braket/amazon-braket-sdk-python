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

"""You can define a circuit with gates that depend on free parameters and specify
the values of these parameters when submitting the circuit as a quantum task.
This module provides FreeParameter for defining symbolic parameters,
FreeParameterExpression for mathematical expressions, and Parameterizable
interface for parameter binding.
"""

from braket.parametric.free_parameter import FreeParameter  # noqa: F401
from braket.parametric.free_parameter_expression import FreeParameterExpression  # noqa: F401
from braket.parametric.parameterizable import Parameterizable  # noqa: F401
