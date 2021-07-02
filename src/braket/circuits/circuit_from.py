# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import re
from typing import List

import numpy as np

import braket.circuits.circuit as circuit
from braket.circuits.circuit import Circuit
from braket.circuits.gate import Gate
from braket.circuits.instruction import Instruction
from braket.circuits.noise import Noise
from braket.circuits.observable import Observable
from braket.circuits.qubit import Qubit
from braket.circuits.qubit_set import QubitSet
from braket.circuits.result_type import ResultType
from braket.ir.jaqcd import Program

# All Circuit objects indexed by ASCII Symbols
# as required by from_ir, from_repr and from_diagram

obj_class_defs = {
    "Circuit": Circuit,
    "Instruction": Instruction,
    "Qubit": Qubit,
    "QubitSet": QubitSet,
}

gate_defs = {
    # Zero arguments
    "I": {"op": Gate.I, "args": []},
    "X": {"op": Gate.X, "args": []},
    "Y": {"op": Gate.Y, "args": []},
    "Z": {"op": Gate.Z, "args": []},
    "H": {"op": Gate.H, "args": []},
    "S": {"op": Gate.S, "args": []},
    "Si": {"op": Gate.Si, "args": []},
    "T": {"op": Gate.T, "args": []},
    "Ti": {"op": Gate.Ti, "args": []},
    "V": {"op": Gate.V, "args": []},
    "Vi": {"op": Gate.Vi, "args": []},
    "Swap": {"op": Gate.Swap, "args": []},
    "SWAP": {"op": Gate.Swap, "args": []},
    "ISwap": {"op": Gate.ISwap, "args": []},
    "ISWAP": {"op": Gate.ISwap, "args": []},
    "CNot": {"op": Gate.CNot, "args": []},
    "CX": {"op": Gate.CNot, "args": []},
    "CY": {"op": Gate.CY, "args": []},
    "CZ": {"op": Gate.CZ, "args": []},
    "CSwap": {"op": Gate.CSwap, "args": []},
    "CSWAP": {"op": Gate.CSwap, "args": []},
    "CCNot": {"op": Gate.CCNot, "args": []},
    "CCX": {"op": Gate.CCNot, "args": []},
    # Single argument
    "Rx": {"op": Gate.Rx, "args": [""]},
    "Ry": {"op": Gate.Ry, "args": [""]},
    "Rz": {"op": Gate.Rz, "args": [""]},
    "PhaseShift": {"op": Gate.PhaseShift, "args": [""]},
    "PHASE": {"op": Gate.PhaseShift, "args": [""]},
    "CPhaseShift": {"op": Gate.CPhaseShift, "args": [""]},
    "CPHASE": {"op": Gate.CPhaseShift, "args": [""]},
    "CPhaseShift00": {"op": Gate.CPhaseShift00, "args": [""]},
    "CPHASE00": {"op": Gate.CPhaseShift00, "args": [""]},
    "CPhaseShift01": {"op": Gate.CPhaseShift01, "args": [""]},
    "CPHASE01": {"op": Gate.CPhaseShift01, "args": [""]},
    "CPhaseShift10": {"op": Gate.CPhaseShift10, "args": [""]},
    "CPHASE10": {"op": Gate.CPhaseShift10, "args": [""]},
    "XX": {"op": Gate.XX, "args": [""]},
    "XY": {"op": Gate.XY, "args": [""]},
    "YY": {"op": Gate.YY, "args": [""]},
    "ZZ": {"op": Gate.ZZ, "args": [""]},
    "PSwap": {"op": Gate.PSwap, "args": [""]},
    "PSWAP": {"op": Gate.PSwap, "args": [""]},
    "BitFlip": {"op": Noise.BitFlip, "args": [""]},
    "BF": {"op": Noise.BitFlip, "args": [""]},
    "PhaseFlip": {"op": Noise.PhaseFlip, "args": [""]},
    "PF": {"op": Noise.PhaseFlip, "args": [""]},
    "PhaseDamping": {"op": Noise.PhaseDamping, "args": [""]},
    "PD": {"op": Noise.PhaseDamping, "args": [""]},
    "AmplitudeDamping": {"op": Noise.AmplitudeDamping, "args": [""]},
    "AD": {"op": Noise.AmplitudeDamping, "args": [""]},
    "TwoQubitDephasing": {"op": Noise.TwoQubitDephasing, "args": [""]},
    "DEPH": {"op": Noise.TwoQubitDephasing, "args": [""]},
    "Depolarizing": {"op": Noise.Depolarizing, "args": [""], "alt_op": Noise.TwoQubitDepolarizing},
    "DEPO": {"op": Noise.Depolarizing, "args": [""], "alt_op": Noise.TwoQubitDepolarizing},
    "TwoQubitDepolarizing": {"op": Noise.TwoQubitDepolarizing, "args": ["", ""]},
    # Multiple arguments
    "PauliChannel": {"op": Noise.PauliChannel, "args": ["probX", "probY", "probZ"]},
    "PC": {"op": Noise.PauliChannel, "args": ["probX", "probY", "probZ"]},
    "GeneralizedAmplitudeDamping": {
        "op": Noise.GeneralizedAmplitudeDamping,
        "args": ["gamma", "probability"],
    },
    "GAD": {"op": Noise.GeneralizedAmplitudeDamping, "args": ["gamma", "probability"]},
    # Observable operators
    "TensorProduct": {"op": Observable.TensorProduct, "args": [""]},
    # Matrix operations
    "Unitary": {"op": Gate.Unitary, "args": ["matrix"]},
    "Kraus": {"op": Noise.Kraus, "args": ["matrices"]},
}

