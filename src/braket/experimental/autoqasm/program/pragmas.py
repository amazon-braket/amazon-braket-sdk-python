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

from __future__ import annotations

import contextlib
from enum import Enum
from typing import Iterable, Optional

from braket.device_schema import DeviceActionType
from braket.experimental.autoqasm import errors, program


class PragmaType(str, Enum):
    """Values used in pragma statements."""

    VERBATIM = "braket verbatim"
    """Denotes a box as a verbatim block."""


@contextlib.contextmanager
def verbatim(annotations: Optional[str | Iterable[str]] = None) -> None:
    """Context management protocol that, when used with a `with` statement, wraps the code block
    in a verbatim block.

    A verbatim block specifies that operations contained within the block are to be executed as
    programmed without compilation or modification of any sort.

    Args:
        annotations (Optional[str | Iterable[str]]): Annotations for the box.

    Raises:
        errors.VerbatimBlockNotAllowed: If a verbatim block is not allowed at this point in
            the program; for example, if the target device does not support verbatim blocks.
    """
    program_conversion_context = program.get_program_conversion_context()

    if program_conversion_context.in_verbatim_block:
        raise errors.VerbatimBlockNotAllowed("Verbatim blocks cannot be nested.")

    device = program_conversion_context.get_target_device()
    if device:
        supported_pragmas = device.properties.action[DeviceActionType.OPENQASM].supportedPragmas
        if "verbatim" not in supported_pragmas:
            raise errors.VerbatimBlockNotAllowed(
                f'The target device "{device.name}" does not support verbatim blocks.'
            )

    try:
        with program.get_program_conversion_context().box(
            pragma=PragmaType.VERBATIM, annotations=annotations
        ):
            program_conversion_context.in_verbatim_block = True
            yield
    finally:
        program_conversion_context.in_verbatim_block = False
