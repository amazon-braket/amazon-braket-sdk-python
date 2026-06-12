| Task | Code |
|---|---|
| Imports | `from braket.aws import DirectReservation` |
| Use reservation as a context manager | `with DirectReservation(device, reservation_arn=reservation_arn):` |
| Start reservation context manually | `reservation = DirectReservation(device, reservation_arn=reservation_arn).start()` |
| Stop manual reservation context | `reservation.stop()` |
| Pass reservation ARN directly to a task | `task = device.run(circuit, shots=100, reservation_arn=reservation_arn)` |
| Use reservation with hybrid job decorator | `@hybrid_job(device=device_arn, reservation_arn=reservation_arn)` |
| Note | Reservation examples require AWS credentials, a configured AWS region, and a valid Braket Direct reservation ARN. |
