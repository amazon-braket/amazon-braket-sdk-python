| Task | Code |
|---|---|
| Imports | `from braket.experimental_capabilities import EnableExperimentalCapability` |
| Enable experimental capabilities temporarily | `with EnableExperimentalCapability():` |
| Add IQM feed-forward measurement | `circuit.measure_ff(0, feedback_key=0)` |
| Add IQM classically controlled PRx | `circuit.cc_prx(0, angle_1=0.15, angle_2=0.25, feedback_key=0)` |
| Pass experimental capabilities to a task | `task = device.run(circuit, shots=100, experimental_capabilities="ALL")` |
| Note | Experimental capabilities may change between SDK releases. Check device support and provider restrictions before production use. |