result_type_defs = {
    "Probability": {"op": ResultType.Probability, "args": []},
    "DensityMatrix": {"op": ResultType.DensityMatrix, "args": []},
    "Expectation": {"op": ResultType.Expectation, "args": [""]},
    "Sample": {"op": ResultType.Sample, "args": [""]},
    "Variance": {"op": ResultType.Variance, "args": [""]},
    "StateVector": {"op": ResultType.StateVector, "args": []},
    "Amplitude": {"op": ResultType.Amplitude, "args": [""]},
}

observable_defs = {
    "X": Observable.X,
    "Y": Observable.Y,
    "Z": Observable.Z,
    "H": Observable.H,
    "I": Observable.I,
    "Hermitian": Observable.Hermitian,
}

gate_to_observable = {
    f"{Gate.X()}": Observable.X,
    f"{Gate.Y()}": Observable.Y,
    f"{Gate.Z()}": Observable.Z,
    f"{Gate.H()}": Observable.H,
    f"{Gate.I()}": Observable.I,
}


@staticmethod
@circuit.subroutine(register=True)
def from_ir(program: Program) -> Circuit:  # noqa: C901
    """
    Create Circuit from Program object.

    Args:
        program (Program): Program object (IR)

    Returns:
        Circuit: A Circuit based on the given Program object
    """

    def _complex_matrices(float_matrix: np.array):
        cm = np.array([])
        # Assume float_matrix not empty
        if type(float_matrix[0][0][0]) != list:
            # Single matrice
            cm = np.array([[complex(col[0], col[1]) for col in row] for row in float_matrix])
        else:
            # Multiple matrices
            if len(float_matrix) > 1:
                # Return an array of matrices
                mats = []
                for mat in float_matrix:
                    mats.append(np.array([[complex(col[0], col[1]) for col in row] for row in mat]))
                cm = mats
            # Coverage: always true - elif len(float_matrix) > 0
            else:
                # Return the only matrix in the array
                cm = np.array([[complex(col[0], col[1]) for col in row] for row in float_matrix[0]])
        return cm

    circ = Circuit()

    # Instructions and Result Types
    instrs = program.instructions
    instrs += program.results

    for instr in instrs:
        op_name = type(instr).__name__
        qubit_set = []

        # Attributes added to qubit_set in order: controls first followed by targets
        for attr_name in ["control", "controls", "target", "targets"]:
            if hasattr(instr, attr_name):
                attr = getattr(instr, attr_name)
                if type(attr) == list:
                    qubit_set += attr
                else:
                    qubit_set += [attr]

        # Operator arguments
        op_args = {}
        for arg_name in [
            "angle",
            "matrix",
            "matrices",
            "gamma",
            "probability",
            "probX",
            "probY",
            "probZ",
            "observable",
            "states",
        ]:
            if hasattr(instr, arg_name):
                arg_attr = getattr(instr, arg_name)
                op_args[arg_name] = arg_attr
                if arg_name == "observable":
                    # Construct the Observable from the ascii symbols
                    # Coverage: always true - if type(arg_attr) == list and len(arg_attr) > 0
                    if type(arg_attr[0]) == list:
                        # The first element is a list
                        #   The argument contains matrix specifications
                        op_args[arg_name] = _complex_matrices(arg_attr)
                    else:
                        # Observable ascii symbols
                        obs_list = []
                        for obs_ascii in arg_attr:
                            obs_list.append(observable_defs[obs_ascii.upper()]())
                        if len(arg_attr) > 1:
                            op_args[arg_name] = Observable.TensorProduct(obs_list)
                        else:
                            op_args[arg_name] = obs_list[0]
                elif arg_name in ["matrix", "matrices"]:
                    op_args[arg_name] = _complex_matrices(arg_attr)

        # Operator methods
        op = None
        if op_name in gate_defs:
            # Gate
            op = gate_defs[op_name]["op"]
            circ.add_instruction(Instruction(op(**op_args), qubit_set))
        # Coverage: always true - elif op_name in result_type_defs
        # Justification: op_name is type(instr).__name__
        else:
            # Result Type
            op = result_type_defs[op_name]["op"]
            if len(qubit_set) > 0:
                op_args["target"] = qubit_set
            if "states" in op_args:
                # SDK ISSUE: To accommodate argname inconsistency:
                #   'states' in IR but 'state' in Amplitude result type
                state = op_args["states"]
                del op_args["states"]
                op_args["state"] = state
            if op_name == "Expectation":
                # Observable argument
                obs = op_args["observable"]
                if type(obs) == np.ndarray:
                    # Hermitian matrix argument
                    op_args["observable"] = Observable.Hermitian(matrix=obs)
            circ.add_result_type(op(**op_args))

    return circ


