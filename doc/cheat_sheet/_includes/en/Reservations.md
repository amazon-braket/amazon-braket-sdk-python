| Task | Snippet |
|---|---|
| Imports | `from braket.aws import DirectReservation` |
| Run tasks in a reservation context | `with DirectReservation(device, reservation_arn=reservation_arn):`<br>`    task = device.run(circuit, shots=100)` |
| Start and stop explicitly | `reservation = DirectReservation(device, reservation_arn=reservation_arn)`<br>`reservation.start()`<br>`task = device.run(circuit, shots=100)`<br>`reservation.stop()` |
| Pass the reservation directly | `task = device.run(circuit, shots=100, reservation_arn=reservation_arn)` |
| Use with the hybrid job decorator | `@hybrid_job(device=Devices.IonQ.Forte1, reservation_arn=reservation_arn)` |
| Use with `AwsQuantumJob.create` | `AwsQuantumJob.create(device=Devices.IonQ.Forte1, source_module="job.py", entry_point="job:run", reservation_arn=reservation_arn)` |

Reservation ARNs are device and AWS account specific. Use the same device that was reserved for the reservation window.
