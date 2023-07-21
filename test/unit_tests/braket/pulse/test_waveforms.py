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
import math
import re
from copy import deepcopy

import numpy as np
import pytest
from oqpy import Program

from braket.circuits.free_parameter import FreeParameter
from braket.pulse import ArbitraryWaveform, ConstantWaveform, DragGaussianWaveform, GaussianWaveform
from braket.pulse.ast.qasm_parser import ast_to_qasm


@pytest.mark.parametrize(
    "amps",
    [
        [complex(1, 2), complex(0.3, -1), 0, 4.2],
        np.array([complex(1, 2), complex(0.3, -1), 0, 4.2]),
    ],
)
def test_arbitrary_waveform(amps):
    id = "arb_wf_x"
    wf = ArbitraryWaveform(amps, id)
    assert wf.amplitudes == list(amps)
    assert wf.id == id
    oq_exp = wf._to_oqpy_expression()
    assert oq_exp.init_expression == list(amps)
    assert oq_exp.name == wf.id


def test_arbitrary_waveform_default_params():
    amps = [1, 4, 5]
    wf = ArbitraryWaveform(amps)
    assert wf.amplitudes == amps
    assert re.match(r"[A-Za-z]{10}", wf.id)


def test_arbitrary_wf_eq():
    wf = ArbitraryWaveform([1, 4, 5], "wf_x")
    wf_2 = ArbitraryWaveform(wf.amplitudes, wf.id)
    assert wf_2 == wf
    for att in ["amplitudes", "id"]:
        wfc = deepcopy(wf_2)
        setattr(wfc, att, "wrong_value")
        assert wf != wfc


def test_arbitrary_waveform_not_castable_into_list():
    amps = 1
    with pytest.raises(TypeError):
        ArbitraryWaveform(amps)


def test_constant_waveform():
    length = 4e-3
    iq = 4
    id = "const_wf_x"
    wf = ConstantWaveform(length, iq, id)
    assert wf.length == length
    assert wf.iq == iq
    assert wf.id == id

    _assert_wf_qasm(wf, "waveform const_wf_x = constant(4000000.0ns, 4);")


def test_constant_waveform_default_params():
    amps = [1, 4, 5]
    wf = ArbitraryWaveform(amps)
    assert wf.amplitudes == amps
    assert re.match(r"[A-Za-z]{10}", wf.id)


def test_constant_wf_eq():
    wf = ConstantWaveform(4e-3, complex(2, 3), "wf_c")
    wf_2 = ConstantWaveform(wf.length, wf.iq, wf.id)
    assert wf_2 == wf
    for att in ["length", "iq", "id"]:
        wfc = deepcopy(wf_2)
        setattr(wfc, att, "wrong_value")
        assert wf != wfc


def test_constant_wf_free_params():
    wf = ConstantWaveform(
        FreeParameter("length_v") + FreeParameter("length_w"), iq=complex(2, -3), id="const_wf"
    )
    assert wf.parameters == [FreeParameter("length_v") + FreeParameter("length_w")]
    _assert_wf_qasm(
        wf,
        "waveform const_wf = "
        "constant((1000000000.0*length_v + 1000000000.0*length_w)ns, 2.0 - 3.0im);",
    )

    wf_2 = wf.bind_values(length_v=2e-6, length_w=4e-6)
    assert len(wf_2.parameters) == 1
    assert math.isclose(wf_2.parameters[0], 6e-6)
    _assert_wf_qasm(wf_2, "waveform const_wf = constant(6000.0ns, 2.0 - 3.0im);")


def test_drag_gaussian_waveform():
    length = 4e-9
    sigma = 0.3
    beta = 0.6
    amplitude = 0.4
    zero_at_edges = False
    id = "drag_gauss_wf"
    wf = DragGaussianWaveform(length, sigma, beta, amplitude, zero_at_edges, id)
    assert wf.id == id
    assert wf.zero_at_edges == zero_at_edges
    assert wf.amplitude == amplitude
    assert wf.beta == beta
    assert wf.sigma == sigma
    assert wf.length == length

    _assert_wf_qasm(
        wf, "waveform drag_gauss_wf = drag_gaussian(4.0ns, 300000000.0ns, 0.6, 0.4, false);"
    )


def test_drag_gaussian_waveform_default_params():
    length = 4e-9
    sigma = 0.3
    beta = 0.6
    wf = DragGaussianWaveform(length, sigma, beta)
    assert re.match(r"[A-Za-z]{10}", wf.id)
    assert wf.zero_at_edges is False
    assert wf.amplitude == 1
    assert wf.beta == beta
    assert wf.sigma == sigma
    assert wf.length == length


