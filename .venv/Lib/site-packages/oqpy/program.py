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
"""Module containing Program and related classes.

This module contains the oqpy.Program class, which is the primary user interface
for constructing openqasm/openpulse. The class follows the builder pattern in that
it contains a representation of the state of a program (internally represented as
AST components), and the class has methods which add to the current state.
"""

from __future__ import annotations

import warnings
from copy import deepcopy
from typing import Any, Hashable, Iterable, Iterator, Optional

from openpulse import ast
from openpulse.printer import dumps
from openqasm3.visitor import QASMVisitor

from oqpy import classical_types, quantum_types
from oqpy.base import (
    AstConvertible,
    OQPyExpression,
    Var,
    expr_matches,
    map_to_ast,
    optional_ast,
    to_ast,
)
from oqpy.pulse import FrameVar, PortVar, WaveformVar
from oqpy.timing import convert_duration_to_float, convert_float_to_duration

__all__ = ["Program"]


class ProgramState:
    """Represents the current program state at a particular context level.

    A new ProgramState is created every time a context (such as the control
    flow constructs If/Else/ForIn/While) is created. A program will retain a
    stack of ProgramState objects for all currently open contexts.
    """

    def __init__(self) -> None:
        self.body: list[ast.Statement | ast.Pragma] = []
        self.if_clause: Optional[ast.BranchingStatement] = None
        self.annotations: list[ast.Annotation] = []

    def add_if_clause(self, condition: ast.Expression, if_clause: list[ast.Statement]) -> None:
        if_clause_annotations, self.annotations = self.annotations, []
        self.finalize_if_clause()
        self.if_clause = ast.BranchingStatement(condition, if_clause, [])
        self.if_clause.annotations = if_clause_annotations

    def add_else_clause(self, else_clause: list[ast.Statement]) -> None:
        if self.if_clause is None:
            raise RuntimeError("Else without If.")
        self.if_clause.else_block = else_clause
        self.finalize_if_clause()

    def finalize_if_clause(self) -> None:
        if self.if_clause is not None:
            if_clause, self.if_clause = self.if_clause, None
            self.add_statement(if_clause)

    def add_statement(self, stmt: ast.Statement | ast.Pragma) -> None:
        # This function accepts Statement and Pragma even though
        # it seems to conflict with the definition of ast.Program.
        # Issue raised in https://github.com/openqasm/openqasm/issues/468
        assert isinstance(stmt, (ast.Statement, ast.Pragma))
        if isinstance(stmt, ast.Statement) and self.annotations:
            stmt.annotations = self.annotations + list(stmt.annotations)
            self.annotations = []
        self.finalize_if_clause()
        self.body.append(stmt)


