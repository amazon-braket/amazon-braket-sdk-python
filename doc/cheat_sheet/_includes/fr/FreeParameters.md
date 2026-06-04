| Imports | `from braket.circuits import FreeParameter` |
| Créer un paramètre libre | `alpha = FreeParameter("alpha")` |
| Utiliser un paramètre libre | `circuit.rx(0, alpha)`|
| Algèbre de paramètres libres | `beta = 2 * alpha + 1`|
| Lier une valeur | `circuit.make_bound_circuit({"alpha": 0.1})`|
| Lister les paramètres libres non liés | `circuit.parameters`|
| Compilation en ligne | `device.run(circuit, inputs={"alpha": 0.1})`|
