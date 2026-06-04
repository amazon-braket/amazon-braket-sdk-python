| Imports | `import math`<br>`from braket.circuits import Circuit`<br>`from braket.experimental_capabilities import EnableExperimentalCapability` |
| Activer les fonctionnalités expérimentales | `with EnableExperimentalCapability():`<br>`    circuit = Circuit()` |
| Mesure en cours de circuit vers un registre de rétroaction (IQM) | `circuit.measure_ff(0, feedback_key=0)` |
| Porte PRx contrôlée classiquement, conditionnée par une clé de rétroaction (IQM) | `circuit.cc_prx(1, math.pi / 2, math.pi / 4, feedback_key=0)` |
| Disponible sur | dispositifs IQM (p. ex. `Devices.IQM.Garnet`) |
