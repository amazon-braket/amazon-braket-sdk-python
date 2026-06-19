| Imports | `from braket.aws import AwsDevice`<br>`from braket.devices import Devices, LocalSimulator`<br>`from braket.emulation import Emulator`<br>`from braket.emulation.local_emulator import LocalEmulator` |
| Obtenir un émulateur pour un QPU | `emulator = AwsDevice(Devices.IQM.Garnet).emulator` |
| Valider un circuit selon les contraintes du dispositif | `emulator.validate(circuit)` |
| Compiler un circuit vers les portes natives et la connectivité du dispositif | `compiled = emulator.transform(circuit)` |
| Exécuter sur le backend émulé (applique le bruit du dispositif) | `result = emulator.run(circuit, shots=100).result()` |
| Inspecter le modèle de bruit du dispositif | `emulator.noise_model` |
| Construire un émulateur personnalisé | `emulator = Emulator(backend=LocalSimulator("braket_dm"))` |
| Émulateur à partir d'un JSON de propriétés de dispositif | `emulator = LocalEmulator.from_json(properties_json)` |
