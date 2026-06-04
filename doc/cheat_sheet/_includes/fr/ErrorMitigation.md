| Débiaisage | `device.run(circuit, shots=2500, device_parameters={"errorMitigation": Debias()})` |
| Affinage (si le débiaisage est utilisé) | `result.additional_metadata.ionqMetadata.sharpenedProbabilities` |
