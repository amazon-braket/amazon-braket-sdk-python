| Imports | `import math`<br>`from braket.circuits import Circuit`<br>`from braket.experimental_capabilities import EnableExperimentalCapability` |
| Enable experimental capabilities<!-- LLM: . Experimental operations raise an error unless created inside this context manager--> | `with EnableExperimentalCapability():`<br>`    circuit = Circuit()` |
| Mid-circuit measurement into a feedback register (IQM) | `circuit.measure_ff(0, feedback_key=0)` |
| Classically-controlled PRx, conditioned on a feedback key (IQM) | `circuit.cc_prx(1, math.pi / 2, math.pi / 4, feedback_key=0)` |
| Available on | IQM devices (e.g. `Devices.IQM.Garnet`) |
