#Copyright 2025 Zachary L. Musselwhite
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as patheffects
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.image as mpimg
import os

import sys

font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'AVFontimerMedium.ttf')
if os.path.exists(font_path):
    prop = fm.FontProperties(fname=font_path)
else:
    print(f"[Warning] Custom font not found at {font_path}. Using default font.", file=sys.stderr)
    prop = fm.FontProperties()

# Map gate types to icon filenames
ICON_MAP = {
    'H': 'h-gate.png',
    'X': 'x-gate.png',
    'Y': 'y-gate.png',
    'Z': 'z-gate.png',
    'S': 's-gate.png',
    'T': 't-gate.png',
    'RX': 'rx-gate.png',
    'RY': 'ry-gate.png',
    'RZ': 'rz-gate.png',
    'C': 'cnot.png',         # CNOT control
    'CNOT': 'cnot.png',
    'CZ': 'cz-gate.png',
    'SWAP': 'swap.png',
    'W': 'w.png',    # Alias for SWAP
    'M': 'measure.png',
    'I': 'i-gate.png',
    '?': 'question.png',
}
ICON_DIR = os.path.join(os.path.dirname(__file__), 'icons')
ICON_SIZE = 128  # pixels

# Cache loaded icons to avoid reloading
_icon_img_cache = {}


def xs_draw(qiskit_circuit, qubit_labels=None):
    """
    Convert a Qiskit QuantumCircuit to the internal matrix format and draw it with the custom style.
    Gates acting on different qubits in the same time step are grouped, matching Qiskit's visual timing.
    Args:
        qiskit_circuit: Qiskit QuantumCircuit object
        qubit_labels: Optional list of labels for the qubits
    """
    try:
        from qiskit.circuit import Measure
    except ImportError:
        raise ImportError("Qiskit is required for xs_draw. Please install qiskit.")

    num_qubits = qiskit_circuit.num_qubits
    qubits = list(qiskit_circuit.qubits)
    ops = qiskit_circuit.data

    # Each time step is a list of lists (per qubit, per timestep)
    time_steps = []
    # For each qubit, track the next available time step
    qubit_available = [0] * num_qubits

    # Helper: find earliest time step where all qargs are available
    def find_earliest(q_indices):
        return max(qubit_available[q] for q in q_indices)

    for op, qargs, cargs in ops:
        name = op.name.upper()
        q_indices = [qubits.index(q) for q in qargs]
        step_idx = find_earliest(q_indices)

        # Ensure no other gate is scheduled on any involved qubit at this time step
        while True:
            # Extend time_steps if needed
            while len(time_steps) <= step_idx:
                time_steps.append([[] for _ in range(num_qubits)])
            # Check if all involved qubits are free at this step (empty or only I)
            if all(not time_steps[step_idx][q] or time_steps[step_idx][q] == ['I'] for q in q_indices):
                break
            step_idx += 1

        # Place the gate(s)
        if name in ['MEASURE']:
            for q in q_indices:
                if not time_steps[step_idx][q] or time_steps[step_idx][q] == ['I']:
                    time_steps[step_idx][q] = ['M']
                else:
                    time_steps[step_idx][q].append('M')
        elif name in ['CX', 'CNOT']:
            if len(q_indices) == 2:
                # Control
                ctrl = q_indices[0]
                tgt = q_indices[1]
                # Control cell
                if not time_steps[step_idx][ctrl] or time_steps[step_idx][ctrl] == ['I']:
                    time_steps[step_idx][ctrl] = ['C']
                else:
                    if 'C' not in time_steps[step_idx][ctrl]:
                        time_steps[step_idx][ctrl].append('C')
                # Target cell: allow coexistence of CNOT 'X' and X gate
                cell = time_steps[step_idx][tgt]
                if not cell or cell == ['I']:
                    time_steps[step_idx][tgt] = ['X']
                else:
                    # If already has 'X' (from X gate), append CNOT 'X' if not present
                    if cell.count('X') == 1:
                        # If only one X, append another for overlay
                        time_steps[step_idx][tgt].append('X')
                    elif 'X' not in cell:
                        time_steps[step_idx][tgt].append('X')
        elif name in ['SWAP']:
            for q in q_indices:
                if not time_steps[step_idx][q] or time_steps[step_idx][q] == ['I']:
                    time_steps[step_idx][q] = ['SWAP']
                else:
                    time_steps[step_idx][q].append('SWAP')
        elif name in ['RX', 'RY', 'RZ']:
            for q in q_indices:
                if not time_steps[step_idx][q] or time_steps[step_idx][q] == ['I']:
                    time_steps[step_idx][q] = [name]
                else:
                    time_steps[step_idx][q].append(name)
        else:
            for q in q_indices:
                if not time_steps[step_idx][q] or time_steps[step_idx][q] == ['I']:
                    time_steps[step_idx][q] = [name]
                else:
                    time_steps[step_idx][q].append(name)
        # Update qubit availability
        for q in q_indices:
            qubit_available[q] = step_idx + 1
    # Store lists of gates per cell
    n_steps = len(time_steps)
    circuit_matrix = [[[] for _ in range(n_steps)] for _ in range(num_qubits)]
    for col in range(n_steps):
        for row in range(num_qubits):
            vals = time_steps[col][row]
            if isinstance(vals, list):
                circuit_matrix[row][col].extend(vals)
            elif vals != 'I':
                circuit_matrix[row][col].append(vals)
    if qubit_labels is None:
        qubit_labels = [f"{q._register.name}_{q._index}" for q in qubits]
    circuit(circuit_matrix, qubit_labels[::-1])

