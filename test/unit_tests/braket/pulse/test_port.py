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

import pytest
from oqpy import PortVar
from oqpy.base import expr_matches

from braket.pulse import Port


@pytest.fixture
def port_id():
    return "test_port_ff"


@pytest.fixture
def port_time_resolution():
    return 1e-9


@pytest.fixture
def port_properties():
    return {"dt": 1e-6, "direction": "tx"}


@pytest.fixture
def port(port_id, port_time_resolution, port_properties):
    return Port(port_id, port_time_resolution, port_properties)


def test_port_no_properties(port_id, port_time_resolution):
    port = Port(port_id, port_time_resolution)
    assert port.id == port_id
    assert port.dt == port_time_resolution
    assert port.properties is None


def test_port_to_oqpy_expression(port, port_id):
    expected_expression = PortVar(port_id)
    assert expr_matches(port._to_oqpy_expression(), expected_expression)


def test_port_equality(port, port_time_resolution):
    p2 = Port(port.id, port_time_resolution)
    p3 = Port("random_id", port_time_resolution, properties=port.properties)
    p4 = Port(port.id, port_time_resolution, properties={"random_property": "foo"})
    p5 = Port(port.id, 0)
    assert port == p2
    assert port == p4
    assert port == p5
    assert port != p3
