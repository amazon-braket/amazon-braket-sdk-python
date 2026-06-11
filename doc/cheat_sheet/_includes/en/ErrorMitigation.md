| Task | Snippet |
|---|---|
| Imports | `from braket.error_mitigation import Debias` |
| Debias | `task = device.run(circuit, shots=2500, device_parameters={"errorMitigation": Debias()})` |
| Sharpened probabilities, if returned | `task.result().additional_metadata.ionqMetadata.sharpenedProbabilities` |
