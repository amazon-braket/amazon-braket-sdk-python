from qiskit import QuantumCircuit
from q_draw_xs import xs_draw

# Create a simple quantum circuit with 2 qubits and 2 classical bits
qc = QuantumCircuit(2, 2)
qc.h(0)           # Apply Hadamard gate to qubit 0
qc.cx(0, 1)       # Apply CNOT gate with control qubit 0 and target qubit 1
qc.measure([0, 1], [0, 1])  # Measure both qubits


xs_draw(qc)  # Draw the circuit using xs_draw
print(qc)  # Print the quantum circuit
