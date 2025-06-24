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

from abc import ABC, abstractmethod
from collections.abc import Iterable
from functools import singledispatchmethod
from typing import Any, Optional, Union

import numpy as np
from sympy import Expr

from braket.default_simulator.gate_operations import BRAKET_GATES, GPhase, Unitary
from braket.default_simulator.noise_operations import (
    AmplitudeDamping,
    BitFlip,
    Depolarizing,
    GeneralizedAmplitudeDamping,
    Kraus,
    PauliChannel,
    PhaseDamping,
    PhaseFlip,
    TwoQubitDephasing,
    TwoQubitDepolarizing,
)
from braket.ir.jaqcd.program_v1 import Results

from ._helpers.arrays import (
    convert_discrete_set_to_list,
    convert_range_def_to_slice,
    flatten_indices,
    get_elements,
    get_type_width,
    update_value,
)
from ._helpers.casting import LiteralType, get_identifier_name, is_none_like
from .circuit import Circuit
from .parser.braket_pragmas import parse_braket_pragma
from .parser.openqasm_ast import (
    ClassicalType,
    FloatLiteral,
    GateModifierName,
    Identifier,
    IndexedIdentifier,
    IndexElement,
    IntegerLiteral,
    QuantumGateDefinition,
    QuantumGateModifier,
    RangeDefinition,
    SubroutineDefinition,
)


class Table:
    """
    Utility class for storing and displaying items.
    """

    def __init__(self, title: str):
        self._title = title
        self._dict = {}

    def __getitem__(self, item: str):
        return self._dict[item]

    def __contains__(self, item: str):
        return item in self._dict

    def __setitem__(self, key: str, value: Any):
        self._dict[key] = value

    def items(self) -> Iterable[tuple[str, Any]]:
        return self._dict.items()

    def _longest_key_length(self) -> int:
        items = self.items()
        return max(len(key) for key, value in items) if items else None

    def __repr__(self):
        rows = [self._title]
        longest_key_length = self._longest_key_length()
        for item, value in self.items():
            rows.append(f"{item:<{longest_key_length}}\t{value}")
        return "\n".join(rows)


class QubitTable(Table):
    def __init__(self):
        super().__init__("Qubits")

    @singledispatchmethod
    def get_by_identifier(self, identifier: Union[Identifier, IndexedIdentifier]) -> tuple[int]:
        """
        Convenience method to get an element with a possibly indexed identifier.
        """
        if identifier.name.startswith("$"):
            return (int(identifier.name[1:]),)
        return self[identifier.name]

    @get_by_identifier.register
    def _(self, identifier: IndexedIdentifier) -> tuple[int]:
        """
        When identifier is an IndexedIdentifier, function returns a tuple
        corresponding to the elements referenced by the indexed identifier.
        """
        name = identifier.name.name
        primary_index = identifier.indices[0]

        def validate_qubit_in_range(qubit: int):
            if qubit >= len(self[name]):
                raise IndexError(
                    f"qubit register index `{qubit}` out of range for qubit register of length {len(self[name])} `{name}`."
                )

        if isinstance(primary_index, list):
            if len(primary_index) != 1:
                raise IndexError("Cannot index multiple dimensions for qubits.")
            primary_index = primary_index[0]
        if isinstance(primary_index, IntegerLiteral):
            validate_qubit_in_range(primary_index.value)
            target = (self[name][primary_index.value],)
        elif isinstance(primary_index, RangeDefinition):
            target = tuple(np.array(self[name])[convert_range_def_to_slice(primary_index)])
        # Discrete set
        else:
            indices = convert_discrete_set_to_list(primary_index)
            for index in indices:
                validate_qubit_in_range(index)
            target = tuple(np.array(self[name])[indices])

        if len(identifier.indices) == 1:
            return target
        elif len(identifier.indices) == 2:
            # used for gate calls on registers, index will be IntegerLiteral
            secondary_index = identifier.indices[1][0].value
            return (target[secondary_index],)
        else:
            raise IndexError("Cannot index multiple dimensions for qubits.")

    def get_qubit_size(self, identifier: Union[Identifier, IndexedIdentifier]) -> int:
        return len(self.get_by_identifier(identifier))


