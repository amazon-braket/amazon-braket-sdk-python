| Task | Snippet |
|---|---|
| Imports | `from braket.circuits import Circuit, FreeParameter` |
| Create a free parameter | `theta = FreeParameter("theta")` |
| Use a free parameter | `circuit = Circuit().rx(0, theta)` |
| Free parameter algebra | `phi = 2 * theta + 1` |
| Bind locally | `bound = circuit.make_bound_circuit({"theta": 0.1})` |
| List unbound parameters | `circuit.parameters` |
| Bind at task creation | `task = device.run(circuit, shots=100, inputs={"theta": 0.1})` |
