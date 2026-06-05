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

# == Amazon Braket Interactive Circuit Visualization with Plotly ==
#
# This example demonstrates the interactive Plotly circuit diagram
# renderer.  It requires ``plotly`` — install it with:
#
#     pip install amazon-braket-sdk[interactive]
#
# or:
#     pip install plotly
#
# Usage in a Jupyter notebook:
#     from braket.circuits import Circuit
#     circuit = Circuit().h(0).cnot(0, 1)
#     fig = circuit.show("interactive")   # returns a plotly Figure
#     fig.show()                          # render inline
#
# In a plain Python script the same call returns a ``go.Figure`` that
# can be written to HTML or displayed with ``fig.show()``.

# ---------------------------------------------------------------------------
# 1.  Basic circuit — single- and multi-qubit gates
# ---------------------------------------------------------------------------

from braket.circuits import Circuit, FreeParameter

circ = Circuit()
circ.h(0)
circ.cnot(0, 1)
circ.rz(1, 0.25)
circ.swap(0, 2)

print("=== Basic circuit ===")
print(circ)

fig = circ.show("interactive")
fig.show()

# ---------------------------------------------------------------------------
# 2.  Parameterized gates — tooltips show the parameter values
# ---------------------------------------------------------------------------

theta = FreeParameter("theta")
phi = FreeParameter("phi")

circ2 = Circuit().rx(0, theta).rz(1, phi).cnot(0, 1).rx(2, 0.75)
# Bind some parameters so values appear in the diagram
circ2_bound = circ2.make_bound_circuit({"theta": 1.57, "phi": 3.14})

print("\n=== Parameterized circuit ===")
print(circ2_bound)

fig2 = circ2_bound.show("interactive")
fig2.show()

# ---------------------------------------------------------------------------
# 3.  Verbatim boxes — expand / collapse demo
# ---------------------------------------------------------------------------
# Verbatim boxes protect sub-circuits from compiler optimisations.
# The Plotly renderer shows them collapsed by default; click the button
# above the diagram to expand and inspect the inner gates.

inner = Circuit().h(0).cnot(0, 1).rz(1, 0.5)
circ3 = Circuit().x(0).add_verbatim_box(inner).cnot(0, 1)

print("\n=== Circuit with verbatim box ===")
print(circ3)

fig3 = circ3.show("interactive")
fig3.show()

# ---------------------------------------------------------------------------
# 4.  Large circuit — zoom & pan
# ---------------------------------------------------------------------------
# Plotly's built-in zoom and pan make large circuits easy to navigate.

circ4 = Circuit()
for q in range(8):
    circ4.h(q)
for q in range(7):
    circ4.cnot(q, q + 1)

print("\n=== Large circuit (8 qubits, 7 entangling steps) ===")
print(circ4)

fig4 = circ4.show("interactive")
fig4.show()

# ---------------------------------------------------------------------------
# 5.  Result types — additional columns in the diagram
# ---------------------------------------------------------------------------

from braket.circuits import Observable

circ5 = (
    Circuit()
    .h(0)
    .cnot(0, 1)
    .expectation(observable=Observable.Z(), target=0)
    .variance(observable=Observable.Y(), target=1)
    .state_vector()
)

print("\n=== Circuit with result types ===")
print(circ5)

fig5 = circ5.show("interactive")
fig5.show()

# ---------------------------------------------------------------------------
# 6.  Saving to HTML (no Jupyter required)
# ---------------------------------------------------------------------------

fig = circ.show("interactive")
fig.write_html("circuit_diagram.html")
print("\nSaved interactive diagram to circuit_diagram.html")

# ---------------------------------------------------------------------------
# 7.  Further information
# ---------------------------------------------------------------------------
# - Hover over any gate to see its name, target qubits, and parameters.
# - Use the toolbar (zoom, pan, reset) to navigate the diagram.
# - Verbatim boxes have a toggle button above the diagram to expand/collapse.
