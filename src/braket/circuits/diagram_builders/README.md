# Braket Circuit Drawer

A lightweight Python module to visualize Braket `Circuit` objects using Matplotlib or to export them as LaTeX (quantikz) code.  
Inspired by Qiskit’s `circuit_drawer`, this package supports common single-qubit gates, parameterized rotations, controlled gates (CNOT, Toffoli), multi-qubit gates, and multi-qubit measurements.

---

## Features

- **Matplotlib Rendering** (`style='mpl'`):
  - Draws horizontal wires for each qubit.
  - Renders single-qubit gates (`H`, `X`, `Y`, `Z`, `S`, `T`, etc.).
  - Displays parameterized rotations (`RX`, `RY`, `RZ`, `PHASE`, `U3`) with numeric angles (rounded to 3 decimals).
  - Draws controlled gates:
    - **CNOT / CX**: control dot + target ⨁ symbol, connected by a vertical line.
    - **Toffoli / CCX / CCNOT**: two control dots + target ⨁, connected by a line spanning three qubits.
  - Draws generic multi-qubit gates as a vertical rectangle spanning involved qubits.
  - Supports multi-qubit measurements: each measured qubit shows a “meter” symbol.

- **LaTeX Export** (`style='latex'`):
  - Produces a `quantikz` environment ready to paste into a `.tex` file.
  - `\gate{…}` for single-qubit and parameterized gates (angles rounded to 3 decimals).
  - `\ctrl{δ}` and `\targ{}` for CNOT/CX and Toffoli/CCX.
  - Places `\meter{}` on each measured qubit.
  - Uses `\gate[wires=…]{…}` for other multi-qubit gates.
  - Optional `initial_states` parameter: specify custom `\lstick{…}` labels (e.g. `['|0>', '|+>']`) for each qubit.

---

## Installation

1. **(Recommended) Create a virtual environment**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate          # On Windows: venv\Scripts\activate
   pip install -e .
   ```

---

## Usage Example

```python
from braket.circuits import Circuit
from braket.circuits.diagram_builders.braket_circuit_drawer import circuit_drawer
import matplotlib.pyplot as plt

circuit = Circuit().h(0).cnot(0, 1).rz(1, 0.5).measure(0, 1)

# Draw with Matplotlib
fig, ax = circuit_drawer(circuit, style='mpl', figsize=(6, 4))
plt.show()

# Generate LaTeX (quantikz)
latex_code = circuit_drawer(circuit, style='latex', initial_states=['|0>', '|0>'])
print(latex_code)
```

---

## Testing

To run unit tests and lint checks:

```bash
tox -e unit-tests
ruff check src --fix
```

Ensure `expected_circuit.png` is present for image diff testing.
