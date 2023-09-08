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

"""AutoQASM supported pragmas.

Pragmas specify how a program should be compiled or executed. In AutoQASM, we support them via
`with` statements. For example:

.. code-block:: python

    @aq.main
    def pragma_example() -> None:
        with aq.verbatim():
            h(0)
            cnot(0, 1)
        x(0)

The verbatim pragma would then apply to the `h` and `cnot`, but not the `x`.
"""


import contextlib

import oqpy.base

from braket.experimental.autoqasm import program


@contextlib.contextmanager
def verbatim() -> None:
    """Context management protocol that, when used with a `with` statement, wraps the code block
    in a verbatim box.

    The verbatim pragma around a code block specifies that operations are to be executed as
    programmed without compilation or modification of any sort.
    """
    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    oqpy_program.pragma("braket verbatim")
    with oqpy.Box(oqpy_program):
        yield