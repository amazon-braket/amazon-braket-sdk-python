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
from braket.pulse import (
    ArbitraryWaveform,
    ConstantWaveform,
    DragGaussianWaveform,
    ErfSquareWaveform,
    GaussianWaveform,
)
from braket.pulse.ast.qasm_parser import ast_to_qasm
from braket.pulse.waveforms import _parse_waveform_from_calibration_schema


@pytest.mark.parametrize(
    "amps",
    [
        [complex(1, 2), complex(0.3, -1), 0, 4.2],
        np.array([complex(1, 2), complex(0.3, -1), 0, 4.2]),
    ],
)
def test_arbitrary_waveform(amps):
    waveform_id = "arb_wf_x"
    wf = ArbitraryWaveform(amps, waveform_id)
    assert wf.amplitudes == list(amps)
    assert wf.id == waveform_id
    oq_exp = wf._to_oqpy_expression()
    assert oq_exp.init_expression == list(amps)
    assert oq_exp.name == wf.id


def test_arbitrary_waveform_repr():
    amps = [1, 4, 5]
    waveform_id = "arb_wf_x"
    wf = ArbitraryWaveform(amps, waveform_id)
    expected = f"ArbitraryWaveform('id': {wf.id}, 'amplitudes': {wf.amplitudes})"
    assert repr(wf) == expected


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

    _assert_wf_qasm(wf, "waveform const_wf_x = constant(4.0ms, 4);")


def test_constant_waveform_repr():
    length = 4e-3
    iq = 4
    id = "const_wf_x"
    wf = ConstantWaveform(length, iq, id)
    expected = f"ConstantWaveform('id': {wf.id}, 'length': {wf.length}, 'iq': {wf.iq})"
    assert repr(wf) == expected


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
        "waveform const_wf = constant((length_v + length_w) * 1s, 2.0 - 3.0im);",
    )

    wf_2 = wf.bind_values(length_v=2e-6, length_w=4e-6)
    assert len(wf_2.parameters) == 1
    assert math.isclose(wf_2.parameters[0], 6e-6)
    _assert_wf_qasm(wf_2, "waveform const_wf = constant(6.0us, 2.0 - 3.0im);")


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

    _assert_wf_qasm(wf, "waveform drag_gauss_wf = drag_gaussian(4.0ns, 300.0ms, 0.6, 0.4, false);")


def test_drag_gaussian_waveform_repr():
    length = 4e-9
    sigma = 0.3
    beta = 0.6
    amplitude = 0.4
    zero_at_edges = False
    id = "drag_gauss_wf"
    wf = DragGaussianWaveform(length, sigma, beta, amplitude, zero_at_edges, id)
    expected = (
        f"DragGaussianWaveform('id': {wf.id}, 'length': {wf.length}, 'sigma': {wf.sigma}, "
        f"'beta': {wf.beta}, 'amplitude': {wf.amplitude}, 'zero_at_edges': {wf.zero_at_edges})"
    )
    assert repr(wf) == expected


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
        "drag_gaussian(length_v * 1s, (sigma_a + sigma_b) * 1s, beta_y, amp_z, false);",
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
        "waveform d_gauss_wf = drag_gaussian(600.0ms, (0.4 + sigma_b) * 1s, beta_y, amp_z, false);",
    )

    wf_3 = wf.bind_values(length_v=0.6, sigma_a=0.3, sigma_b=0.1, beta_y=0.2, amp_z=0.1)
    assert wf_3.parameters == [0.6, 0.4, 0.2, 0.1]
    _assert_wf_qasm(wf_3, "waveform d_gauss_wf = drag_gaussian(600.0ms, 400.0ms, 0.2, 0.1, false);")


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

    _assert_wf_qasm(wf, "waveform gauss_wf = gaussian(4.0ns, 300.0ms, 0.4, false);")


