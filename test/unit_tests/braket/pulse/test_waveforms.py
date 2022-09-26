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


import re
from copy import deepcopy

from oqpy import Program

from braket.pulse import ArbitraryWaveform, ConstantWaveform, DragGaussianWaveform, GaussianWaveform


def test_arbitrary_waveform():
    amps = [complex(1, 2), complex(0.3, -1), 0, 4.2]
    id = "arb_wf_x"
    wf = ArbitraryWaveform(amps, id)
    assert wf.amplitudes == amps
    assert wf.id == id
    oq_exp = wf.to_oqpy_expression()
    assert oq_exp.init_expression == amps
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


def test_constant_waveform():
    length = 4e-3
    iq = 4
    id = "const_wf_x"
    wf = ConstantWaveform(length, iq, id)
    assert wf.length == length
    assert wf.iq == iq
    assert wf.id == id

    p = Program(None)
    p.declare(wf.to_oqpy_expression())
    assert p.to_qasm(include_externs=False) == "waveform const_wf_x = constant(4000000.0ns, 4);"


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

    p = Program(None)
    p.declare(wf.to_oqpy_expression())
    assert (
        p.to_qasm(include_externs=False)
        == "waveform drag_gauss_wf = drag_gaussian(4.0ns, 0.3, 0.6, 0.4, false);"
    )


def test_drag_gaussian_waveform_default_params():
    length = 4e-9
    sigma = 0.3
    beta = 0.6
    wf = DragGaussianWaveform(length, sigma, beta)
    assert re.match(r"[A-Za-z]{10}", wf.id)
    assert wf.zero_at_edges is True
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

    p = Program(None)
    p.declare(wf.to_oqpy_expression())
    assert (
        p.to_qasm(include_externs=False) == "waveform gauss_wf = gaussian(4.0ns, 0.3, 0.4, false);"
    )


def test_gaussian_waveform_default_params():
    length = 4e-9
    sigma = 0.3
    wf = GaussianWaveform(length, sigma)
    assert re.match(r"[A-Za-z]{10}", wf.id)
    assert wf.zero_at_edges is True
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