class Program:
    """A builder class for OpenQASM/OpenPulse programs."""

    DURATION_MAX_DIGITS = 12

    def __init__(self, version: Optional[str] = "3.0", simplify_constants: bool = True) -> None:
        self.stack: list[ProgramState] = [ProgramState()]
        self.defcals: dict[
            tuple[tuple[str, ...], str, tuple[str, ...]], ast.CalibrationDefinition
        ] = {}
        self.subroutines: dict[str, ast.SubroutineDefinition] = {}
        self.gates: dict[str, ast.QuantumGateDefinition] = {}
        self.externs: dict[str, ast.ExternDeclaration] = {}
        self.declared_vars: dict[str, Var] = {}
        self.undeclared_vars: dict[str, Var] = {}
        self.simplify_constants = simplify_constants
        self.declared_subroutines: set[str] = set()
        self.declared_gates: set[str] = set()
        self.expr_cache: dict[Hashable, ast.Expression] = {}
        """A cache of ast made by CachedExpressionConvertible objects used in this program.

        This is used by `to_ast` to avoid repetitively evaluating ast conversion methods.
        """

        if version is None or (
            len(version.split(".")) in [1, 2]
            and all([item.isnumeric() for item in version.split(".")])
        ):
            self.version = version
        else:
            raise RuntimeError("Version number does not match the X[.y] format.")

    def __iadd__(self, other: Program) -> Program:
        """In-place concatenation of programs."""
        if len(other.stack) > 1:
            raise RuntimeError("Cannot add subprogram with unclosed contextmanagers.")
        self._state.finalize_if_clause()
        self._state.body.extend(other._state.body)
        self._state.if_clause = other._state.if_clause
        self._state.annotations.extend(other._state.annotations)
        self._state.finalize_if_clause()
        self.defcals.update(other.defcals)
        for name, subroutine_stmt in other.subroutines.items():
            self._add_subroutine(
                name, subroutine_stmt, needs_declaration=name not in other.declared_subroutines
            )
        for name, gate_stmt in other.gates.items():
            self._add_gate(name, gate_stmt, needs_declaration=name not in other.declared_gates)
        self.externs.update(other.externs)
        for var in other.declared_vars.values():
            self._mark_var_declared(var)
        for var in other.undeclared_vars.values():
            self._add_var(var)
        return self

    def __add__(self, other: Program) -> Program:
        """Return concatenation of two programs."""
        assert isinstance(other, Program)
        self_copy = deepcopy(self)
        self_copy += other
        return self_copy

    @property
    def _state(self) -> ProgramState:
        """The current program state is found on the top of the stack."""
        return self.stack[-1]

    @property
    def frame_vars(self) -> Iterator[FrameVar]:
        """Returns an Iterator of any declared/undeclared FrameVar used in the program."""
        for v in {**self.declared_vars, **self.undeclared_vars}.values():
            if isinstance(v, FrameVar):
                yield v

    @property
    def waveform_vars(self) -> Iterator[WaveformVar]:
        """Returns an Iterator of any declared/undeclared WaveformVar used in the program."""
        for v in {**self.declared_vars, **self.undeclared_vars}.values():
            if isinstance(v, WaveformVar):
                yield v

    def _push(self) -> None:
        """Open a new context by pushing a new program state on the stack."""
        self.stack.append(ProgramState())

    def _pop(self) -> ProgramState:
        """Close a context by removing the program state from the top stack, and return it."""
        state = self.stack.pop()
        state.finalize_if_clause()
        if state.annotations:
            warnings.warn(f"Annotation(s) {state.annotations} not applied to any statement")
        return state

    def _add_var(self, var: Var) -> None:
        """Register a variable with the program.

        If the variable is not declared (and is specified to need declaration),
        the variable will be automatically declared at the top of the program
        upon conversion to ast.

        This method is safe to call on the same variable multiple times.
        """
        name = var.name
        existing_var = self.declared_vars.get(name)
        if existing_var is None:
            existing_var = self.undeclared_vars.get(name)
        if (
            existing_var is not None
            and var is not existing_var
            and not expr_matches(var, existing_var)
        ):
            raise RuntimeError(f"Program has conflicting variables with name {name}")
        if name not in self.declared_vars:
            self.undeclared_vars[name] = var

    def _mark_var_declared(self, var: Var) -> None:
        """Indicate that a variable has been declared."""
        self._add_var(var)
        name = var.name
        new_var = self.undeclared_vars.pop(name, None)
        if new_var is not None:
            self.declared_vars[name] = new_var

    def autodeclare(self, encal: bool = False) -> None:
        """Declare any currently undeclared variables at the beginning of the program."""
        while any(v._needs_declaration for v in self.undeclared_vars.values()):
            self.declare(
                [var for var in self.undeclared_vars.values() if var._needs_declaration],
                to_beginning=True,
                encal=encal,
            )

    def _add_statement(self, stmt: ast.Statement) -> None:
        """Add a statment to the current context's program state."""
        self._state.add_statement(stmt)

    def _add_subroutine(
        self, name: str, stmt: ast.SubroutineDefinition, needs_declaration: bool = True
    ) -> None:
        """Register a subroutine which has been used.

        Subroutines are added to the top of the program upon conversion to ast.
        """
        self.subroutines[name] = stmt
        if not needs_declaration:
            self.declared_subroutines.add(name)

    def _add_gate(
        self, name: str, stmt: ast.QuantumGateDefinition, needs_declaration: bool = True
    ) -> None:
        """Register a gate definition which has been used.

        Gate definitions are added to the top of the program upon conversion to ast.
        """
        self.gates[name] = stmt
        if not needs_declaration:
            self.declared_gates.add(name)

    def _add_defcal(
        self,
        qubit_names: list[str],
        name: str,
        arguments: list[str],
        stmt: ast.CalibrationDefinition,
    ) -> None:
        """Register a defcal defined in this program.

        Defcals are added to the top of the program upon conversion to ast.
        """
        self.defcals[(tuple(qubit_names), name, tuple(arguments))] = stmt

    def _make_externs_statements(self, auto_encal: bool = False) -> list[ast.ExternDeclaration]:
        """Return a list of extern statements for inclusion at beginning of program.

        if auto_encal is True, any externs using openpulse types will be wrapped in a Cal block.
        """
        if not auto_encal:
            return list(self.externs.values())
        openqasm_externs, openpulse_externs = [], []
        openpulse_types = ast.PortType, ast.FrameType, ast.WaveformType
        for extern_statement in self.externs.values():
            for arg in extern_statement.arguments:
                if isinstance(arg.type, openpulse_types):
                    openpulse_externs.append(extern_statement)
                    break
            else:
                if isinstance(extern_statement.return_type, openpulse_types):
                    openpulse_externs.append(extern_statement)
                else:
                    openqasm_externs.append(extern_statement)
        if openpulse_externs:
            openqasm_externs.append(ast.CalibrationStatement(body=openpulse_externs))
        return openqasm_externs

    def to_ast(
        self,
        encal: bool = False,
        include_externs: bool = True,
        ignore_needs_declaration: bool = False,
        encal_declarations: bool = False,
    ) -> ast.Program:
        """Convert to an AST program.

        Args:
            encal: If true, wrap all statements in a "Cal" block, ensuring
                that all openpulse statements are contained within a Cal block.
            include_externs: If true, for all used extern statements, include
                an extern declaration at the top of the program.
            ignore_needs_declaration: If true, the field `_needs_declaration` of
                undeclared variables is ignored and their declaration will not
                be added to the AST
            encal_declarations: If true, when declaring undeclared variables,
                if the variables have openpulse types, automatically wrap the
                declarations in cal blocks.
        """
        mutating_prog = Program(self.version, self.simplify_constants)
        mutating_prog += self

        if not ignore_needs_declaration and mutating_prog.undeclared_vars:
            mutating_prog.autodeclare(encal=encal_declarations)

        assert len(mutating_prog.stack) == 1
        mutating_prog._state.finalize_if_clause()
        if mutating_prog._state.annotations:
            warnings.warn(
                f"Annotation(s) {mutating_prog._state.annotations} not applied to any statement"
            )
        statements = []
        if include_externs:
            statements += mutating_prog._make_externs_statements(encal_declarations)
        statements += (
            [
                mutating_prog.subroutines[subroutine_name]
                for subroutine_name in mutating_prog.subroutines
                if subroutine_name not in mutating_prog.declared_subroutines
            ]
            + [
                mutating_prog.gates[gate_name]
                for gate_name in mutating_prog.gates
                if gate_name not in mutating_prog.declared_gates
            ]
            + mutating_prog._state.body
        )
        if encal:
            statements = [ast.CalibrationStatement(statements)]
        if encal_declarations:
            statements = [ast.CalibrationGrammarDeclaration("openpulse")] + statements
        prog = ast.Program(statements=statements, version=mutating_prog.version)
        if encal_declarations:
            MergeCalStatementsPass().visit(prog)
        return prog

    def to_qasm(
        self,
        encal: bool = False,
        include_externs: bool = True,
        ignore_needs_declaration: bool = False,
        encal_declarations: bool = False,
    ) -> str:
        """Convert to QASM text.

        See to_ast for option documentation.
        """
        return dumps(
            self.to_ast(
                encal=encal,
                include_externs=include_externs,
                ignore_needs_declaration=ignore_needs_declaration,
                encal_declarations=encal_declarations,
            ),
            indent="    ",
        ).strip()

    def declare(
        self,
        variables: list[Var] | Var,
        to_beginning: bool = False,
        encal: bool = False,
    ) -> Program:
        """Declare a variable.

        Args:
            variables: A list of variables to declare, or a single variable to declare.
            to_beginning: If true, insert the declaration at the beginning of the program,
                instead of at the current point.
            encal: If true, wrap any declarations of undeclared variables with openpulse
                types in a cal block.
        """
        if isinstance(variables, (classical_types._ClassicalVar, quantum_types.Qubit)):
            variables = [variables]

        assert isinstance(variables, list)

        openpulse_vars, openqasm_vars = [], []
        for var in variables:
            if encal and isinstance(var, (PortVar, FrameVar, WaveformVar)):
                openpulse_vars.append(var)
            else:
                openqasm_vars.append(var)

        if to_beginning:
            openqasm_vars.reverse()

        for var in openqasm_vars:
            if callable(var) and hasattr(var, "subroutine_declaration"):
                name, stmt = var.subroutine_declaration
                self._add_subroutine(name, stmt, needs_declaration=False)
            else:
                stmt = var.make_declaration_statement(self)
                self._mark_var_declared(var)

            if to_beginning:
                self._state.body.insert(0, stmt)
            else:
                self._add_statement(stmt)

        if openpulse_vars:
            cal_stmt = ast.CalibrationStatement([])
            for var in openpulse_vars:
                stmt = var.make_declaration_statement(self)
                cal_stmt.body.append(stmt)
                self._mark_var_declared(var)
            if to_beginning:
                self._state.body.insert(0, cal_stmt)
            else:
                self._add_statement(cal_stmt)
        return self

    def delay(
        self, time: AstConvertible, qubits_or_frames: AstConvertible | Iterable[AstConvertible] = ()
    ) -> Program:
        """Apply a delay to a set of qubits or frames."""
        if not isinstance(qubits_or_frames, Iterable):
            qubits_or_frames = [qubits_or_frames]
        ast_duration = to_ast(self, convert_float_to_duration(time, require_nonnegative=True))
        ast_qubits_or_frames = map_to_ast(self, qubits_or_frames)
        self._add_statement(ast.DelayInstruction(ast_duration, ast_qubits_or_frames))
        return self

    def barrier(self, qubits_or_frames: Iterable[AstConvertible]) -> Program:
        """Apply a barrier to a set of qubits or frames."""
        ast_qubits_or_frames = map_to_ast(self, qubits_or_frames)
        self._add_statement(ast.QuantumBarrier(ast_qubits_or_frames))
        return self

    def function_call(
        self,
        name: str,
        args: Iterable[AstConvertible],
        assigns_to: AstConvertible = None,
    ) -> None:
        """Add a function call with an optional output assignment."""
        function_call_node = ast.FunctionCall(ast.Identifier(name), map_to_ast(self, args))
        if assigns_to is None:
            self.do_expression(function_call_node)
        else:
            self._do_assignment(to_ast(self, assigns_to), "=", function_call_node)

    def play(self, frame: AstConvertible, waveform: AstConvertible) -> Program:
        """Play a waveform on a particular frame."""
        self.function_call("play", [frame, waveform])
        return self

    def capture(self, frame: AstConvertible, kernel: AstConvertible) -> Program:
        """Capture signal integrated against a kernel on a particular frame."""
        self.function_call("capture", [frame, kernel])
        return self

    def set_phase(self, frame: AstConvertible, phase: AstConvertible) -> Program:
        """Set the phase of a particular frame."""
        # We use make_float to force phase to be a unitless (i.e. non-duration) quantity.
        # Users are expected to keep track the units that are not expressible in openqasm
        # such as s^{-1}. For instance, in 2 * oqpy.pi * tppi * DurationVar(1e-8),
        # tppi is a float but has a frequency unit. This will coerce the result type
        # to a float by assuming the duration should be represented in seconds."
        self.function_call("set_phase", [frame, convert_duration_to_float(phase)])
        return self

    def shift_phase(self, frame: AstConvertible, phase: AstConvertible) -> Program:
        """Shift the phase of a particular frame."""
        self.function_call("shift_phase", [frame, convert_duration_to_float(phase)])
        return self

    def set_frequency(self, frame: AstConvertible, freq: AstConvertible) -> Program:
        """Set the frequency of a particular frame."""
        self.function_call("set_frequency", [frame, convert_duration_to_float(freq)])
        return self

    def shift_frequency(self, frame: AstConvertible, freq: AstConvertible) -> Program:
        """Shift the frequency of a particular frame."""
        self.function_call("shift_frequency", [frame, convert_duration_to_float(freq)])
        return self

    def set_scale(self, frame: AstConvertible, scale: AstConvertible) -> Program:
        """Set the amplitude scaling of a particular frame."""
        self.function_call("set_scale", [frame, convert_duration_to_float(scale)])
        return self

    def shift_scale(self, frame: AstConvertible, scale: AstConvertible) -> Program:
        """Shift the amplitude scaling of a particular frame."""
        self.function_call("shift_scale", [frame, convert_duration_to_float(scale)])
        return self

    def returns(self, expression: AstConvertible) -> Program:
        """Return a statement from a function definition or a defcal statement."""
        self._add_statement(ast.ReturnStatement(to_ast(self, expression)))
        return self

    def _create_modifiers_ast(
        self,
        control: quantum_types.Qubit | Iterable[quantum_types.Qubit] | None,
        neg_control: quantum_types.Qubit | Iterable[quantum_types.Qubit] | None,
        inv: bool,
        exp: AstConvertible,
    ) -> tuple[list[ast.QuantumGateModifier], list[AstConvertible]]:
        """Create the AST for the gate modifiers."""
        used_qubits: list[AstConvertible] = []
        modifiers: list[ast.QuantumGateModifier] = []

        control = control if control is not None else []
        control = {control} if isinstance(control, quantum_types.Qubit) else set(control)
        if control:
            modifiers.append(
                ast.QuantumGateModifier(
                    modifier=ast.GateModifierName.ctrl,
                    argument=to_ast(self, len(control)) if len(control) > 1 else None,
                )
            )
            used_qubits.extend(sorted(control))

        neg_control = neg_control if neg_control is not None else []
        neg_control = (
            {neg_control} if isinstance(neg_control, quantum_types.Qubit) else set(neg_control)
        )
        if neg_control:
            modifiers.append(
                ast.QuantumGateModifier(
                    modifier=ast.GateModifierName.negctrl,
                    argument=to_ast(self, len(neg_control)) if len(neg_control) > 1 else None,
                )
            )
            for qubit in sorted(neg_control):
                if qubit in used_qubits:
                    raise ValueError(f"Qubit {qubit} has already been defined as a control qubit.")
                else:
                    used_qubits.append(qubit)

        if inv:
            modifiers.append(
                ast.QuantumGateModifier(
                    modifier=ast.GateModifierName.inv,
                )
            )

        if isinstance(exp, OQPyExpression) or (isinstance(exp, float) and exp != 1.0):
            modifiers.append(
                ast.QuantumGateModifier(
                    modifier=ast.GateModifierName.pow, argument=to_ast(self, exp)
                )
            )
        return modifiers, used_qubits

    def gate(
        self,
        qubits: AstConvertible | Iterable[AstConvertible],
        name: str,
        *args: Any,
        control: quantum_types.Qubit | Iterable[quantum_types.Qubit] | None = None,
        neg_control: quantum_types.Qubit | Iterable[quantum_types.Qubit] | None = None,
        inv: bool = False,
        exp: AstConvertible = 1,
    ) -> Program:
        """Apply a gate with its modifiers to a qubit or set of qubits.

        Args:
            qubits (AstConvertible | Iterable[AstConvertible]): The qubit or list of qubits
                to which the gate will be applied
            name (str): The gate name
            *args (Any): A list of parameters passed to the gate
            control (quantum_types.Qubit | Iterable[quantum_types.Qubit] | None): The list
                of control qubits (default: None)
            neg_control: (quantum_types.Qubit | Iterable[quantum_types.Qubit] | None): The list
                of negative control qubits (default: None)
            inv (bool): Flag to use the inverse gate (default: False)
            exp (AstConvertible): The exponent used with `pow` gate modifier

        Returns:
            Program: The OQpy program to which the gate is added
        """
        modifiers, used_qubits = self._create_modifiers_ast(control, neg_control, inv, exp)

        if isinstance(qubits, (quantum_types.Qubit, quantum_types.IndexedQubitArray)):
            qubits = [qubits]
        assert isinstance(qubits, Iterable)

        for qubit in qubits:
            if qubit in used_qubits:
                raise ValueError(
                    f"Qubit {qubit} has already been defined as a control qubit or a negative control qubit."
                )
            else:
                used_qubits.append(qubit)

        self._add_statement(
            ast.QuantumGate(
                modifiers,
                ast.Identifier(name),
                map_to_ast(self, args),
                map_to_ast(self, used_qubits),
            )
        )
        return self

    def reset(self, qubit: quantum_types.Qubit) -> Program:
        """Reset a particular qubit."""
        self._add_statement(ast.QuantumReset(qubits=qubit.to_ast(self)))
        return self

    def measure(
        self, qubit: quantum_types.Qubit, output_location: classical_types.BitVar | None = None
    ) -> Program:
        """Measure a particular qubit.

        If provided, store the result in the given output location.
        """
        self._add_statement(
            ast.QuantumMeasurementStatement(
                measure=ast.QuantumMeasurement(ast.Identifier(qubit.name)),
                target=optional_ast(self, output_location),
            )
        )
        return self

    def pragma(self, command: str) -> Program:
        """Add a pragma instruction."""
        if len(self.stack) != 1:
            raise RuntimeError("Pragmas must be global")
        self._add_statement(ast.Pragma(command))
        return self

    def include(self, path: str) -> Program:
        """Add an include statement."""
        if len(self.stack) != 1:
            # cf. https://openqasm.com/language/comments.html#included-files
            raise RuntimeError("Include statements must be global")
        self._add_statement(ast.Include(path))
        return self

    def _do_assignment(self, var: AstConvertible, op: str, value: AstConvertible) -> None:
        """Helper function for variable assignment operations."""
        if isinstance(var, classical_types.DurationVar):
            value = convert_float_to_duration(value)
        var_ast = to_ast(self, var)
        if isinstance(var_ast, ast.IndexExpression):
            assert isinstance(var_ast.collection, ast.Identifier)
            var_ast = ast.IndexedIdentifier(name=var_ast.collection, indices=[var_ast.index])
        self._add_statement(
            ast.ClassicalAssignment(
                var_ast,
                ast.AssignmentOperator[op],
                to_ast(self, value),
            )
        )

    def do_expression(self, expression: AstConvertible) -> Program:
        """Add a statement which evaluates a given expression without assigning the output."""
        self._add_statement(ast.ExpressionStatement(to_ast(self, expression)))
        return self

    def set(
        self,
        var: classical_types._ClassicalVar | classical_types.OQIndexExpression,
        value: AstConvertible,
    ) -> Program:
        """Set a variable value."""
        self._do_assignment(var, "=", value)
        return self

    def increment(self, var: classical_types._ClassicalVar, value: AstConvertible) -> Program:
        """Increment a variable value."""
        self._do_assignment(var, "+=", value)
        return self

    def decrement(self, var: classical_types._ClassicalVar, value: AstConvertible) -> Program:
        """Decrement a variable value."""
        self._do_assignment(var, "-=", value)
        return self

    def mod_equals(self, var: classical_types.IntVar, value: AstConvertible) -> Program:
        """In-place update of a variable to be itself modulo value."""
        assert isinstance(var, classical_types.IntVar)
        self._do_assignment(var, "%=", value)
        return self

    def annotate(self, keyword: str, command: Optional[str] = None) -> Program:
        """Add an annotation to the next statement."""
        self._state.annotations.append(ast.Annotation(keyword, command))
        return self