def test_gaussian_waveform_repr():
    length = 4e-9
    sigma = 0.3
    amplitude = 0.4
    zero_at_edges = False
    id = "gauss_wf"
    wf = GaussianWaveform(length, sigma, amplitude, zero_at_edges, id)
    expected = (
        f"GaussianWaveform('id': {wf.id}, 'length': {wf.length}, 'sigma': {wf.sigma}, "
        f"'amplitude': {wf.amplitude}, 'zero_at_edges': {wf.zero_at_edges})"
    )
    assert repr(wf) == expected


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
        "waveform gauss_wf = gaussian(length_v * 1s, sigma_x * 1s, amp_z, false);",
    )

    wf_2 = wf.bind_values(length_v=0.6, sigma_x=0.4)
    assert wf_2.parameters == [0.6, 0.4, FreeParameter("amp_z")]
    _assert_wf_qasm(wf_2, "waveform gauss_wf = gaussian(600.0ms, 400.0ms, amp_z, false);")

    wf_3 = wf.bind_values(length_v=0.6, sigma_x=0.3, amp_z=0.1)
    assert wf_3.parameters == [0.6, 0.3, 0.1]
    _assert_wf_qasm(wf_3, "waveform gauss_wf = gaussian(600.0ms, 300.0ms, 0.1, false);")


def test_erf_square_waveform():
    length = 4e-9
    width = 0.3
    sigma = 0.2
    off_center = 1e-9
    amplitude = 0.4
    zero_at_edges = False
    id = "erf_square_wf"
    wf = ErfSquareWaveform(length, width, sigma, off_center, amplitude, zero_at_edges, id)
    assert wf.id == id
    assert wf.zero_at_edges == zero_at_edges
    assert wf.amplitude == amplitude
    assert wf.width == width
    assert wf.sigma == sigma
    assert wf.length == length
    assert wf.off_center == off_center


def test_erf_square_waveform_repr():
    length = 4e-9
    width = 0.3
    sigma = 0.2
    off_center = 1e-9
    amplitude = 0.4
    zero_at_edges = False
    id = "erf_square_wf"
    wf = ErfSquareWaveform(length, width, sigma, off_center, amplitude, zero_at_edges, id)
    repr(wf)


def test_erf_square_waveform_default_params():
    length = 4e-9
    width = 0.3
    sigma = 0.2
    off_center = 1e-9
    wf = ErfSquareWaveform(length, width, sigma, off_center)
    assert re.match(r"[A-Za-z]{10}", wf.id)
    assert wf.zero_at_edges is False
    assert wf.amplitude == 1
    assert wf.width == width
    assert wf.sigma == sigma
    assert wf.length == length
    assert wf.off_center == off_center


def test_erf_square_wf_eq():
    wf = ErfSquareWaveform(4e-9, 0.3, 0.2, 1e-9, 0.7, True, "wf_es")
    wf_2 = ErfSquareWaveform(
        wf.length, wf.width, wf.sigma, wf.off_center, wf.amplitude, wf.zero_at_edges, wf.id
    )
    assert wf_2 == wf
    for att in ["length", "width", "sigma", "off_center", "amplitude", "zero_at_edges", "id"]:
        wfc = deepcopy(wf_2)
        setattr(wfc, att, "wrong_value")
        assert wf != wfc


def test_erf_square_wf_free_params():
    wf = ErfSquareWaveform(
        FreeParameter("length_v"),
        FreeParameter("width_x"),
        FreeParameter("sigma_y"),
        FreeParameter("off_center_x"),
        FreeParameter("amp_z"),
        id="erf_square_wf",
    )
    assert wf.parameters == [
        FreeParameter("length_v"),
        FreeParameter("width_x"),
        FreeParameter("sigma_y"),
        FreeParameter("off_center_x"),
        FreeParameter("amp_z"),
    ]

    wf_2 = wf.bind_values(length_v=0.6, width_x=0.4)
    assert wf_2.parameters == [
        0.6,
        0.4,
        FreeParameter("sigma_y"),
        FreeParameter("off_center_x"),
        FreeParameter("amp_z"),
    ]
    _assert_wf_qasm(
        wf_2,
        "waveform erf_square_wf = erf_square(600.0ms, 400.0ms, sigma_y * 1s, off_center_x * 1s,"
        " amp_z, false);",
    )

    wf_3 = wf.bind_values(length_v=0.6, width_x=0.3, sigma_y=0.1, off_center_x=0.05)
    assert wf_3.parameters == [0.6, 0.3, 0.1, 0.05, FreeParameter("amp_z")]
    _assert_wf_qasm(
        wf_3,
        "waveform erf_square_wf = erf_square(600.0ms, 300.0ms, 100.0ms, 50.0ms, amp_z, false);",
    )


