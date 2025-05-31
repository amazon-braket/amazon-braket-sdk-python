"""
braket_circuit_drawer.py

Provides functionality to visualize AWS Braket `Circuit` objects using Matplotlib
or to generate LaTeX (quantikz) code. Inspired by Qiskit's `circuit_drawer`.

Main functions:
- draw_circuit_matplotlib(circuit, figsize=(None, None), dx=1.5, dy=1.0):
    Draws a Braket `Circuit` using Matplotlib, including parameterized gates and
    multi-qubit measurements.

- generate_circuit_latex(circuit, initial_states=None):
    Generates a string of LaTeX code (quantikz) that represents the circuit.
    Parameterized gates show their angles (rounded to 3 decimals). Multi-qubit
    measurements put a `\meter{}` on each measured qubit.

- circuit_drawer(circuit, style='mpl', **kwargs):
    High-level function to choose between 'mpl' (Matplotlib) or 'latex' output.

Usage example:
    from braket.circuits import Circuit
    from braket_circuit_drawer import circuit_drawer
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


def parse_circuit(circuit):
    """
    Parse a Braket Circuit object and extract a list of instructions with:
      - gate: uppercase name of the gate (string)
      - qubits: list of target qubit indices
      - col_index: integer column index (order in circuit.instructions)
      - instr: the original instruction object (to extract parameters)

    Returns:
      - instructions: list of dicts, each with keys 'gate', 'qubits', 'col_index', 'instr'
      - n_qubits: total number of qubits used (max index + 1) or 0 if none
    """
    instructions = []
    max_qubit_index = -1

    for idx, instr in enumerate(circuit.instructions):
        # 1) Attempt to get a clean gate name from the operator's class name
        try:
            gate_name = instr.operator.__class__.__name__.upper()
        except Exception:
            # Fallback to str() if class name is not available
            gate_name = str(instr.operator).upper()

        # 2) Extract the qubit targets. Braket uses 'target' or 'targets'
        qubits = []
        if hasattr(instr, "target"):
            try:
                qubits = list(instr.target)
            except Exception:
                qubits = [instr.target] if instr.target is not None else []
        elif hasattr(instr, "targets"):
            qubits = list(instr.targets)

        # Keep track of the highest qubit index
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
    """
    Draw a Braket Circuit using Matplotlib.

    Parameters:
      - circuit: braket.circuits.Circuit object
      - figsize: tuple (width, height) in inches. If any is None, computes size automatically.
      - dx: horizontal spacing between columns
      - dy: vertical spacing between qubit wires

    Returns:
      - fig, ax: Matplotlib Figure and Axes instances
    """
    instructions, n_qubits = parse_circuit(circuit)
    if n_qubits == 0:
        raise ValueError("The circuit contains no qubits to visualize.")

    # Compute figure size if not explicitly provided
    if figsize[0] is None or figsize[1] is None:
        width = (len(instructions) + 2) * dx
        height = (n_qubits + 2) * dy
        fig, ax = plt.subplots(figsize=(width, height))
    else:
        fig, ax = plt.subplots(figsize=figsize)

    ax.set_aspect("equal")
    ax.axis("off")

    def y_of(q):
        # Map qubit index q to a y-coordinate: q=0 → y=0, q=1 → y=-dy, etc.
        return -q * dy

    # Draw horizontal “wires” for each qubit
    x_min = -dx
    x_max = (len(instructions) + 1) * dx
    for q in range(n_qubits):
        y = y_of(q)
        ax.hlines(y, x_min, x_max, color="black", linewidth=1.0)

    # Helper to draw a measurement “meter” symbol at (x_ctr, yq)
    def _draw_meter(x_ctr, yq, size=0.15 * dy):
        # A circle with no fill and a “⎲”-like tick inside
        circle = Circle((x_ctr, yq), size, fill=False, edgecolor="black", linewidth=1.0)
        ax.add_patch(circle)
        # Draw a small “T” shape inside to indicate a meter
        # Horizontal cap
        ax.hlines(yq + size * 0.3, x_ctr - size * 0.5, x_ctr + size * 0.5, color="black", linewidth=1.0)
        # Vertical stem
        ax.vlines(x_ctr, yq - size * 0.3, yq + size * 0.3, color="black", linewidth=1.0)

    # Iterate over instructions to draw gates
    for instr_dict in instructions:
        gate = instr_dict["gate"]
        qubits = instr_dict["qubits"]
        col = instr_dict["col_index"]
        instr = instr_dict["instr"]
        x_ctr = col * dx

        if not qubits:
            continue  # ignore instructions with no qubits

        # 1) Single-qubit parameterized gates (RX, RY, RZ, PHASE, U3, etc.)
        if len(qubits) == 1 and gate in ["RX", "RY", "RZ", "PHASE", "U3"]:
            q = qubits[0]
            yq = y_of(q)

            # Try to extract angle or rotation_angle attribute
            angle = None
            if hasattr(instr.operator, "angle"):
                angle = instr.operator.angle
            elif hasattr(instr.operator, "rotation_angle"):
                angle = instr.operator.rotation_angle

            # Round to 3 decimals if found
            if angle is not None:
                label = f"{gate}({angle:.3f})"
            else:
                label = gate

            width_gate = 0.8 * dx
            height_gate = 0.6 * dy
            rect = Rectangle(
                (x_ctr - width_gate / 2, yq - height_gate / 2),
                width_gate, height_gate,
                facecolor="white", edgecolor="black", linewidth=1.0,
            )
            ax.add_patch(rect)
            ax.text(x_ctr, yq, label, ha="center", va="center", fontsize=8)

        # 2) Single-qubit gates without parameters (H, X, Y, Z, S, T, etc.)
        elif len(qubits) == 1 and gate not in ["CNOT", "CX", "TOFFOLI", "CCX", "CCNOT", "MEASURE"]:
            q = qubits[0]
            yq = y_of(q)
            width_gate = 0.8 * dx
            height_gate = 0.6 * dy
            rect = Rectangle(
                (x_ctr - width_gate / 2, yq - height_gate / 2),
                width_gate, height_gate,
                facecolor="white", edgecolor="black", linewidth=1.0,
            )
            ax.add_patch(rect)
            ax.text(x_ctr, yq, gate, ha="center", va="center", fontsize=8)

        # 3) CNOT / CX (2 qubits)
        elif gate in ["CNOT", "CX"] and len(qubits) == 2:
            q_ctrl, q_tgt = qubits
            y_ctrl = y_of(q_ctrl)
            y_tgt = y_of(q_tgt)
            r = 0.1 * dy

            # Draw control dot
            circle_ctrl = Circle((x_ctr, y_ctrl), r, color="black")
            ax.add_patch(circle_ctrl)
            # Draw target circle with “+”
            circle_tgt = Circle((x_ctr, y_tgt), r, fill=False, edgecolor="black", linewidth=1.0)
            ax.add_patch(circle_tgt)
            ax.text(x_ctr, y_tgt, "+", ha="center", va="center", fontsize=8)

            # Connect vertical line between ctrl and tgt
            ymin = min(y_ctrl, y_tgt) + r
            ymax = max(y_ctrl, y_tgt) - r
            ax.vlines(x_ctr, ymin, ymax, color="black", linewidth=1.0)

        # 4) Toffoli / CCX / CCNOT (3 qubits)
        elif gate in ["TOFFOLI", "CCX", "CCNOT"] and len(qubits) == 3:
            q_ctrl1, q_ctrl2, q_tgt = qubits
            y1 = y_of(q_ctrl1)
            y2 = y_of(q_ctrl2)
            yt = y_of(q_tgt)
            r = 0.1 * dy

            # Control dots
            circle1 = Circle((x_ctr, y1), r, color="black")
            circle2 = Circle((x_ctr, y2), r, color="black")
            ax.add_patch(circle1)
            ax.add_patch(circle2)
            # Target circle with “+”
            circle_t = Circle((x_ctr, yt), r, fill=False, edgecolor="black", linewidth=1.0)
            ax.add_patch(circle_t)
            ax.text(x_ctr, yt, "+", ha="center", va="center", fontsize=8)

            # Connect vertical line spanning all three
            ymin = min(y1, y2, yt) + r
            ymax = max(y1, y2, yt) - r
            ax.vlines(x_ctr, ymin, ymax, color="black", linewidth=1.0)

        # 5) Measurement(s) (MEASURE) on one or more qubits
        elif gate.startswith("MEASURE"):
            for q in qubits:
                yq = y_of(q)
                _draw_meter(x_ctr, yq)

        # 6) Generic multi-qubit gates (e.g., SWAP, custom gates, etc.)
        else:
            # Determine top and bottom y-coordinates among all involved qubits
            y_vals = [y_of(q) for q in qubits]
            y_top = max(y_vals) + 0.3 * dy
            y_bot = min(y_vals) - 0.3 * dy
            width_gate = 0.8 * dx
            height_gate = y_top - y_bot

            rect = Rectangle(
                (x_ctr - width_gate / 2, y_bot),
                width_gate, height_gate,
                facecolor="white", edgecolor="black", linewidth=1.0,
            )
            ax.add_patch(rect)
            y_center = (y_top + y_bot) / 2
            ax.text(x_ctr, y_center, gate, ha="center", va="center", fontsize=8)

    ax.set_xlim(x_min, x_max + dx)
    ax.set_ylim(-n_qubits * dy - dy / 2, dy / 2)
    plt.tight_layout()
    return fig, ax

def generate_circuit_latex(circuit, initial_states=None):
    """
    Generate LaTeX (quantikz) code for the given Braket Circuit.

    Parameters:
      - circuit: braket.circuits.Circuit object
      - initial_states: optional list of initial state labels (e.g., ['|0>', '|+>', ...])
        If provided, each will be placed in the \lstick{} for that qubit. Otherwise, defaults to \ket{0} for all.

    Returns:
      - latex_code: a string containing a `quantikz` environment ready to paste into a .tex file.
    """
    instructions, n_qubits = parse_circuit(circuit)
    if n_qubits == 0:
        raise ValueError("The circuit contains no qubits to generate LaTeX.")

    n_cols = len(instructions)
    # Initialize a matrix of "\qw" tokens: size n_qubits x n_cols
    matrix = [["\\qw" for _ in range(n_cols)] for _ in range(n_qubits)]

    for instr_dict in instructions:
        gate = instr_dict["gate"]
        qubits = instr_dict["qubits"]
        col = instr_dict["col_index"]
        instr = instr_dict["instr"]

        if not qubits:
            continue

        # 1) Parameterized single-qubit gates (RX, RY, RZ, PHASE, U3, etc.)
        if len(qubits) == 1 and gate in ["RX", "RY", "RZ", "PHASE", "U3"]:
            q = qubits[0]
            angle = None
            if hasattr(instr.operator, "angle"):
                angle = instr.operator.angle
            elif hasattr(instr.operator, "rotation_angle"):
                angle = instr.operator.rotation_angle

            if angle is not None:
                label = f"{gate}({angle:.3f})"
            else:
                label = gate

            matrix[q][col] = f"\\gate{{{label}}}"

        # 2) Single-qubit gates without parameters (H, X, Y, Z, S, T, etc.)
        elif len(qubits) == 1 and gate not in ["CNOT", "CX", "TOFFOLI", "CCX", "CCNOT", "MEASURE"]:
            q = qubits[0]
            matrix[q][col] = f"\\gate{{{gate}}}"

        # 3) CNOT / CX (2 qubits)
        elif gate in ["CNOT", "CX"] and len(qubits) == 2:
            q_ctrl, q_tgt = qubits
            delta = q_tgt - q_ctrl
            matrix[q_ctrl][col] = f"\\ctrl{{{delta}}}"
            matrix[q_tgt][col] = "\\targ{}"

        # 4) Toffoli / CCX / CCNOT (3 qubits)
        elif gate in ["TOFFOLI", "CCX", "CCNOT"] and len(qubits) == 3:
            q_ctrl1, q_ctrl2, q_tgt = qubits
            matrix[q_ctrl1][col] = f"\\ctrl{{{q_tgt - q_ctrl1}}}"
            matrix[q_ctrl2][col] = f"\\ctrl{{{q_tgt - q_ctrl2}}}"
            matrix[q_tgt][col] = "\\targ{}"

        # 5) Measurement(s) (MEASURE) on one or more qubits
        elif gate.startswith("MEASURE"):
            for q in qubits:
                matrix[q][col] = "\\meter{}"

        # 6) Generic multi-qubit gates
        else:
            top = min(qubits)
            wires = len(qubits)
            matrix[top][col] = f"\\gate[wires={wires}]{{{gate}}}"
            # Leave the rest of the rows “below” empty so quantikz collapses wires
            for q in qubits[1:]:
                matrix[q][col] = ""

    # Build the LaTeX lines
    lines = []
    lines.append("\\begin{quantikz}")
    for q in range(n_qubits):
        if initial_states and q < len(initial_states):
            label = initial_states[q]
        else:
            label = "\\lstick{\\ket{0}}"
        row_tokens = [label] + matrix[q]
        line = " & ".join(row_tokens) + " \\\\"
        lines.append(line)
    lines.append("\\end{quantikz}")

    latex_code = "\n".join(lines)
    return latex_code


def circuit_drawer(circuit, style="mpl", **kwargs):
    """
    High-level function to visualize a Braket Circuit.

    Parameters:
      - circuit: braket.circuits.Circuit object
      - style: 'mpl' for Matplotlib, 'latex' for quantikz output
      - kwargs: any extra keyword arguments are forwarded to draw_circuit_matplotlib
                (if style='mpl') or to generate_circuit_latex (if style='latex').

    Returns:
      - If style=='mpl': a tuple (fig, ax) of Matplotlib Figure and Axes.
      - If style=='latex': a string containing the LaTeX code.
    """
    if style == "mpl":
        return draw_circuit_matplotlib(circuit, **kwargs)
    elif style == "latex":
        return generate_circuit_latex(circuit, **kwargs)
    else:
        raise ValueError("Unknown style: must be 'mpl' or 'latex'.")


if __name__ == "__main__":
    try:
        from braket.circuits import Circuit
        import matplotlib.pyplot as plt

        # Example circuit: H, CNOT, RX(π/2), CCNOT, measure qubits 0,1,2
        circuit = Circuit().h(0).cnot(0, 1).rx(1, 1.5708).ccnot(0, 1, 2).measure(4)

        # 1) Visualize with Matplotlib
        fig, ax = draw_circuit_matplotlib(circuit, figsize=(6, 4))
        plt.show()

        # 2) Generate LaTeX (quantikz)
        latex = generate_circuit_latex(circuit, initial_states=["|0>", "|0>", "|0>"])
        print("\n------ LaTeX (quantikz) code: ------\n")
        print(latex)

    except ImportError:
        print(
            "AWS Braket SDK is not installed. To test this example, run:\n"
            "    pip install amazon-braket-sdk\n"
        )