class ScopedTable(Table):
    """
    Scoped version of Table
    """

    def __init__(self, title):
        super().__init__(title)
        self._scopes = [{}]

    def push_scope(self) -> None:
        self._scopes.append({})

    def pop_scope(self) -> None:
        self._scopes.pop()

    @property
    def in_global_scope(self):
        return len(self._scopes) == 1

    @property
    def current_scope(self) -> dict[str, Any]:
        return self._scopes[-1]

    def __getitem__(self, item: str):
        """
        Resolve scope of item and return its value.
        """
        for scope in reversed(self._scopes):
            if item in scope:
                return scope[item]
        raise KeyError(f"Undefined key: {item}")

    def __setitem__(self, key: str, value: Any):
        """
        Set value of item in current scope.
        """
        try:
            self.get_scope(key)[key] = value
        except KeyError:
            self.current_scope[key] = value

    def __delitem__(self, key: str):
        """
        Delete item from first scope in which it exists.
        """
        for scope in reversed(self._scopes):
            if key in scope:
                del scope[key]
                return
        raise KeyError(f"Undefined key: {key}")

    def get_scope(self, key: str) -> dict[str, Any]:
        """Get the smallest scope containing the given key"""
        for scope in reversed(self._scopes):
            if key in scope:
                return scope
        raise KeyError(f"Undefined key: {key}")

    def items(self) -> Iterable[tuple[str, Any]]:
        items = {}
        for scope in reversed(self._scopes):
            for key, value in scope.items():
                if key not in items:
                    items[key] = value
        return items.items()

    def __repr__(self):
        rows = [self._title]
        longest_key_length = self._longest_key_length()
        for level, scope in enumerate(self._scopes):
            rows.append(f"SCOPE LEVEL {level}")
            for item, value in scope.items():
                rows.append(f"{item:<{longest_key_length}}\t{value}")
        return "\n".join(rows)


class SymbolTable(ScopedTable):
    """
    Scoped table used to map names to types.
    """

    class Symbol:
        def __init__(
            self,
            symbol_type: Union[ClassicalType, LiteralType],
            const: bool = False,
        ):
            self.type = symbol_type
            self.const = const

        def __repr__(self):
            return f"Symbol<{self.type}, const={self.const}>"

    def __init__(self):
        super().__init__("Symbols")

    def add_symbol(
        self,
        name: str,
        symbol_type: Union[ClassicalType, LiteralType, type[Identifier]],
        const: bool = False,
    ) -> None:
        """
        Add a symbol to the symbol table.

        Args:
            name (str): Name of the symbol.
            symbol_type (Union[ClassicalType, LiteralType]): Type of the symbol. Symbols can
                have a literal type when they are a numeric argument to a gate or an integer
                literal loop variable.
            const (bool): Whether the variable is immutable.
        """
        self.current_scope[name] = SymbolTable.Symbol(symbol_type, const)

    def get_symbol(self, name: str) -> Symbol:
        """
        Get a symbol from the symbol table by name.

        Args:
            name (str): Name of the symbol.

        Returns:
            Symbol: The symbol object.
        """
        return self[name]

    def get_type(self, name: str) -> Union[ClassicalType, type[LiteralType]]:
        """
        Get the type of a symbol by name.

        Args:
            name (str): Name of the symbol.

        Returns:
            Union[ClassicalType, LiteralType]: The type of the symbol.
        """
        return self.get_symbol(name).type

    def get_const(self, name: str) -> bool:
        """
        Get const status of a symbol by name.

        Args:
            name (str): Name of the symbol.

        Returns:
            bool: Whether the symbol is a const symbol.
        """
        return self.get_symbol(name).const


