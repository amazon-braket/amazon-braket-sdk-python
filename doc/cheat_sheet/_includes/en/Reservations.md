| Imports | `from braket.aws import AwsDevice, DirectReservation` |
| Reserve via a context manager<!-- LLM: . Every task created inside the context is submitted against the reservation--> | `with DirectReservation(device, reservation_arn="<arn>"):`<br>`    task = device.run(circuit, shots=100)` |
| Start / stop a reservation explicitly | `res = DirectReservation(device, reservation_arn="<arn>")`<br>`res.start()`<br>`res.stop()` |
| Apply to a single quantum task | `device.run(circuit, shots=100, reservation_arn="<arn>")` |
| Apply to a hybrid job | `@hybrid_job(device=Devices.IQM.Garnet, reservation_arn="<arn>")` |
