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

from typing import Union

from ..parser.openqasm_ast import (
    FloatLiteral,
    GateModifierName,
    Identifier,
    IntegerLiteral,
    QuantumGate,
    QuantumGateModifier,
    QuantumPhase,
    QuantumStatement,
)


def invert_phase(phase: QuantumPhase) -> QuantumPhase:
    """Invert a quantum phase"""
    new_modifiers = [mod for mod in phase.modifiers if mod.modifier != GateModifierName.inv]
    new_param = FloatLiteral(-phase.argument.value)
    return QuantumPhase(new_modifiers, new_param, phase.qubits)


def is_inverted(quantum_op: Union[QuantumGate, QuantumPhase]) -> bool:
    """
    Tell whether a gate with modifiers is inverted, or if the inverse modifiers
    cancel out. Since inv @ ctrl U == ctrl @ inv U, we can accomplish this by
    only counting the inverse modifiers.
    """
    inv_modifier = QuantumGateModifier(GateModifierName.inv, None)
    num_inv_modifiers = quantum_op.modifiers.count(inv_modifier)
    return bool(num_inv_modifiers % 2)


def is_controlled(phase: QuantumPhase) -> bool:
    """
    Returns whether a quantum phase has any control modifiers. If it does, then
    it will be transformed by the interpreter into a controlled global phase gate.
    """
    for mod in phase.modifiers:
        if mod.modifier in (GateModifierName.ctrl, GateModifierName.negctrl):
            return True
    return False


def convert_phase_to_gate(controlled_phase: QuantumPhase) -> QuantumGate:
    """Convert a controlled quantum phase into a quantum gate"""
    ctrl_modifiers = get_ctrl_modifiers(controlled_phase.modifiers)
    first_ctrl_modifier = ctrl_modifiers[-1]
    if first_ctrl_modifier.modifier == GateModifierName.negctrl:
        raise ValueError("negctrl modifier undefined for gphase operation")
    if first_ctrl_modifier.argument.value == 1:
        ctrl_modifiers.pop()
    else:
        ctrl_modifiers[-1].argument.value -= 1
    return QuantumGate(
        ctrl_modifiers,
        Identifier("U"),
        [
            IntegerLiteral(0),
            IntegerLiteral(0),
            controlled_phase.argument,
        ],
        controlled_phase.qubits,
    )


def get_ctrl_modifiers(modifiers: list[QuantumGateModifier]) -> list[QuantumGateModifier]:
    """Get the control modifiers from a list of quantum gate modifiers"""
    return [
        mod
        for mod in modifiers
        if mod.modifier in (GateModifierName.ctrl, GateModifierName.negctrl)
    ]


def get_pow_modifiers(modifiers: list[QuantumGateModifier]) -> list[QuantumGateModifier]:
    """Get the power modifiers from a list of quantum gate modifiers"""
    return [mod for mod in modifiers if mod.modifier == GateModifierName.pow]


def modify_body(
    body: list[QuantumStatement],
    do_invert: bool,
    ctrl_modifiers: list[QuantumGateModifier],
    ctrl_qubits: list[Identifier],
    pow_modifiers: list[QuantumGateModifier],
) -> list[QuantumStatement]:
    """Apply modifiers information to the definition body of a quantum gate"""
    if do_invert:
        body = list(reversed(body))
        for s in body:
            s.modifiers.insert(0, QuantumGateModifier(GateModifierName.inv, None))
    for s in body:
        if isinstance(s, QuantumGate) or is_controlled(s):
            s.modifiers = ctrl_modifiers + pow_modifiers + s.modifiers
            s.qubits = ctrl_qubits + s.qubits
    return body