class VariableTable(ScopedTable):
    """
    Scoped table used store values for symbols. This implements the classical memory for
    the Interpreter.
    """

    def __init__(self):
        super().__init__("Data")

    def add_variable(self, name: str, value: Any) -> None:
        self.current_scope[name] = value

    def get_value(self, name: str) -> LiteralType:
        return self[name]

    @singledispatchmethod
    def get_value_by_identifier(
        self, identifier: Identifier, type_width: Optional[IntegerLiteral] = None
    ) -> LiteralType:
        """
        Convenience method to get value with a possibly indexed identifier.
        """
        return self[identifier.name]

    @get_value_by_identifier.register
    def _(
        self, identifier: IndexedIdentifier, type_width: Optional[IntegerLiteral] = None
    ) -> LiteralType:
        """
        When identifier is an IndexedIdentifier, function returns an ArrayLiteral
        corresponding to the elements referenced by the indexed identifier.
        """
        name = identifier.name.name
        value = self[name]
        indices = flatten_indices(identifier.indices)
        return get_elements(value, indices, type_width)

    def update_value(
        self,
        name: str,
        value: Any,
        var_type: ClassicalType,
        indices: Optional[list[IndexElement]] = None,
    ) -> None:
        """Update value of a variable, optionally providing an index"""
        current_value = self[name]
        if indices:
            value = update_value(current_value, value, flatten_indices(indices), var_type)
        self[name] = value

    def is_initalized(self, name: str) -> bool:
        """Determine whether a declared variable is initialized"""
        return not is_none_like(self[name])


class GateTable(ScopedTable):
    """
    Scoped table to implement gates.
    """

    def __init__(self):
        super().__init__("Gates")

    def add_gate(self, name: str, definition: QuantumGateDefinition) -> None:
        self[name] = definition

    def get_gate_definition(self, name: str) -> QuantumGateDefinition:
        return self[name]


class SubroutineTable(ScopedTable):
    """
    Scoped table to implement subroutines.
    """

    def __init__(self):
        super().__init__("Subroutines")

    def add_subroutine(self, name: str, definition: SubroutineDefinition) -> None:
        self[name] = definition

    def get_subroutine_definition(self, name: str) -> SubroutineDefinition:
        return self[name]


class ScopeManager:
    """
    Allows ProgramContext to manage scope with `with` keyword.
    """

    def __init__(self, context: "ProgramContext"):
        self.context = context

    def __enter__(self):
        self.context.push_scope()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context.pop_scope()


