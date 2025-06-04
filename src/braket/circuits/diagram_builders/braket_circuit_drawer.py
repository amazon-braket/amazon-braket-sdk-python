"""
braket_circuit_drawer.py

Provides functionality to visualize Braket `Circuit` objects using Matplotlib
or to generate LaTeX (quantikz) code. Inspired by Qiskit's `circuit_drawer`.

Main functions:
- draw_circuit_matplotlib(circuit, figsize=(None, None), dx=1.5, dy=1.0):
    Draws a Braket `Circuit` using Matplotlib, including parameterized gates and
    multi-qubit measurements.

- generate_circuit_latex(circuit, initial_states=None):
    Generates a string of LaTeX code (quantikz) that represents the circuit.
    Parameterized gates show their angles (rounded to 3 decimals). Multi-qubit
    measurements put a `\\meter{}` on each measured qubit.

- circuit_drawer(circuit, style='mpl', **kwargs):
    High-level function to choose between 'mpl' (Matplotlib) or 'latex' output.

Usage example:
    from braket.circuits import Circuit
    from braket.circuits.diagram_builders.braket_circuit_drawer import circuit_drawer
    import matplotlib.pyplot as plt

    circuit = Circuit().h(0).cnot(0, 1).rx(1, 3.14159).measure(0, 1)

    # 1) Visualize with Matplotlib:
    fig, ax = circuit_drawer(circuit, style='mpl', figsize=(6, 4))
    plt.show()

    # 2) Get LaTeX code (quantikz):
    latex_code = circuit_drawer(circuit, style='latex', initial_states=['|0>', '|0>'])
    print(latex_code)
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

PARAMETERIZED_GATES = {"RX", "RY", "RZ", "PHASE", "U3"}
CONTROL_GATES = {"CNOT", "CX"}
TOFFOLI_GATES = {"TOFFOLI", "CCX", "CCNOT"}


def parse_circuit(circuit):
    instructions = []
    max_qubit_index = -1

    for idx, instr in enumerate(circuit.instructions):
        try:
            gate_name = instr.operator.__class__.__name__.upper()
        except Exception:
            gate_name = str(instr.operator).upper()

        qubits = []
        if hasattr(instr, "target"):
            try:
                qubits = list(instr.target)
            except Exception:
                qubits = [instr.target] if instr.target is not None else []
        elif hasattr(instr, "targets"):
            qubits = list(instr.targets)

        if qubits:
            max_qubit_index = max(max_qubit_index, max(qubits))

        instructions.append({
            "gate": gate_name,
            "qubits": qubits,
            "col_index": idx,
            "instr": instr,
        })

    n_qubits = (max_qubit_index + 1) if max_qubit_index >= 0 else 0
    return instructions, n_qubits


def draw_circuit_matplotlib(circuit, figsize=(8, 6), dx=1.5, dy=1.0):
    instructions, n_qubits = parse_circuit(circuit)
    if n_qubits == 0:
        raise ValueError("The circuit contains no qubits to visualize.")

    if figsize[0] is None or figsize[1] is None:
        width = (len(instructions) + 2) * dx
        height = (n_qubits + 2) * dy
        fig, ax = plt.subplots(figsize=(width, height))
    else:
        fig, ax = plt.subplots(figsize=figsize)

    ax.set_aspect("equal")
    ax.axis("off")

    def y_of(q):
        return -q * dy

    x_min = -dx
    x_max = (len(instructions) + 1) * dx
    for q in range(n_qubits):
        y = y_of(q)
        ax.hlines(y, x_min, x_max, color="black", linewidth=1.0)

    def _draw_meter(x_ctr, yq, size=0.15 * dy):
        circle = Circle((x_ctr, yq), size, fill=False, edgecolor="black", linewidth=1.0)
        ax.add_patch(circle)
        ax.hlines(yq + size * 0.3, x_ctr - size * 0.5, x_ctr + size * 0.5, color="black", linewidth=1.0)
        ax.vlines(x_ctr, yq - size * 0.3, yq + size * 0.3, color="black", linewidth=1.0)

    for instr_dict in instructions:
        gate = instr_dict["gate"]
        qubits = instr_dict["qubits"]
        col = instr_dict["col_index"]
        instr = instr_dict["instr"]
        x_ctr = col * dx

        if not qubits:
            continue

        if len(qubits) == 1 and gate in PARAMETERIZED_GATES:
            q = qubits[0]
            yq = y_of(q)
            angle = getattr(instr.operator, "angle", None)
            label = f"{gate}({angle:.3f})" if angle is not None else gate
            rect = Rectangle((x_ctr - 0.4 * dx, yq - 0.3 * dy), 0.8 * dx, 0.6 * dy, facecolor="white", edgecolor="black")
            ax.add_patch(rect)
            ax.text(x_ctr, yq, label, ha="center", va="center", fontsize=8)

        elif len(qubits) == 1 and gate not in CONTROL_GATES.union(TOFFOLI_GATES).union({"MEASURE"}):
            q = qubits[0]
            yq = y_of(q)
            rect = Rectangle((x_ctr - 0.4 * dx, yq - 0.3 * dy), 0.8 * dx, 0.6 * dy, facecolor="white", edgecolor="black")
            ax.add_patch(rect)
            ax.text(x_ctr, yq, gate, ha="center", va="center", fontsize=8)

        elif gate in CONTROL_GATES and len(qubits) == 2:
            q_ctrl, q_tgt = qubits
            y_ctrl, y_tgt = y_of(q_ctrl), y_of(q_tgt)
            r = 0.1 * dy
            ax.add_patch(Circle((x_ctr, y_ctrl), r, color="black"))
            ax.add_patch(Circle((x_ctr, y_tgt), r, fill=False, edgecolor="black"))
            ax.text(x_ctr, y_tgt, "+", ha="center", va="center", fontsize=8)
            ax.vlines(x_ctr, min(y_ctrl, y_tgt) + r, max(y_ctrl, y_tgt) - r, color="black", linewidth=1.0)

        elif gate in TOFFOLI_GATES and len(qubits) == 3:
            q1, q2, qt = qubits
            y1, y2, yt = y_of(q1), y_of(q2), y_of(qt)
            r = 0.1 * dy
            for y in [y1, y2]:
                ax.add_patch(Circle((x_ctr, y), r, color="black"))
            ax.add_patch(Circle((x_ctr, yt), r, fill=False, edgecolor="black"))
            ax.text(x_ctr, yt, "+", ha="center", va="center", fontsize=8)
            ax.vlines(x_ctr, min(y1, y2, yt) + r, max(y1, y2, yt) - r, color="black", linewidth=1.0)

        elif gate == "MEASURE":
            for q in qubits:
                _draw_meter(x_ctr, y_of(q))

        else:
            y_vals = [y_of(q) for q in qubits]
            y_top, y_bot = max(y_vals) + 0.3 * dy, min(y_vals) - 0.3 * dy
            rect = Rectangle((x_ctr - 0.4 * dx, y_bot), 0.8 * dx, y_top - y_bot, facecolor="white", edgecolor="black")
            ax.add_patch(rect)
            ax.text(x_ctr, (y_top + y_bot) / 2, gate, ha="center", va="center", fontsize=8)

    ax.set_xlim(x_min, x_max + dx)
    ax.set_ylim(-n_qubits * dy - dy / 2, dy / 2)
    plt.tight_layout()
    return fig, ax


def generate_circuit_latex(circuit, initial_states=None):
    instructions, n_qubits = parse_circuit(circuit)
    if n_qubits == 0:
        raise ValueError("The circuit contains no qubits to generate LaTeX.")

    n_cols = len(instructions)
    matrix = [["\\qw" for _ in range(n_cols)] for _ in range(n_qubits)]

    for instr_dict in instructions:
        gate = instr_dict["gate"]
        qubits = instr_dict["qubits"]
        col = instr_dict["col_index"]
        instr = instr_dict["instr"]

        if not qubits:
            continue

        if len(qubits) == 1 and gate in PARAMETERIZED_GATES:
            q = qubits[0]
            angle = getattr(instr.operator, "angle", None)
            label = f"{gate}({angle:.3f})" if angle is not None else gate
            matrix[q][col] = f"\\gate{{{label}}}"

        elif len(qubits) == 1 and gate not in CONTROL_GATES.union(TOFFOLI_GATES).union({"MEASURE"}):
            q = qubits[0]
            matrix[q][col] = f"\\gate{{{gate}}}"

        elif gate in CONTROL_GATES and len(qubits) == 2:
            q_ctrl, q_tgt = qubits
            delta = q_tgt - q_ctrl
            matrix[q_ctrl][col] = f"\\ctrl{{{delta}}}"
            matrix[q_tgt][col] = "\\targ{}"

        elif gate in TOFFOLI_GATES and len(qubits) == 3:
            q1, q2, qt = qubits
            matrix[q1][col] = f"\\ctrl{{{qt - q1}}}"
            matrix[q2][col] = f"\\ctrl{{{qt - q2}}}"
            matrix[qt][col] = "\\targ{}"

        elif gate == "MEASURE":
            for q in qubits:
                matrix[q][col] = "\\meter{}"

        else:
            top = min(qubits)
            wires = len(qubits)
            matrix[top][col] = f"\\gate[wires={wires}]{{{gate}}}"
            for q in qubits[1:]:
                matrix[q][col] = ""

    lines = ["\\begin{quantikz}"]
    for q in range(n_qubits):
        label = initial_states[q] if initial_states and q < len(initial_states) else "\\lstick{\\ket{0}}"
        row_tokens = [label] + matrix[q]
        lines.append(" & ".join(row_tokens) + " \\")
    lines.append("\\end{quantikz}")
    return "\n".join(lines)


def circuit_drawer(circuit, style="mpl", **kwargs):
    if style == "mpl":
        return draw_circuit_matplotlib(circuit, **kwargs)
    elif style == "latex":
        return generate_circuit_latex(circuit, **kwargs)
    else:
        raise ValueError("Unknown style: must be 'mpl' or 'latex'.")
