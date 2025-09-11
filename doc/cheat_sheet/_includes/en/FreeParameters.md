| Imports | `from braket.circuits import FreeParameter` |
| Create a free parameter | `alpha = FreeParameter(“alpha”)` |
| Use a free Parameter | `circuit.rx(0, alpha)`| 
| Free parameter algebra | `beta = 2 * alpha + 1`| 
| Bind a value | `circuit.make_bound_circuit({“alpha”: 0.1})`| 
| Get the list of unbound FreeParameters| `circuit.parameters`| 
| Inline compilation| `device.run(circuit, inputs={“alpha”: 0.1})`| 
