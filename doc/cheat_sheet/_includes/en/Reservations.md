| Imports | `from braket.aws.direct_reservations import DirectReservation` |
| Use as a context manager | `with DirectReservation(device_arn, reservation_arn="<my_reservation_arn>"):`<br>`    task = device.run(circuit, shots=100)` |
| Start a reservation | `DirectReservation(device_arn, reservation_arn="<my_reservation_arn>").start()` |
| Reserve a device from `AwsDevice` | `device.run(circuit, shots=100, reservation_arn="<my_reservation_arn>")` |
