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

from oqpy import Program

from braket.pulse import ArbitraryWaveform, ConstantWaveform, DragGaussianWaveform, GaussianWaveform


def test_arbitrary_waveform():
    amps = [complex(1, 2), complex(0.3, -1), 0, 4.2]
    name = "arb_wf_x"
    wf = ArbitraryWaveform(amps, name)
    assert wf.amplitudes == amps
    assert wf.name == name
    oq_exp = wf.to_oqpy_expression()
    assert oq_exp.init_expression == amps
    assert oq_exp.name == wf.name


def test_arbitrary_waveform_default_params():
    amps = [1, 4, 5]
    wf = ArbitraryWaveform(amps)
    assert wf.amplitudes == amps
    assert re.match(r"[A-Za-z]{10}", wf.name)


def test_constant_waveform():
    length = 4e-3
    iq = 4
    name = "const_wf_x"
    wf = ConstantWaveform(length, iq, name)
    assert wf.length == length
    assert wf.iq == iq
    assert wf.name == name

    p = Program(None)
    p.declare(wf.to_oqpy_expression())
    assert p.to_qasm(include_externs=False) == "waveform const_wf_x = constant(4000000.0ns, 4);"


def test_constant_waveform_default_params():
    amps = [1, 4, 5]
    wf = ArbitraryWaveform(amps)
    assert wf.amplitudes == amps
    assert re.match(r"[A-Za-z]{10}", wf.name)


def test_drag_gaussian_waveform():
    length = 4e-9
    sigma = 0.3
    beta = 0.6
    amplitude = 0.4
    zero_at_edges = False
    name = "drag_gauss_wf"
    wf = DragGaussianWaveform(length, sigma, beta, amplitude, zero_at_edges, name)
    assert wf.name == name
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
    assert re.match(r"[A-Za-z]{10}", wf.name)
    assert wf.zero_at_edges is True
    assert wf.amplitude == 1
    assert wf.beta == beta
    assert wf.sigma == sigma
    assert wf.length == length


def test_gaussian_waveform():
    length = 4e-9
    sigma = 0.3
    amplitude = 0.4
    zero_at_edges = False
    name = "gauss_wf"
    wf = GaussianWaveform(length, sigma, amplitude, zero_at_edges, name)
    assert wf.name == name
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
    assert re.match(r"[A-Za-z]{10}", wf.name)
    assert wf.zero_at_edges is True
    assert wf.amplitude == 1
    assert wf.sigma == sigma
    assert wf.length == length
