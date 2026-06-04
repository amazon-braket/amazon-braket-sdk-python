| Task | Code |

|---|---|

| Imports | `from braket.aws import DirectReservation` |

| Use reservation as a context manager | `with DirectReservation(device, reservation\_arn=reservation\_arn):` |

| Start reservation context manually | `reservation = DirectReservation(device, reservation\_arn=reservation\_arn).start()` |

| Stop manual reservation context | `reservation.stop()` |

| Pass reservation ARN directly to a task | `task = device.run(circuit, shots=100, reservation\_arn=reservation\_arn)` |

| Use reservation with hybrid job decorator | `@hybrid\_job(device=device\_arn, reservation\_arn=reservation\_arn)` |

| Note | Reservation examples require AWS credentials, a configured AWS region, and a valid Braket Direct reservation ARN. |

