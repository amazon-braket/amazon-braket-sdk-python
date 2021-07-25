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

from typing import List

import numpy as np
from pydantic import BaseModel

from braket.circuits.qubit_set import QubitSet

IRInstruction = BaseModel


def complex_matrices(float_matrix: np.array):
    """Convert a single matrix or a list of matrices from [real, imaginary] pairs into complex numbers.

    Args:
        float_matrix (np.array): Matrix or list of matrices of [real, imaginary] pairs

    Returns:
        Matrix or list of matrices of complex numbers
    """
    cm = np.array([])
    # Assume float_matrix not empty
    if type(float_matrix[0][0][0]) != list:
        # Single matrix
        cm = np.array([[complex(col[0], col[1]) for col in row] for row in float_matrix])
    else:
        # Return an array of matrices
        mats = []
        for mat in float_matrix:
            mats.append(np.array([[complex(col[0], col[1]) for col in row] for row in mat]))
        cm = mats
    return cm


def _attr_dict(obj, attr_names):
    return {
        attr_name: getattr(obj, attr_name)
        for attr_name in attr_names
        if attr_name in obj.__fields__
    }


def _ir_instr_to_qubit_set(ir_instruction: IRInstruction, attr_names: List[str]) -> QubitSet:
    return QubitSet(_attr_dict(ir_instruction, attr_names).values())
