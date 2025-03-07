# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from __future__ import annotations

from typing import Any

from oqpy import PortVar
from oqpy.base import OQPyExpression


class Port:
    """Ports represent any input or output component meant to manipulate and observe qubits on
    a device. See https://openqasm.com/language/openpulse.html#ports for more details.
    """

    def __init__(self, port_id: str, dt: float, properties: dict[str, Any] | None = None):
        """Initializes a Port.

        Args:
            port_id (str): str identifying a unique port on the device.
            dt (float): The smallest time step that may be used on the control hardware.
            properties (Optional[dict[str, Any]]): Dict containing properties of
                this port. Defaults to None.
        """
        self._port_id = port_id
        self._dt = dt
        self.properties = properties

    @property
    def id(self) -> str:
        """Returns a str indicating the port id."""
        return self._port_id

    @property
    def dt(self) -> float:
        """Returns the smallest time step that may be used on the control hardware."""
        return self._dt

    def __eq__(self, other: Port) -> bool:
        return self.id == other.id if isinstance(other, Port) else False

    def _to_oqpy_expression(self) -> OQPyExpression:
        return PortVar(name=self.id)