@staticmethod
@circuit.subroutine(register=True)
def from_repr(repr_str: str) -> Circuit:  # noqa: C901
    """
    Create Circuit from a string produced by repr(circuit).

    Args:
        repr_str (str): The string produced by repr(circuit)

    Returns:
        Circuit: A Circuit based on the given string produced by repr(circuit)

    Raises:
        ValueError: If syntax errors are encountered in the given string
            or unknown symbols are encountered
    """

    # Head Pointer (hp) points to the first character of the token
    # On return, hp is positioned at the next token

    # hp - the head pointer
    hp = 0

    # Convert a gate to its corresponding Observable
    def _gate_to_observable(gate: Gate) -> Observable:
        obs = gate
        gate_key = f"{obs}"
        if gate_key in gate_to_observable:
            obs = gate_to_observable[gate_key]()
        return obs

    # Get the operator from its ascii symbol
    def _get_op(obj_type: str):
        obj_op = None
        if obj_type in obj_class_defs:
            # Class
            obj_op = obj_class_defs[obj_type]
        elif obj_type in gate_defs:
            # Gate
            obj_op = gate_defs[obj_type]["op"]
        elif obj_type in result_type_defs:
            # Result Type
            obj_op = result_type_defs[obj_type]["op"]
        return obj_op

    # Get a token at position hp terminated by a character contained in terms
    def _get_token(terms: str) -> str:
        nonlocal hp
        obj = ""

        # Find the terminator
        for _hp in range(hp, len(repr_str)):
            if repr_str[_hp] in terms:
                break
        # Terminator is in position _hp

        if not repr_str[_hp] in terms:
            raise ValueError(
                f"At near character {_hp}, a terminator (one of {terms}) is expected "
                + f"but found {repr_str[_hp]}"
            )
        obj = repr_str[hp:_hp]
        hp = _hp + 1

        return obj

    # Get a name; e.g., Qubit
    def _get_name() -> str:
        nonlocal hp

        obj = ""
        if repr_str[hp] == "'":
            # Starting with a single quotation mark
            hp += 1
            obj = _get_token("'")
            if repr_str[hp] != ":":
                # Not followed by a :
                raise ValueError(f"At near character {hp}, : is expected but found {repr_str[hp]}")
            hp += 1
            while repr_str[hp] == " ":
                # Skip spaces that follow
                hp += 1
        else:
            # Unquoted name followed by =; treated as a quoted name followed by :
            obj = _get_token("=")

        return obj

    # Get a scalar; e.g., '101', 2, or 1.5
    def _get_sc():
        nonlocal hp
        obj = ""
        _hp = hp

        while repr_str[_hp] in "'-0123456789.":
            # Skip to the terminator
            _hp += 1
        obj = repr_str[hp:_hp]
        hp = _hp

        try:
            if obj[0] == "'":
                # String scalar
                obj = obj.strip("'")
            elif "." in obj:
                # Float scalar
                obj = float(obj)
            else:
                # Integer scalar
                obj = int(obj)
        except ValueError:
            raise ValueError(f"Invalid scalar {repr_str[hp:_hp]} at near character {hp}")

        return obj

    # Get a named value
    # '<name>': <value>
    # '<name>=<value>
    #     <value> can be
    #         <scalar>
    #         <typed_value>
    #         [<typed_value_list]
    #         [<quoted_string_list>]
    def _get_nv():
        nonlocal hp
        obj = ""
        nm = _get_name()

        if repr_str[hp] == "[":
            # An array
            hp += 1
            if repr_str[hp] == "'":
                # An array of strings
                obj = _get_scl()
            else:
                # A typed value list
                obj = _get_tvl()
            if repr_str[hp] != "]":
                raise ValueError(f"At near character {hp}, ] is expected but found {repr_str[hp]}")
            hp += 1
        elif repr_str[hp] in "'-0123456789":
            # A scalar
            obj = _get_sc()
        else:
            # A typed value
            obj = _get_tv()

        if nm == "observable":
            # Replace the gate operator with an observable
            obj = _gate_to_observable(obj)
        obj = {nm: obj}
        if nm == "qubit_count":
            # Ignored argument qubit_count
            # Must not check earlier in order to allow the parser to run its course
            return None

        return obj

    # Get a typed value
    # <typed_value> can be
    #     <type>(<scalar>)
    #     <type>([<typed_value_list>])
    #     <type>(<named_value_list>)
    #     <type>(<typed_value_list>)
    def _get_tv():
        nonlocal hp
        obj = ""
        obj_type = _get_token("(")

        if repr_str[hp] in "-0123456789":
            # A numeric scalar
            obj = _get_sc()
            obj_op = _get_op(obj_type)
            if not obj_op:
                raise ValueError(f"Unknown operator {obj_type}")
            else:
                obj = obj_op(obj)
        elif repr_str[hp] == "[":
            # An array
            hp += 1
            tvl = _get_tvl()
            obj_op = _get_op(obj_type)
            if not obj_op:
                raise ValueError(f"Unknown operator {obj_type}")
            else:
                obj = obj_op(tvl)
            if repr_str[hp] != "]":
                raise ValueError(f"At near character {hp}, ] is expected but found {repr_str[hp]}")
            hp += 1
        elif repr_str[hp] == ")":
            # No arguments
            obj_op = _get_op(obj_type)
            obj = obj_op()
        else:
            if re.match(r"[a-zA-Z0-9]+\(", repr_str[hp:]):
                # A typed value list
                tvl = _get_tvl()
                obj_op = _get_op(obj_type)
                if not obj_op:
                    raise ValueError(f"Unknown operator {obj_type}")
                # Coverage: always true - elif obj_type == "TensorProduct"
                # Justification: Only TensorProduct will reach here
                else:
                    # TensorProduct argument treatment
                    obs_list = []
                    for obs in tvl:
                        obs_list.append(_gate_to_observable(obs))
                    obj = obj_op(obs_list)
            else:
                # A named value list
                nvl = _get_nvl()
                obj_op = _get_op(obj_type)
                if not obj_op:
                    raise ValueError(f"Unknown operator {obj_type}")
                else:
                    if "instructions" in nvl:
                        # Circuit level named value list
                        # Use nvl['instructions'] as the argument
                        # instead of using nvl as an argument list
                        obj = obj_op(nvl["instructions"])
                        if "result_types" in nvl:
                            for rt in nvl["result_types"]:
                                obj.add_result_type(rt)
                    else:
                        obj = obj_op(**nvl)

        if repr_str[hp] != ")":
            raise ValueError(f"At near character {hp}, ) is expected but found {repr_str[hp]}")
        hp += 1

        return obj

    # Get a scalar list
    def _get_scl() -> List:
        nonlocal hp
        # Get the first scalar
        obj_list = [_get_sc()]

        if repr_str[hp] == ",":
            # More scalars to come
            hp += 1
            while repr_str[hp] == " ":
                hp += 1
            # Recursively obtain the full list
            obj_list += _get_scl()

        return obj_list

    # Get a named value list (could be empty)
    def _get_nvl() -> List:
        nonlocal hp
        obj_list = {}
        # Get the first named value
        nv = _get_nv()
        if nv:
            obj_list = nv
        if repr_str[hp] == ",":
            # More named values to come
            hp += 1
            while repr_str[hp] == " ":
                # Skip spaces that follow
                hp += 1
            # Recursively obtain the full list
            obj_list.update(_get_nvl())

        return obj_list

    # Get a typed value list
    def _get_tvl() -> List:
        nonlocal hp
        obj_list = [_get_tv()]

        if repr_str[hp] == ",":
            # More typed values to come
            hp += 1
            while repr_str[hp] == " ":
                # Skip spaces that follow
                hp += 1
            # Recursively obtain the full list
            obj_list += _get_tvl()

        return obj_list

    # Main program is a one-liner
    return _get_tv()


