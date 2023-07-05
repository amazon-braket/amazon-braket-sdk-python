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

"""AutoQASM provides a native Python programming experience for building complex quantum programs
and running them on simulators and quantum hardware using Amazon Braket.

The basic usage of AutoQASM is as follows:

    import braket.experimental.autoqasm as aq
    from braket.experimental.autoqasm.gates import h, cnot, measure

    @aq.function
    def my_program():
        h(0)
        cnot(0, 1)
        result = measure([0, 1])
        return result

    program = my_program()
    print(program.to_ir())

The Python code above outputs the following OpenQASM program:

    OPENQASM 3.0;
    qubit[2] __qubits__;
    h __qubits__[0];
    cnot __qubits__[0], __qubits__[1];
    bit[2] result;
    result[0] = measure __qubits__[0];
    result[1] = measure __qubits__[1];
"""

from oqpy import ArrayVar, BitVar, BoolVar, FloatVar, IntVar  # noqa: F401

from . import api, constants, gates, operators, types  # noqa: F401
from .api import function  # noqa: F401
from .gates import QubitIdentifier  # noqa: F401
from .program import (  # noqa: F401
    Program,
    ProgramConversionContext,
    Verbatim,
    build_program,
    get_program_conversion_context,
    in_active_program_conversion_context,
)
from .transpiler import transpiler  # noqa: F401
from .types import qasm_range as range  # noqa: F401
