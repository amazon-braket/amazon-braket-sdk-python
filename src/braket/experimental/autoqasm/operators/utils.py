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


"Utility methods for operators."

from braket.circuits import FreeParameter
from braket.experimental.autoqasm import program
from braket.experimental.autoqasm import types as aq_types


def _convert_parameters(*args: list[FreeParameter]) -> list[aq_types.FloatVar]:
    """Converts FreeParameter objects to FloatVars through the program conversion context
    parameter registry.

    FloatVars are more compatible with the program conversion operations.

    Args:
        args (list[FreeParameter]): FreeParameter objects.

    Returns:
        list[FloatVar]: FloatVars for program conversion.
    """
    result = []
    for arg in args:
        if isinstance(arg, FreeParameter):
            var = program.get_program_conversion_context().get_parameter(arg.name)
            result.append(var)
        else:
            result.append(arg)
    return result[0] if len(result) == 1 else result