def _get_icon_img(gate_upper):
    fname = ICON_MAP.get(gate_upper, ICON_MAP['?'])
    path = os.path.join(ICON_DIR, fname)
    if path not in _icon_img_cache:
        print(f"[DEBUG] Attempting to load icon for gate '{gate_upper}': {path}")
        if os.path.exists(path):
            img = mpimg.imread(path)
            img = np.flipud(img)
            print(f"[DEBUG] Loaded icon: {path}")
        else:
            fallback = os.path.join(ICON_DIR, ICON_MAP['?'])
            print(f"[WARNING] Icon file not found for gate '{gate_upper}' at {path}. Using fallback: {fallback}")
            img = mpimg.imread(fallback)
            img = np.flipud(img)
        _icon_img_cache[path] = img
    return _icon_img_cache[path]

def _add_glow(ax, x, y, color, size=0.3, alpha=0.3, zorder=1):
    # Add a radial glow effect using scatter
    glow_radii = np.linspace(size, size * 2, 10)
    for r in glow_radii:
        this_alpha = alpha / (r * 2)
        this_alpha = max(0.0, min(this_alpha, 1.0))  # Clamp to [0, 1]
        ax.scatter([x], [y], s=(r * 900), color=color, alpha=this_alpha, zorder=zorder)

def _draw_gate_icon(ax, x, y, gate, color, prop, zorder=3, y2=None):
    """Draw the PNG icon for the gate at (x, y) with a fixed size (128x128px), or from y to y2 if tall (CNOT)."""
    gate = str(gate)
    gate_upper = gate.upper()
    img = _get_icon_img(gate_upper)

    if y2 is not None and gate_upper == 'C':
        # Draw taller CNOT icon from y (control) to y2 (target), with 75% opacity
        y_top = min(y, y2)
        y_bot = max(y, y2)
        # Make it a bit taller (increase padding)
        icon_extent = [x - 0.35, x + 0.35, y_top - 0.15, y_bot + 0.30]
        ax.imshow(img, extent=icon_extent, zorder=zorder, origin='upper', alpha=0.75)
    else:
        # Default: center in cell
        icon_extent = [x - 0.35, x + 0.35, y - 0.35, y + 0.35]
        ax.imshow(img, extent=icon_extent, zorder=zorder, origin='upper')
    # Optionally, draw a glow behind the icon
    # All vector drawing code removed. Only PNG icon rendering and glow remain.
    # If you want to display a gate label on top of the icon, you can add it here using ax.text, using the 'color' parameter for consistency.

