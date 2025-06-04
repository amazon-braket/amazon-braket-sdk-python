import pytest
from braket.circuits import Circuit
from braket.circuits.diagram_builders.braket_circuit_drawer import (
    draw_circuit_matplotlib,
    generate_circuit_latex,
    circuit_drawer,
)

from PIL import ImageChops, Image
import io
import os


def test_draw_circuit_matplotlib_runs_without_error():
    circuit = Circuit().h(0).cnot(0, 1).rz(1, 0.5).measure(1)
    fig, ax = draw_circuit_matplotlib(circuit)
    assert fig is not None
    assert ax is not None


def normalize_lines(s):
    return [line.strip() for line in s.strip().splitlines() if line.strip()]


def test_generate_circuit_latex_exact_output():
    circuit = Circuit().h(0).cnot(0, 1).rz(1, 0.5).measure(1)
    latex_code = generate_circuit_latex(circuit, initial_states=["|0>", "|0>"])

    expected_latex = (
        "\\begin{quantikz}\n"
        "\\lstick{|0>} & \\gate{H} & \\ctrl{1} & \\qw & \\qw \\\\\n"
        "\\lstick{|0>} & \\qw & \\targ{} & \\gate{RZ(0.500)} & \\meter{} \\\\\n"
        "\\end{quantikz}"
    )
    print("EXPECTED:", repr(expected_latex.strip()))
    print("GOT     :", repr(latex_code.strip()))
    assert normalize_lines(latex_code) == normalize_lines(expected_latex)


def test_circuit_drawer_matplotlib():
    circuit = Circuit().h(0).rx(0, 3.14)
    fig, ax = circuit_drawer(circuit, style="mpl")
    assert fig is not None and ax is not None


def test_circuit_drawer_latex():
    circuit = Circuit().h(0).x(1).cnot(0, 1)
    latex = circuit_drawer(circuit, style="latex")
    expected = (
        "\\begin{quantikz}\n"
        "\\lstick{\\ket{0}} & \\gate{H} & \\ctrl{1} \\\\n"
        "\\lstick{\\ket{0}} & \\gate{X} & \\targ{} \\\\n"
        "\\end{quantikz}"
    )
    assert latex.strip().startswith("\\begin{quantikz}")
    assert "\\ctrl" in latex and "\\targ" in latex


def test_circuit_drawer_invalid_style():
    circuit = Circuit().x(0)
    with pytest.raises(ValueError, match="Unknown style"):
        circuit_drawer(circuit, style="invalid")