class MergeCalStatementsPass(QASMVisitor[None]):
    """Merge adjacent CalibrationStatement ast nodes."""

    def visit_Program(self, node: ast.Program, context: None = None) -> None:
        node.statements = self.process_statement_list(node.statements)
        self.generic_visit(node, context)

    def visit_ForInLoop(self, node: ast.ForInLoop, context: None = None) -> None:
        node.block = self.process_statement_list(node.block)
        self.generic_visit(node, context)

    def visit_WhileLoop(self, node: ast.WhileLoop, context: None = None) -> None:
        node.block = self.process_statement_list(node.block)
        self.generic_visit(node, context)

    def visit_BranchingStatement(self, node: ast.BranchingStatement, context: None = None) -> None:
        node.if_block = self.process_statement_list(node.if_block)
        node.else_block = self.process_statement_list(node.else_block)
        self.generic_visit(node, context)

    def visit_CalibrationStatement(
        self, node: ast.CalibrationStatement, context: None = None
    ) -> None:
        node.body = self.process_statement_list(node.body)
        self.generic_visit(node, context)

    def visit_SubroutineDefinition(
        self, node: ast.SubroutineDefinition, context: None = None
    ) -> None:
        node.body = self.process_statement_list(node.body)
        self.generic_visit(node, context)

    def process_statement_list(
        self, statements: list[ast.Statement | ast.Pragma]
    ) -> list[ast.Statement | ast.Pragma]:
        new_list = []
        cal_stmts = []
        for stmt in statements:
            if isinstance(stmt, ast.CalibrationStatement):
                cal_stmts.extend(stmt.body)
            else:
                if cal_stmts:
                    new_list.append(ast.CalibrationStatement(body=cal_stmts))
                    cal_stmts = []
                new_list.append(stmt)

        if cal_stmts:
            new_list.append(ast.CalibrationStatement(body=cal_stmts))

        return new_list