class AbstractProgramContext(ABC):
    """
    Interpreter state.

    Symbol table - symbols in scope
    Variable table - variable values
    Gate table - gate definitions
    Subroutine table - subroutine definitions
    Qubit mapping - mapping from logical qubits to qubit indices

    Circuit - IR build to hand off to the simulator
    """

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.variable_table = VariableTable()
        self.gate_table = GateTable()
        self.subroutine_table = SubroutineTable()
        self.qubit_mapping = QubitTable()
        self.scope_manager = ScopeManager(self)
        self.inputs = {}
        self.num_qubits = 0

    @property
    @abstractmethod
    def circuit(self):
        """The circuit being built in this context."""

    def __repr__(self):
        return "\n\n".join(
            repr(x)
            for x in (self.symbol_table, self.variable_table, self.gate_table, self.qubit_mapping)
        )

    def load_inputs(self, inputs: dict[str, Any]) -> None:
        """
        Load inputs for the circuit

        Args:
            inputs (dict[str, Any]): A dictionary containing the inputs to be loaded
        """
        for key, value in inputs.items():
            self.inputs[key] = value

    def parse_pragma(self, pragma_body: str):
        """
        Parse pragma

        Args:
            pragma_body (str): The body of the pragma statement.
        """
        return parse_braket_pragma(pragma_body, self.qubit_mapping)

    def declare_variable(
        self,
        name: str,
        symbol_type: Union[ClassicalType, type[LiteralType], type[Identifier]],
        value: Optional[Any] = None,
        const: bool = False,
    ) -> None:
        """
        Declare variable in current scope

        Args:
            name (str): The name of the variable
            symbol_type(Union[ClassicalType, type[LiteralType], type[Identifier]]): The type of the variable.
            value (Optional[Any]): The initial value of the variable . Defaults to None.
            const (bool): Flag indicating if the variable is constant. Defaults to False.
        """
        self.symbol_table.add_symbol(name, symbol_type, const)
        self.variable_table.add_variable(name, value)

    def declare_qubit_alias(
        self,
        name: str,
        value: Identifier,
    ) -> None:
        """
        Declare qubit alias in current scope

        Args:
            name(str): The name of the qubit alias.
            value(Identifier): The identifier representing the qubit
        """
        self.symbol_table.add_symbol(name, Identifier)
        self.variable_table.add_variable(name, value)

    def enter_scope(self) -> ScopeManager:
        """
        Allows pushing/popping scope with indentation and the `with` keyword.

        Usage:
        # inside the original scope
        ...
        with program_context.enter_scope():
            # inside a new scope
            ...
        # exited new scope, back in the original scope
        """
        return self.scope_manager

    def push_scope(self) -> None:
        """Enter a new scope"""
        self.symbol_table.push_scope()
        self.variable_table.push_scope()
        self.gate_table.push_scope()

    def pop_scope(self) -> None:
        """Exit current scope"""
        self.symbol_table.pop_scope()
        self.variable_table.pop_scope()
        self.gate_table.pop_scope()

    @property
    def in_global_scope(self):
        return self.symbol_table.in_global_scope

    def get_type(self, name: str) -> Union[ClassicalType, type[LiteralType]]:
        """
        Get symbol type by name

        Args:
            name (str): The name of the symbol.

        Returns:
            Union[ClassicalType, type[LiteralType]]: The type of the symbol.
        """
        return self.symbol_table.get_type(name)

    def get_const(self, name: str) -> bool:
        """
        Get whether a symbol is const by name"

        Args:
            name (str): The name of the symbol.

        Returns:
            bool: True of the symbol os const, False otherwise.
        """
        return self.symbol_table.get_const(name)

    def get_value(self, name: str) -> LiteralType:
        """
        Get value of a variable by name

        Args:
            name(str): The name of the variable.

        Returns:
            LiteralType: The value of the variable.

        Raises:
            KeyError: If the variable is not found.
        """
        return self.variable_table.get_value(name)

    def get_value_by_identifier(
        self, identifier: Union[Identifier, IndexedIdentifier]
    ) -> LiteralType:
        """
        Get value of a variable by identifier

        Args:
            identifier (Union[Identifier, IndexedIdentifier]): The identifier of the variable.

        Returns:
            LiteralType: The value of the variable.

        Raises:
            KeyError: If the variable is not found.
        """
        # find type width for the purpose of bitwise operations
        var_type = self.get_type(get_identifier_name(identifier))
        type_width = get_type_width(var_type)
        return self.variable_table.get_value_by_identifier(identifier, type_width)

    def is_initialized(self, name: str) -> bool:
        """
        Check whether variable is initialized by name

        Args:
            name (str): The name of the variable.

        Returns:
            bool: True if the variable is initialized, False otherwise.
        """
        return self.variable_table.is_initalized(name)

    def update_value(self, variable: Union[Identifier, IndexedIdentifier], value: Any) -> None:
        """
        Update value by identifier, possible only a sub-index of a variable

        Args:
            variable (Union[Identifier, IndexedIdentifier]): The identifier of the variable.
            value (Any): The new value of the variable.
        """
        name = get_identifier_name(variable)
        var_type = self.get_type(name)
        indices = variable.indices if isinstance(variable, IndexedIdentifier) else None
        self.variable_table.update_value(name, value, var_type, indices)

    def add_qubits(self, name: str, num_qubits: Optional[int] = 1) -> None:
        """
        Allocate additional qubits for the circuit

        Args:
            name(str): The name of the qubit register
            num_qubits (Optional[int]): The number of qubits to allocate. Default is 1.
        """
        self.qubit_mapping[name] = tuple(range(self.num_qubits, self.num_qubits + num_qubits))
        self.num_qubits += num_qubits
        self.declare_qubit_alias(name, Identifier(name))

    def get_qubits(self, qubits: Union[Identifier, IndexedIdentifier]) -> tuple[int]:
        """
        Get qubit indices from a qubit identifier, possibly referring to a sub-index of
        a qubit register

        Args:
            qubits (Union[Identifier, IndexedIdentifier]): The identifier of the qubits.

        Returns:
            tuple[int]: The indices of the qubits.

        Raises:
            KeyError: If the qubit identifier is not found.
        """
        return self.qubit_mapping.get_by_identifier(qubits)

    def add_gate(self, name: str, definition: QuantumGateDefinition) -> None:
        """
        Add a gate definition

        Args:
            name(str): The name of the gate.
            definition (QuantumGateDefinition): The definition of the gate.
        """
        self.gate_table.add_gate(name, definition)

    def get_gate_definition(self, name: str) -> QuantumGateDefinition:
        """
        Get a gate definition by name

        Args:
            name (str): The name of the gate.

        Returns:
            QuantumGateDefinition: The definition of the gate.

        Raises:
            ValueError: If the gate is not defined.
        """
        try:
            return self.gate_table.get_gate_definition(name)
        except KeyError:
            raise ValueError(f"Gate {name} is not defined.")

    def is_user_defined_gate(self, name: str) -> bool:
        """
        Check whether the gate is user-defined gate

        Args:
            name (str): The name of the gate.

        Returns:
            bool: True of the gate is user-defined, False otherwise.
        """
        try:
            self.get_gate_definition(name)
            return True
        except ValueError:
            return False

    @abstractmethod
    def is_builtin_gate(self, name: str) -> bool:
        """
        Abstract method to check if the gate with the given name is currently in scope as a built-in Braket gate.
        Args:
            name (str): name of the built-in Braket gate to be checked
        Returns:
            bool: True if the gate is a built-in gate, False otherwise.
        """

    def add_subroutine(self, name: str, definition: SubroutineDefinition) -> None:
        """
        Add a subroutine definition

        Args:
            name(str): The name of the subroutine.
            definition (SubroutineDefinition): The definition of the subroutine.
        """
        self.subroutine_table.add_subroutine(name, definition)

    def get_subroutine_definition(self, name: str) -> SubroutineDefinition:
        """
        Get a subroutine definition by name

        Args:
            name (str): The name of the subroutine.

        Returns:
            SubroutineDefinition: The definition of the subroutine.

        Raises:
            NameError: If the subroutine with the give name is not defined.
        """
        try:
            return self.subroutine_table.get_subroutine_definition(name)
        except KeyError:
            raise NameError(f"Subroutine {name} is not defined.")

    def add_result(self, result: Results) -> None:
        """
        Abstract method to add result type to the circuit

        Args:
            result (Results): The result object representing the measurement results
        """
        raise NotImplementedError

    def add_phase(
        self,
        phase: FloatLiteral,
        qubits: Optional[list[Union[Identifier, IndexedIdentifier]]] = None,
    ) -> None:
        """Add quantum phase instruction to the circuit"""
        # if targets overlap, duplicates will be ignored
        target = set(sum((self.get_qubits(q) for q in qubits), ())) if qubits else []
        self.add_phase_instruction(target, phase.value)

    @abstractmethod
    def add_phase_instruction(self, target, phase_value):
        """
        Abstract method to add phase instruction to the circuit

        Args:
            target (int or list[int]): The target qubit or qubits to which the phase instruction is applied
            phase_value (float): The phase value to be applied
        """

    def add_builtin_gate(
        self,
        gate_name: str,
        parameters: list[FloatLiteral],
        qubits: list[Union[Identifier, IndexedIdentifier]],
        modifiers: Optional[list[QuantumGateModifier]] = None,
    ) -> None:
        """
        Add a builtin gate instruction to the circuit

        Args:
            gate_name (str): The name of the built-in gate.
            parameters (list[FloatLiteral]): The list of the gate parameters.
            qubits (list[Union[Identifier, IndexedIdentifier]]): The list of qubits the gate acts on.
            modifiers (Optional[list[QuantumGateModifier]]): The list of gate modifiers (optional).
        """
        target = sum(((*self.get_qubits(qubit),) for qubit in qubits), ())
        params = np.array([self.handle_parameter_value(param.value) for param in parameters])
        num_inv_modifiers = modifiers.count(QuantumGateModifier(GateModifierName.inv, None))
        power = 1
        if num_inv_modifiers % 2:
            power *= -1  # todo: replace with adjoint

        ctrl_mod_map = {
            GateModifierName.negctrl: 0,
            GateModifierName.ctrl: 1,
        }
        ctrl_modifiers = []
        for mod in modifiers:
            ctrl_mod_ix = ctrl_mod_map.get(mod.modifier)
            if ctrl_mod_ix is not None:
                ctrl_modifiers += [ctrl_mod_ix] * mod.argument.value
            if mod.modifier == GateModifierName.pow:
                power *= mod.argument.value
        self.add_gate_instruction(
            gate_name, target, params, ctrl_modifiers=ctrl_modifiers, power=power
        )

    def handle_parameter_value(self, value: Union[float, Expr]) -> Any:
        """Convert parameter value to required format. Default conversion is noop.
        Args:
            value (Union[float, Expr]): Value of the parameter
        """
        if isinstance(value, Expr):
            return value.evalf()
        return value

    @abstractmethod
    def add_gate_instruction(
        self, gate_name: str, target: tuple[int, ...], params, ctrl_modifiers: list[int], power: int
    ):
        """Abstract method to add Braket gate to the circuit.
        Args:
            gate_name (str): name of the built-in Braket gate.
            target (tuple[int]): control_qubits + target_qubits.
            ctrl_modifiers (list[int]): Quantum state on which to control the
                operation. Must be a binary sequence of same length as number of qubits in
                `control-qubits` in target. For example "0101", [0, 1, 0, 1], 5 all represent
                controlling on qubits 0 and 2 being in the \\|0⟩ state and qubits 1 and 3 being
                in the \\|1⟩ state.
            power(float): Integer or fractional power to raise the gate to.
        """

    def add_custom_unitary(
        self,
        unitary: np.ndarray,
        target: tuple[int, ...],
    ) -> None:
        """Abstract method to add a custom Unitary instruction to the circuit
        Args:
            unitary (np.ndarray): unitary matrix
            target (tuple[int, ...]): control_qubits + target_qubits
        """
        raise NotImplementedError

    def add_noise_instruction(
        self, noise_instruction: str, target: list[int], probabilities: list[float]
    ):
        """Abstract method to add a noise instruction to the circuit

        Args:
            noise_instruction (str): The name of the noise operation
            target (list[int]): The target qubit or qubits to which the noise operation is applied.
            probabilities (list[float]): The probabilities associated with each possible outcome
                of the noise operation.
        """
        raise NotImplementedError

    def add_kraus_instruction(self, matrices: list[np.ndarray], target: list[int]):
        """Abstract method to add a Kraus instruction to the circuit

        Args:
            matrices (list[ndarray]): The matrices defining the Kraus operation
            target (list[int]): The target qubit or qubits to which the Kraus operation is applied.
        """
        raise NotImplementedError

    def add_measure(self, target: tuple[int], classical_targets: Iterable[int] = None):
        """Add qubit targets to be measured"""


