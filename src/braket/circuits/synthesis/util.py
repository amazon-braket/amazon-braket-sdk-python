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

import numpy as np
from scipy.linalg import block_diag
from typing import List, Tuple, Union

from braket.circuits.synthesis.predicates import is_diag, is_hermitian, commute, is_unitary


def to_su(u: np.ndarray) -> np.ndarray:
    """
    Given a unitary in U(N), return the
    unitary in SU(N).

    Args:
        u (np.ndarray): The unitary in U(N).

    Returns:
        su (np.ndarray): The unitary in SU(N)
    """

    return u * np.linalg.det(u) ** (-1 / np.shape(u)[0])