def _assert_wf_qasm(waveform, expected_qasm):
    p = Program(None)
    p.declare(waveform._to_oqpy_expression())
    assert ast_to_qasm(p.to_ast(include_externs=False)) == expected_qasm


@pytest.mark.parametrize(
    "waveform_json, waveform",
    [
        (
            {
                "waveformId": "q0_q1_cz_CZ",
                "amplitudes": [[0.0, 0.0], [0.0, 0.0]],
            },
            ArbitraryWaveform(id="q0_q1_cz_CZ", amplitudes=[complex(0.0, 0.0), complex(0.0, 0.0)]),
        ),
        (
            {
                "waveformId": "wf_drag_gaussian_0",
                "name": "drag_gaussian",
                "arguments": [
                    {"name": "length", "value": 6.000000000000001e-8, "type": "float"},
                    {"name": "sigma", "value": 6.369913502160144e-9, "type": "float"},
                    {"name": "amplitude", "value": -0.4549282253548838, "type": "float"},
                    {"name": "beta", "value": 7.494904522022295e-10, "type": "float"},
                ],
            },
            DragGaussianWaveform(
                id="wf_drag_gaussian_0",
                sigma=6.369913502160144e-9,
                length=6.000000000000001e-8,
                beta=7.494904522022295e-10,
                amplitude=-0.4549282253548838,
            ),
        ),
        (
            {
                "waveformId": "wf_gaussian_0",
                "name": "gaussian",
                "arguments": [
                    {"name": "length", "value": 6.000000000000001e-8, "type": "float"},
                    {"name": "sigma", "value": 6.369913502160144e-9, "type": "float"},
                    {"name": "amplitude", "value": -0.4549282253548838, "type": "float"},
                ],
            },
            GaussianWaveform(
                id="wf_gaussian_0",
                length=6.000000000000001e-8,
                sigma=6.369913502160144e-9,
                amplitude=-0.4549282253548838,
            ),
        ),
        (
            {
                "waveformId": "wf_constant",
                "name": "constant",
                "arguments": [
                    {"name": "length", "value": 2.1, "type": "float"},
                    {"name": "iq", "value": 0.23, "type": "complex"},
                ],
            },
            ConstantWaveform(id="wf_constant", length=2.1, iq=0.23),
        ),
        (
            {
                "waveformId": "wf_erf_square_0",
                "name": "erf_square",
                "arguments": [
                    {"name": "length", "value": 6.000000000000001e-8, "type": "float"},
                    {"name": "width", "value": 3.000000000000000e-8, "type": "float"},
                    {"name": "sigma", "value": 5.000000000060144e-9, "type": "float"},
                    {"name": "off_center", "value": 4.000000000000000e-9, "type": "float"},
                    {"name": "amplitude", "value": 0.4549282253548838, "type": "float"},
                ],
            },
            ErfSquareWaveform(
                id="wf_erf_square_0",
                length=6.000000000000001e-8,
                width=3.000000000000000e-8,
                sigma=5.000000000060144e-9,
                off_center=4.000000000000000e-9,
                amplitude=0.4549282253548838,
            ),
        ),
    ],
)
def test_parse_waveform_from_calibration_schema(waveform_json, waveform):
    assert _parse_waveform_from_calibration_schema(waveform_json) == waveform
