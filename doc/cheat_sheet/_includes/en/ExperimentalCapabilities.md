| Task | Snippet |
|---|---|
| Imports | `from braket.experimental_capabilities import EnableExperimentalCapability`<br>`from braket.circuits import Circuit` |
| Enable inside a block | `with EnableExperimentalCapability():`<br>`    circuit = Circuit().measure_ff(0, 0).cc_prx(1, 1.57, 0.0, 0)` |
| IQM feed-forward measurement | `circuit.measure_ff(target=0, feedback_key=0)` |
| IQM classically controlled PRx | `circuit.cc_prx(target=1, angle_1=1.57, angle_2=0.0, feedback_key=0)` |
| Use with verbatim execution | `wrapped = Circuit().add_verbatim_box(circuit)` |

Experimental capabilities are opt-in and may change. The SDK raises an error if experimental operators are constructed outside `EnableExperimentalCapability`.
