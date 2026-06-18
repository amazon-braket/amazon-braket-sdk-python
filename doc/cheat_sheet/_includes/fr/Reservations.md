| Imports | `from braket.aws import AwsDevice, DirectReservation` |
| Réserver via un gestionnaire de contexte | `with DirectReservation(device, reservation_arn="<arn>"):`<br>`    task = device.run(circuit, shots=100)` |
| Démarrer / arrêter une réservation explicitement | `res = DirectReservation(device, reservation_arn="<arn>")`<br>`res.start()`<br>`res.stop()` |
| Appliquer à une seule tâche quantique | `device.run(circuit, shots=100, reservation_arn="<arn>")` |
| Appliquer à une tâche hybride | `@hybrid_job(device=Devices.IQM.Garnet, reservation_arn="<arn>")` |