def test_drag_gaussian_wf_eq():
    wf = DragGaussianWaveform(4e-3, 0.3, 0.2, 0.7, True, "wf_dg")
    wf_2 = DragGaussianWaveform(wf.length, wf.sigma, wf.beta, wf.amplitude, wf.zero_at_edges, wf.id)
    assert wf_2 == wf
    for att in ["length", "sigma", "beta", "amplitude", "zero_at_edges", "id"]:
        wfc = deepcopy(wf_2)
        setattr(wfc, att, "wrong_value")
        assert wf != wfc


def test_gaussian_waveform():
    length = 4e-9
    sigma = 0.3
    amplitude = 0.4
    zero_at_edges = False
    id = "gauss_wf"
    wf = GaussianWaveform(length, sigma, amplitude, zero_at_edges, id)
    assert wf.id == id
    assert wf.zero_at_edges == zero_at_edges
    assert wf.amplitude == amplitude
    assert wf.sigma == sigma
    assert wf.length == length

    _assert_wf_qasm(wf, "waveform gauss_wf = gaussian(4.0ns, 300000000.0ns, 0.4, false);")


def test_drag_gaussian_wf_free_params():
    wf = DragGaussianWaveform(
        FreeParameter("length_v"),
        FreeParameter("sigma_a") + FreeParameter("sigma_b"),
        FreeParameter("beta_y"),
        FreeParameter("amp_z"),
        id="d_gauss_wf",
    )
    assert wf.parameters == [
        FreeParameter("length_v"),
        FreeParameter("sigma_a") + FreeParameter("sigma_b"),
        FreeParameter("beta_y"),
        FreeParameter("amp_z"),
    ]
    _assert_wf_qasm(
        wf,
        "waveform d_gauss_wf = "
        "drag_gaussian((1000000000.0*length_v)ns, (1000000000.0*sigma_a + "
        "1000000000.0*sigma_b)ns, beta_y, amp_z, false);",
    )

    wf_2 = wf.bind_values(length_v=0.6, sigma_a=0.4)
    assert wf_2.parameters == [
        0.6,
        0.4 + FreeParameter("sigma_b"),
        FreeParameter("beta_y"),
        FreeParameter("amp_z"),
    ]
    _assert_wf_qasm(
        wf_2,
        "waveform d_gauss_wf = drag_gaussian(600000000.0ns, (1000000000.0*sigma_b "
        "+ 400000000.0)ns, beta_y, amp_z, false);",
    )

    wf_3 = wf.bind_values(length_v=0.6, sigma_a=0.3, sigma_b=0.1, beta_y=0.2, amp_z=0.1)
    assert wf_3.parameters == [0.6, 0.4, 0.2, 0.1]
    _assert_wf_qasm(
        wf_3, "waveform d_gauss_wf = drag_gaussian(600000000.0ns, 400000000.0ns, 0.2, 0.1, false);"
    )


def test_gaussian_waveform_default_params():
    length = 4e-9
    sigma = 0.3
    wf = GaussianWaveform(length, sigma)
    assert re.match(r"[A-Za-z]{10}", wf.id)
    assert wf.zero_at_edges is False
    assert wf.amplitude == 1
    assert wf.sigma == sigma
    assert wf.length == length


def test_gaussian_wf_eq():
    wf = GaussianWaveform(4e-3, 0.3, 0.7, True, "wf_dg")
    wf_2 = GaussianWaveform(wf.length, wf.sigma, wf.amplitude, wf.zero_at_edges, wf.id)
    assert wf_2 == wf
    for att in ["length", "sigma", "amplitude", "zero_at_edges", "id"]:
        wfc = deepcopy(wf_2)
        setattr(wfc, att, "wrong_value")
        assert wf != wfc


def test_gaussian_wf_free_params():
    wf = GaussianWaveform(
        FreeParameter("length_v"), FreeParameter("sigma_x"), FreeParameter("amp_z"), id="gauss_wf"
    )
    assert wf.parameters == [
        FreeParameter("length_v"),
        FreeParameter("sigma_x"),
        FreeParameter("amp_z"),
    ]
    _assert_wf_qasm(
        wf,
        "waveform gauss_wf = gaussian((1000000000.0*length_v)ns, (1000000000.0*sigma_x)ns, "
        "amp_z, false);",
    )

    wf_2 = wf.bind_values(length_v=0.6, sigma_x=0.4)
    assert wf_2.parameters == [0.6, 0.4, FreeParameter("amp_z")]
    _assert_wf_qasm(
        wf_2, "waveform gauss_wf = gaussian(600000000.0ns, 400000000.0ns, amp_z, false);"
    )

    wf_3 = wf.bind_values(length_v=0.6, sigma_x=0.3, amp_z=0.1)
    assert wf_3.parameters == [0.6, 0.3, 0.1]
    _assert_wf_qasm(wf_3, "waveform gauss_wf = gaussian(600000000.0ns, 300000000.0ns, 0.1, false);")


def _assert_wf_qasm(waveform, expected_qasm):
    p = Program(None)
    p.declare(waveform._to_oqpy_expression())
    assert ast_to_qasm(p.to_ast(include_externs=False)) == expected_qasm
