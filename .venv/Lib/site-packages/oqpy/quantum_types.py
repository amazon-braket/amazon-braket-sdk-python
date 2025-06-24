############################################################################
#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
############################################################################
"""Classes representing variables containing quantum types (i.e. Qubits)."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Iterator, Optional, Sequence, Union

from openpulse import ast
from openpulse.printer import dumps

from oqpy.base import AstConvertible, Var, make_annotations, to_ast
from oqpy.classical_types import AngleVar, _ClassicalVar

if TYPE_CHECKING:
    from oqpy.program import Program


__all__ = ["Qubit", "defcal", "gate", "PhysicalQubits", "Cal"]


class Qubit(Var):
    """OQpy variable representing a single qubit."""

    def __init__(
        self,
        name: str,
        size: Optional[int] = None,
        needs_declaration: bool = True,
        annotations: Sequence[str | tuple[str, str]] = (),
    ):
        super().__init__(name, needs_declaration=needs_declaration)
        self.name = name
        self.size = size
        self.annotations = annotations

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Qubit) and self.name == other.name

    def __lt__(self, other: Qubit) -> bool:
        return self.name < other.name

    def to_ast(self, prog: Program) -> ast.Expression:
        """Converts the OQpy variable into an ast node."""
        prog._add_var(self)
        return ast.Identifier(self.name)

    def make_declaration_statement(self, program: Program) -> ast.Statement:
        """Make an ast statement that declares the OQpy variable."""
        if self.size == 0:
            raise ValueError("The size of the qubit register cannot be zero.")
        decl = ast.QubitDeclaration(
            ast.Identifier(self.name),
            size=ast.IntegerLiteral(self.size) if self.size else None,
        )
        decl.annotations = make_annotations(self.annotations)
        return decl

    def __getitem__(self, index: AstConvertible) -> IndexedQubitArray:
        if self.size is None:
            raise TypeError(f"'{self.name}' is not subscriptable")
        return IndexedQubitArray(collection=self, index=index)


class PhysicalQubits:
    """Provides a means of accessing qubit variables corresponding to physical qubits.

    For example, the openqasm qubit "$3" is accessed by ``PhysicalQubits[3]``.
    """

    def __class_getitem__(cls, item: int) -> Qubit:
        assert isinstance(item, int)
        return Qubit(f"${item}", needs_declaration=False)


class IndexedQubitArray:
    """Represents an indexed qubit array."""

    def __init__(self, collection: Qubit, index: AstConvertible):
        self.collection = collection
        self.index = index

    def to_ast(self, program: Program) -> ast.IndexedIdentifier:
        """Converts this indexed qubit array into an ast node."""
        return ast.IndexedIdentifier(
            name=to_ast(program, self.collection), indices=[[to_ast(program, self.index)]]
        )


@contextlib.contextmanager
def gate(
    program: Program,
    qubits: Union[Qubit, list[Qubit]],
    name: str,
    arguments: Optional[list[AstConvertible]] = None,
    declare_here: bool = False,
) -> Union[Iterator[None], Iterator[list[AngleVar]], Iterator[AngleVar]]:
    """Context manager for creating a gate.

    .. code-block:: python

        with gate(program, q1, "HRzH", [AngleVar(name="theta")]) as theta:
            program.gate(q1, "H")
            program.gate(q1, "Rz", theta)
            program.gate(q1, "H")
    """
    if isinstance(qubits, Qubit):
        qubits = [qubits]

    arguments_ast = []
    variables = []
    if arguments is not None:
        for arg in arguments:
            if not isinstance(arg, AngleVar):
                raise ValueError(arg, "Gates only support args of type AngleVar.")
            arguments_ast.append(ast.Identifier(name=arg.name))
            arg._needs_declaration = False
            variables.append(arg)

    program._push()
    if len(variables) > 1:
        yield variables
    elif len(variables) == 1:
        yield variables[0]
    else:
        yield None
    state = program._pop()

    stmt = ast.QuantumGateDefinition(
        name=ast.Identifier(name),
        arguments=arguments_ast,
        qubits=[ast.Identifier(q.name) for q in qubits],
        body=state.body,
    )
    if declare_here:
        program._add_statement(stmt)
    program._add_gate(name, stmt, needs_declaration=not declare_here)


@contextlib.contextmanager
def defcal(
    program: Program,
    qubits: Union[Qubit, list[Qubit]],
    name: str,
    arguments: Optional[list[AstConvertible]] = None,
    return_type: Optional[ast.ClassicalType] = None,
) -> Union[Iterator[None], Iterator[list[_ClassicalVar]], Iterator[_ClassicalVar]]:
    """Context manager for creating a defcal.

    .. code-block:: python

        with defcal(program, q1, "X", [AngleVar(name="theta"), oqpy.pi/2], oqpy.bit) as theta:
            program.play(frame, waveform)
    """
    if isinstance(qubits, Qubit):
        qubits = [qubits]
    assert return_type is None or isinstance(return_type, ast.ClassicalType)

    arguments_ast = []
    variables = []
    if arguments is not None:
        for arg in arguments:
            if isinstance(arg, _ClassicalVar):
                arguments_ast.append(
                    ast.ClassicalArgument(type=arg.type, name=ast.Identifier(name=arg.name))
                )
                arg._needs_declaration = False
                variables.append(arg)
            else:
                arguments_ast.append(to_ast(program, arg))

    program._push()
    if len(variables) > 1:
        yield variables
    elif len(variables) == 1:
        yield variables[0]
    else:
        yield None
    state = program._pop()

    stmt = ast.CalibrationDefinition(
        ast.Identifier(name),
        arguments_ast,
        [ast.Identifier(q.name) for q in qubits],
        return_type,
        state.body,
    )
    program._add_statement(stmt)
    program._add_defcal(
        [qubit.name for qubit in qubits], name, [dumps(a) for a in arguments_ast], stmt
    )


@contextlib.contextmanager
def Cal(program: Program) -> Iterator[None]:
    """Context manager that begins a cal block."""
    program._push()
    yield
    state = program._pop()
    program._add_statement(ast.CalibrationStatement(state.body))
