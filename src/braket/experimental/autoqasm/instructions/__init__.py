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

"""Instructions that apply to qubits or frames, including quantum gates, reset, measure
and pulse control.

Example of using a `h` gate and a `cnot` gate to create a Bell circuit:

.. code-block:: python

    @aq.function
    def bell():
        h(0)
        cnot(0, 1)
        measure([0, 1])
"""

from .gates import *  # noqa: F401, F403
from .instructions import QubitIdentifierType, reset  # noqa: F401
from .measurements import measure  # noqa: F401
from .pulse import *  # noqa: F401, F403
