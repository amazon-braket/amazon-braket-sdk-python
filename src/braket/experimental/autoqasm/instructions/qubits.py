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


"""Utility functions that handle qubit construction and naming."""

import re
from functools import singledispatch
from typing import Any, Union

import oqpy.base
from openpulse.printer import dumps

from braket.experimental.autoqasm import constants, errors, program
from braket.parametric import FreeParameterExpression


def _get_physical_qubit_indices(qids: list[str]) -> list[int]:
    """Convert physical qubit labels to the corresponding qubit indices.

    Args:
        qids (list[str]): Physical qubit labels.

    Returns:
        list[int]: Qubit indices corresponding to the input physical qubits.
    """
    braket_qubits = []
    for qid in qids:
        if not (isinstance(qid, str) and re.match(r"\$\d+", qid)):
            raise ValueError(
                f"Invalid physical qubit label: '{qid}'. Physical qubit must be labeled as a string"
                "with '$' followed by an integer. For example: '$1'."
            )
        braket_qubits.append(int(qid[1:]))
    return braket_qubits


def _global_qubit_register(qubit_idx_expr: Union[int, str]) -> oqpy.Qubit:
    return oqpy.Qubit(f"{constants.QUBIT_REGISTER}[{qubit_idx_expr}]", needs_declaration=False)


@singledispatch
def _qubit(qid: Any) -> oqpy.Qubit:
    """Maps a given qubit representation to an oqpy qubit.

    Args:
        qid (Any): The qubit argument provided to a gate.

    Returns:
        Qubit: A translated oqpy qubit.
    """
    raise ValueError(f"invalid qubit label: '{qid}'")


@_qubit.register
def _(qid: bool) -> oqpy.Qubit:
    raise ValueError(f"invalid qubit label: '{qid}'")


@_qubit.register
def _(qid: float) -> oqpy.Qubit:
    raise TypeError(f"qubit index cannot be a float: '{qid}'")


@_qubit.register
def _(qid: int) -> oqpy.Qubit:
    # Integer virtual qubit, like `h(0)`
    program.get_program_conversion_context().register_qubit(qid)
    return _global_qubit_register(qid)


@_qubit.register
def _(qid: oqpy._ClassicalVar) -> oqpy.Qubit:
    # Indexed by variable, such as i in range(n); h(i)
    if program.get_program_conversion_context().get_declared_qubits() is None:
        raise errors.UnknownQubitCountError()
    return _global_qubit_register(qid.name)


@_qubit.register
def _(qid: oqpy.base.OQPyExpression) -> oqpy.Qubit:
    # Indexed by expression, such as i in range(n); h(i + 1)
    if program.get_program_conversion_context().get_declared_qubits() is None:
        raise errors.UnknownQubitCountError()

    oqpy_program = program.get_program_conversion_context().get_oqpy_program()
    qubit_idx_expr = dumps(qid.to_ast(oqpy_program))
    return _global_qubit_register(qubit_idx_expr)


@_qubit.register
def _(qid: str) -> oqpy.Qubit:
    # Physical qubit label, like `h("$0")`
    if qid.startswith("$"):
        qubit_idx = qid[1:]
        try:
            qubit_idx = int(qubit_idx)
        except ValueError:
            raise ValueError(f"invalid physical qubit label: '{qid}'")
        return oqpy.PhysicalQubits[qubit_idx]
    else:
        raise ValueError(f"invalid qubit label: '{qid}'")


@_qubit.register
def _(qid: FreeParameterExpression) -> oqpy.Qubit:
    # Unbound expression dependent on input, like `h(q)` where q is unbound
    int_var = oqpy.IntVar(
        name=str(qid),
        needs_declaration=False,
        size=32,
    )
    return _qubit(int_var)


@_qubit.register
def _(qid: oqpy.Qubit) -> oqpy.Qubit:
    return qid