def circuit(circuit_matrix, qubit_labels=None):
    """
    Draws a quantum circuit diagram with a futuristic neon look and unique gate icons.

    Args:
        circuit_matrix (list of lists): Rows are qubits, columns are time steps.
        qubit_labels (list of str, optional): Labels for the qubits.
    """
    num_qubits = len(circuit_matrix)
    if num_qubits == 0:
        print("Cannot draw an empty circuit.")
        return
    num_steps = len(circuit_matrix[0]) if num_qubits > 0 else 0
    if qubit_labels is None:
        qubit_labels = [f'q{i}' for i in range(num_qubits)]
    elif len(qubit_labels) != num_qubits:
        raise ValueError("Number of qubit labels must match the number of qubits.")

    # --- Futuristic style settings ---
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(num_steps + 1.5, num_qubits + 1))
    fig.patch.set_facecolor('#10131a')
    ax.set_facecolor('#181c27')

    ax.set_xlim(-0.6, num_steps - 0.4)
    ax.set_ylim(-0.6, num_qubits - 0.4)
    ax.set_yticks(range(num_qubits))
    ax.set_yticklabels(reversed(qubit_labels), fontsize=14, color='#00ffe7', fontweight='bold', fontproperties=prop)
    ax.set_xticks(range(num_steps))
    ax.set_xticklabels([f"t{t}" for t in range(num_steps)], fontsize=12, color='#00ffe7', fontweight='bold', fontproperties=prop)
    ax.set_xlabel("Time Steps", fontsize=13, color='#00ffe7', labelpad=16, fontproperties=prop)
    ax.invert_yaxis()
    ax.grid(False)

    # Draw a neon grid
    for i in range(num_qubits):
        ax.plot([-0.5, num_steps - 0.5], [i, i], color='#0fffc3', lw=2, alpha=0.25, zorder=0)
    for j in range(num_steps):
        ax.plot([j, j], [-0.5, num_qubits - 0.5], color='#0fffc3', lw=1, alpha=0.10, zorder=0)

    # Draw gates with unique futuristic icons
    num_qubits = len(circuit_matrix)
    num_steps = len(circuit_matrix[0]) if num_qubits > 0 else 0
    for step_idx in range(num_steps):
        # Check for CNOT in this column
        col_gates = [circuit_matrix[q][step_idx] for q in range(num_qubits)]
        if any('C' in cell for cell in col_gates) and any('X' in cell for cell in col_gates):
            # Find control and target rows
            ctrl_row = next(q for q, cell in enumerate(col_gates) if 'C' in cell)
            tgt_row = next(q for q, cell in enumerate(col_gates) if 'X' in cell)
            # Always draw X-gate icon at target cell if present
            if 'X' in col_gates[tgt_row]:
                _draw_gate_icon(ax, step_idx, tgt_row, 'X', color='#00ffe7', prop=prop, zorder=3)
            # Draw CNOT icon tall from ctrl_row to tgt_row (overlays X gate)
            _draw_gate_icon(ax, step_idx, ctrl_row, 'C', color='#00ffe7', prop=prop, zorder=4, y2=tgt_row)
            # Draw other gates in this column (skip C/X at ctrl/tgt)
            for qubit_idx, gates in enumerate(col_gates):
                for g in gates:
                    if (qubit_idx == ctrl_row and g == 'C') or (qubit_idx == tgt_row and g == 'X'):
                        continue
                    _draw_gate_icon(ax, step_idx, qubit_idx, g, color='#00ffe7', prop=prop, zorder=3)
        else:
            # No CNOT: draw all gates as usual
            for qubit_idx, gates in enumerate(col_gates):
                for g in gates:
                    _draw_gate_icon(ax, step_idx, qubit_idx, g, color='#00ffe7', prop=prop, zorder=3)

    # Add drop shadow for title
    ax.set_title(
        "Quantum Circuit (Futuristic)", fontsize=20, color='#00ffe7', pad=22,
        fontweight='bold', fontproperties=prop,
        loc='center'
    )
    ax.tick_params(axis='both', which='both', length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.tight_layout(pad=3.5)
    plt.subplots_adjust(left=0.18, right=0.82, top=0.85, bottom=0.18)
    plt.savefig('output.png', bbox_inches='tight')
    plt.close()

def example():
    """
    An example of how to use the circuit drawing function.
    """
    # A simple 3-qubit circuit
    example_circuit = [
        ['H', 'X', 'I'],  # Qubit 0
        ['I', 'Z', 'Y'],  # Qubit 1
        ['Y', 'I', 'H'],  # Qubit 2
    ]
    print("Drawing an example circuit.")
    circuit(example_circuit, qubit_labels=['Q0', 'Q1', 'Ancilla'])

def complex_example():
    """
    Draws a complex quantum circuit with all gate types and multiple time steps.
    """
    complex_circuit = [
        ['H', 'X', 'RX', 'CZ', 'SWAP', 'Y', 'I', 'Z', 'RY', 'M'],
        ['I', 'CZ', 'C', 'X', 'S', 'T', 'RZ', 'SWAP', 'H', '?'],
        ['S', 'T', 'Y', 'I', 'C', 'CZ', 'RX', 'M', 'SWAP', 'Z'],
        ['C', 'X', 'SWAP', 'RY', 'RZ', 'H', 'Y', 'I', 'T', 'M'],
    ]
    labels = ['Q0', 'Q1', 'Q2', 'Q3']
    print("Drawing a complex circuit.")
    circuit(complex_circuit, qubit_labels=labels)

def icon_example():
    """
    Draws a circuit with all major gate types/icons for preview.
    """
    # Each column is a time step; each row is a qubit
    # For CNOT/CZ/SWAP, use placeholders (e.g. 'C', 'X', 'Z', 'S', 'W')
    icon_circuit = [
        ['H', 'X', 'Y', 'Z', 'S', 'T', 'Rx', 'Ry', 'Rz', 'C', 'C', 'S', 'M', 'I', '?'],  # Qubit 0
        ['I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'X', 'Z', 'W', 'M', 'I', 'I'],     # Qubit 1 (for CNOT, CZ, SWAP, etc)
    ]
    labels = ['Q0', 'Q1']
    print("Drawing an icon preview circuit.")
    circuit(icon_circuit, qubit_labels=labels)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'icons':
        icon_example()
    elif len(sys.argv) > 1 and sys.argv[1] == 'complex':
        complex_example()
    else:
        example()
