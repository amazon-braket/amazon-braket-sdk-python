|                      |                                                       |
| -------------------- | ----------------------------------------------------- |
| Create a FreeParameter | `alpha=FreeParameter(“alpha”)` |
| Use FreeParameters | `circuit.rx(0, alpha+1)`| 
| Bind a FreeParameter()| `circuit.make_bound_circuit({“alpha”: 0.1})`| 
| Get the list of unbound FreeParameters| `circuit.parameters`| 
| Inline compilation| `device.run(circuit, inputs={“alpha”: 0.1})`| 