@staticmethod
@circuit.subroutine(register=True)
def from_diagram(diagram_str: str) -> Circuit:  # noqa: C901
    """
    Create Circuit from a circuit diagram string produced by f'{circuit}'.

    Args:
        diagram_str (str): The circuit diagram string produced by f'{circuit}'

    Returns:
        Circuit: A Circuit based on the given circuit diagram string produced by f'{circuit}'

    Raises:
        ValueError: If syntax errors are encountered in the given circuit diagram string
            or unknown instructions are encountered.
    """

    # Parse a Gate specification: <gate_operator>(<gate_argument_list>)
    def _get_gate_arg(gate: str):
        gate_op = ""
        gate_arg = 0.0
        g_spec = re.findall(r"^([A-Za-z0-9]+)(\(([,.0-9-]+)\))?", gate)

        if len(g_spec):
            g_spec = g_spec[0]  # Unbracket the array
            # Coverage: always true - if g_spec[0]
            # Justification: findall matched
            # g_spec[0]: gate_op
            # g_spec[1]: (gate_arg)
            # g_spec[2]: gate_arg
            gate_op = g_spec[0]
            if g_spec[2]:
                gate_arg = [float(f) for f in g_spec[2].split(",")]

        return gate_op, gate_arg

    # Get the Instruction from the qubit set
    def _get_instr(qbSet: str) -> Instruction:
        i_spec = qbSet

        gate_op = ""
        gate_arg = None
        target = []
        instr = None

        # Determine the operator and arguments
        if "C" in i_spec:
            # Controlled gate
            target = i_spec["C"]  # Control bit/bits come first
            del i_spec["C"]
            # C or CC
            ctrl = "C" * len(target)
            g, t = tuple(i_spec.items())[0]
            # g contains the operation on the target t (array of qubits)
            target += t
            gate_op, gate_arg = _get_gate_arg(g)
            gate_op = ctrl + gate_op
        else:
            # Not a controlled gate
            g, t = tuple(i_spec.items())[0]
            target = t
            gate_op, gate_arg = _get_gate_arg(g)

        # Build the Instruction
        if gate_op in gate_defs:
            _gate_def = gate_defs[gate_op]

            if len(_gate_def["args"]) == 0:
                # No arguments
                instr = Instruction(_gate_def["op"](), target)
            elif len(_gate_def["args"]) == 1:
                # Single argument
                if len(target) > 1 and "alt_op" in _gate_def:
                    # Multi-qubits are involved AND there is a multi-qubit version.
                    instr = Instruction(_gate_def["alt_op"](gate_arg[0]), target)
                else:
                    instr = Instruction(_gate_def["op"](gate_arg[0]), target)
            else:
                # Multiple arguments
                args = {}
                for n, v in zip(_gate_def["args"], gate_arg):
                    args[n] = v
                instr = Instruction(_gate_def["op"](**args), target)

        return instr

    # Parse a Result Type specification: <result_type>(<result_type_argument_list>)
    def _get_result_type_arg(result_type: str):
        rt_op = ""
        rt_arg = None
        r_spec = re.findall(r"^([A-Za-z0-9]+)(\(([@XYZHI]+)\))?", result_type)

        if len(r_spec):
            # r_spec[0]: rt_op
            # r_spec[1]: (rt_args)
            # r_spec[2]: rt_args
            r_spec = r_spec[0]  # Unbracket the array
            # Coverage: always true - if r_spec[0]
            # Justification: findall matched
            rt_op = r_spec[0]
            if r_spec[2]:
                rt_args = r_spec[2].split("@")
                # Multiple observable arguments
                # First observable argument
                # Coverage: always true - if len(rt_args) and rt_args[0] in observable_defs
                # Justification: rt_args not empty and observable guaranteed exist from regex
                rt_arg = observable_defs[rt_args[0]]()
                for rta in rt_args[1:]:
                    # Coverage: if rta in observable_defs
                    # Justification: Subsequent observable argument (guaranteed existance by regex)
                    rt_arg = rt_arg @ observable_defs[rta]()

        return rt_op, rt_arg

    # Get the Result Type from the qubit set
    def _get_result_type(qbSet: str) -> ResultType:
        rt_spec = qbSet
        rt_op = ""
        rt_arg = None
        target = []
        result_type = None

        # Get the result type and arguments from only the first element
        rt, tg = tuple(rt_spec.items())[0]
        target = tg
        rt_op, rt_arg = _get_result_type_arg(rt)

        # Build the result type
        if rt_op in result_type_defs:
            _rt_def = result_type_defs[rt_op]

            if len(_rt_def["args"]) == 0:
                # No arguments
                result_type = _rt_def["op"](target)
            elif rt_arg:
                result_type = _rt_def["op"](rt_arg, target)

        return result_type

    circ = Circuit()
    lines = diagram_str.strip().split("\n")

    # The first line defines the moments
    moment_line = lines[0]
    # The last line defines the (global) result types
    result_types_spec = (
        re.sub(" ", "", lines[-1].replace("Additional result types: ", ""))
        if lines[-1] != moment_line
        else ""
    )

    # Moment labels are separated by |
    moment_labels = re.findall(r"([^|]+)\|", moment_line)
    num_moments = len(moment_labels) - 1
    # An array of moments widths
    col_widths = [len(m) for m in moment_labels]

    # Raw format (as is from the diagram) raw[qubit][moment]
    # Raw gate
    gate_raw = {}
    # Raw connector - the | to connect multi-qubit gate symbols
    cnnt_raw = {}
    # Default to last
    qubit_num = -1
    for line in lines[2:]:  # pragma: no branch
        # For each line of the diagram
        if line == moment_line:
            # Ignore the moment line repeat
            break
        # The first column "may" contain the qubit label
        # If not, it is the subsequent line of the previous qubit label
        qubit_col = re.findall(r"^q([0-9]+)", line[0 : col_widths[0]])
        # Assume looking for a connector
        raw = cnnt_raw
        if len(qubit_col):
            # New qubit line
            # Looking for a gate
            raw = gate_raw
            qubit_num = int(qubit_col[0])

        # Split the moments of the line into the q_line array
        q_line = []
        col_start = col_widths[0] + 1
        for col_width in col_widths[1:]:
            # Append spacing to align (for ease of debugging)
            cell = line[col_start : col_start + col_width] + " " * col_width
            q_line.append(cell[0:col_width])
            col_start += col_width + 1
        # Put the moments into the gate or connector specification
        raw[qubit_num] = q_line

    # Scan parallel moments and split each into individual moments
    # p_moments[moment] contains the set of gate positions
    p_moments = {}
    for m in range(num_moments):
        p_set = set()
        for qb in gate_raw:
            gr = gate_raw[qb][m]
            # Last character lc1 and last second character lc2
            lc1 = ""
            lc2 = ""
            # Scan the raw moment at position p
            p = 0
            for c in gr:
                if c != "-" and lc1 == "-" and lc2 != "(":
                    # Mark the position now a gate name is found (and not an argument)
                    p_set.add(p)
                lc2 = lc1
                lc1 = c
                p += 1
        if len(p_set):
            p_moments[m] = sorted(p_set)

    # Working from the last moment backward to allow inserting new moments after splitting
    pm_reversed = []
    for k in p_moments:
        pm_reversed.append(k)
        num_moments += len(p_moments[k])

    pm_reversed = reversed(pm_reversed)
    for m in pm_reversed:
        for qb in gate_raw:
            # gr is the gate raw of qubit qb at moment m
            gr = gate_raw[qb][m]
            pm = p_moments[m].copy()
            # pm is a set of gate positions (single or multiple)
            # Append the last position for looping
            pm.append(len(gr))

            # qbMoments contains the split moments
            qbMoments = []
            p = 0
            for i in pm:
                qbMoments.append(gr[p:i])
                p = i

            # Insert the split gate moments (or itself if single)
            gate_raw[qb][m : m + 1] = qbMoments

            # Split the connectors
            cr = cnnt_raw[qb][m]
            qbMoments = []
            p = 0
            for i in pm:
                qbMoments.append(cr[p:i])
                p = i

            # Insert the split connector moments (or itself if single)
            cnnt_raw[qb][m : m + 1] = qbMoments

    # Now each moment line contains only one gate or connector
    # num_moments is updated with the extra moments after splitting

    # momentQbSets[m] contains qbSets, which contains qbSet for each qubit
    momentQbSets = []
    for m in range(num_moments):
        # Consolidate multi-qubits gates
        qbSets = []  # Elements are qbSet
        qbSet = {}  # { gate_qb: [ qb, ... ] }
        for qb in gate_raw:
            # Gate
            gate_qb = gate_raw[qb][m].strip("- ")
            # Ignore connectors passing through the qubit line
            if gate_qb and gate_qb != "|":
                if gate_qb not in qbSet:
                    # Initialise the qbSet
                    qbSet[gate_qb] = []
                qbSet[gate_qb].append(qb)
            # Connector
            cnntor = cnnt_raw[qb][m].strip()
            if cnntor == "" and qbSet != {}:
                # No connectors but there are gates
                qbSets.append(qbSet)
                qbSet = {}

        # Create a new moment with the qbSets
        momentQbSets.append(qbSets)

    # Adding instructions and result types moment by moment, qubit by qubit
    for m in range(num_moments):
        for qbSet in momentQbSets[m]:
            instr = _get_instr(qbSet)
            if instr:
                circ.add_instruction(instr)
            else:
                result_type = _get_result_type(qbSet)
                if result_type:
                    circ.add_result_type(result_type)
                else:
                    raise ValueError(f"Unknown instruction {qbSet}")

    # Circuit result types
    # Needs to preserve the order to match the input
    rts = re.findall(r"StateVector|Amplitude\([^)]*\)", result_types_spec)
    for rt in rts:
        if rt == "StateVector":
            circ.state_vector()
        amp_spec = re.findall(r"Amplitude\([^)]*\)", rt)
        if len(amp_spec) > 0:
            bitstrings = (
                re.sub(r"Amplitude\(", "", re.sub(" ", "", amp_spec[0])).rstrip(")").split(",")
            )
            circ.amplitude(bitstrings)

    return circ
