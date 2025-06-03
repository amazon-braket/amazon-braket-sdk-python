import pytest
from braket.circuits import Circuit
from braket.circuits.diagram_builders.braket_circuit_drawer import (
    draw_circuit_matplotlib,
    generate_circuit_latex,
    circuit_drawer,
)

def test_draw_circuit_matplotlib_runs_without_error():
    circuit = Circuit().h(0).cnot(0, 1).rz(1, 0.5).measure(1)
    fig, ax = draw_circuit_matplotlib(circuit)
    assert fig is not None
    assert ax is not None
    # No assertions on the figure itself, just that it was generated.

def test_generate_circuit_latex_output():
    circuit = Circuit().h(0).cnot(0, 1).rz(1, 0.5).measure(1)
    latex_code = generate_circuit_latex(circuit, initial_states=["|0>", "|0>"])
    assert "\\begin{quantikz}" in latex_code
    assert "\\gate{H}" in latex_code or "\\gate{H(1)}" in latex_code
    assert "\\ctrl" in latex_code
    assert "\\targ" in latex_code
    assert "\\meter{}" in latex_code
    assert "\\end{quantikz}" in latex_code

def test_circuit_drawer_matplotlib():
    circuit = Circuit().h(0).rx(0, 3.14)
    fig, ax = circuit_drawer(circuit, style="mpl")
    assert fig is not None and ax is not None

def test_circuit_drawer_latex():
    circuit = Circuit().h(0).x(1).cnot(0, 1)
    latex = circuit_drawer(circuit, style="latex")
    assert isinstance(latex, str)
    assert "\\begin{quantikz}" in latex

def test_circuit_drawer_invalid_style():
    circuit = Circuit().x(0)
    with pytest.raises(ValueError, match="Unknown style"):
        circuit_drawer(circuit, style="invalid")