class ProgramContext(AbstractProgramContext):
    def __init__(self, circuit: Optional[Circuit] = None):
        """
        Args:
            circuit (Optional[Circuit]): A partially-built circuit to continue building with this
                context. Default: None.
        """
        super().__init__()
        self._circuit = circuit or Circuit()

    @property
    def circuit(self):
        return self._circuit

    def is_builtin_gate(self, name: str) -> bool:
        user_defined_gate = self.is_user_defined_gate(name)
        return name in BRAKET_GATES and not user_defined_gate

    def add_phase_instruction(self, target: tuple[int], phase_value: int):
        phase_instruction = GPhase(target, phase_value)
        self._circuit.add_instruction(phase_instruction)

    def add_gate_instruction(
        self, gate_name: str, target: tuple[int, ...], params, ctrl_modifiers: list[int], power: int
    ):
        instruction = BRAKET_GATES[gate_name](
            target, *params, ctrl_modifiers=ctrl_modifiers, power=power
        )
        self._circuit.add_instruction(instruction)

    def add_custom_unitary(
        self,
        unitary: np.ndarray,
        target: tuple[int, ...],
    ) -> None:
        instruction = Unitary(target, unitary)
        self._circuit.add_instruction(instruction)

    def add_noise_instruction(
        self, noise_instruction: str, target: list[int], probabilities: list[float]
    ):
        one_prob_noise_map = {
            "bit_flip": BitFlip,
            "phase_flip": PhaseFlip,
            "pauli_channel": PauliChannel,
            "depolarizing": Depolarizing,
            "two_qubit_depolarizing": TwoQubitDepolarizing,
            "two_qubit_dephasing": TwoQubitDephasing,
            "amplitude_damping": AmplitudeDamping,
            "generalized_amplitude_damping": GeneralizedAmplitudeDamping,
            "phase_damping": PhaseDamping,
        }
        self._circuit.add_instruction(one_prob_noise_map[noise_instruction](target, *probabilities))

    def add_kraus_instruction(self, matrices: list[np.ndarray], target: list[int]):
        self._circuit.add_instruction(Kraus(target, matrices))

    def add_result(self, result: Results) -> None:
        self._circuit.add_result(result)

    def add_measure(self, target: tuple[int], classical_targets: Iterable[int] = None):
        self._circuit.add_measure(target, classical_targets)
