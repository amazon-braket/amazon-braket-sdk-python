| Debias | `device.run(circuit, shots=2500, device_parameters={"errorMitigation": Debias()})` |
| Sharpening (if debiasing used) | `result.additional_metadata.ionqMetadata.sharpenedProbabilities` |