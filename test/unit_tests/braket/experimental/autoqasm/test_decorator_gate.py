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

"""AutoQASM tests exercising the @aq.gate decorator and related functionality.
"""

import braket.experimental.autoqasm as aq


def test_empty_gate() -> None:
    @aq.gate
    def my_gate():
        pass

    @aq.function
    def my_program():
        my_gate()

    my_program()
