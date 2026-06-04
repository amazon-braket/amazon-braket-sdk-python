| Task | Code |
|---|---|
| Import Debias | `from braket.error_mitigation import Debias` |
| Use debias error mitigation | `device.run(circuit, shots=2500, device_parameters={"errorMitigation": Debias()})` |
| Get sharpened probabilities, if returned | `result.additional_metadata.ionqMetadata.sharpenedProbabilities` |