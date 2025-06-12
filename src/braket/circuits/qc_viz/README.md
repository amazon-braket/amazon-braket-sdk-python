# q-draw-xs


A futuristic, neon-style quantum circuit drawer for Qiskit circuits. Draws with custom PNG icons and supports CNOT/X overlays as in Qiskit diagrams.

## Installation

```bash
git clone https://github.com/xs-es/q-draw-xs.git
```

## Usage

```python
from q_draw_xs import xs_draw
from qiskit import QuantumCircuit

qc = QuantumCircuit(3, 3)
qc.h(0)
qc.x(1)
qc.cx(0, 1)
qc.measure([0, 1, 2], [0, 1, 2])

xs_draw(qc)
```

## CLI Test

```bash
python circuit-test.py
```

## Features
- Neon PNG icon overlay
- Qiskit-style CNOT/X overlay
- Customizable icons and fonts

![image](https://github.com/user-attachments/assets/a65e6bc9-8378-4733-a609-7bbf1d3395a8)


