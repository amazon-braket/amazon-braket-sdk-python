# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from __future__ import annotations

import os
import warnings
from contextlib import AbstractContextManager

from braket.aws.aws_device import AwsDevice
from braket.devices import Device


class DirectReservation(AbstractContextManager):
    """
    Context manager that modifies AwsQuantumTasks created within the context to use a reservation
    ARN for all tasks targeting the specified device. Note: this context manager only allows for
    one reservation at a time.

    Reservations are AWS account and device specific. Only the AWS account that created the
    reservation can use your reservation ARN. Additionally, the reservation ARN is only valid on the
    reserved device at the chosen start and end times.

    Args:
        device (Device | str | None): The Braket device for which you have a reservation ARN, or
            optionally the device ARN.
        reservation_arn (str | None): The Braket Direct reservation ARN to be applied to all
            quantum tasks run within the context.

    Examples:
        As a context manager
        >>> with DirectReservation(device_arn, reservation_arn="<my_reservation_arn>"):
        ...     task1 = device.run(circuit, shots)
        ...     task2 = device.run(circuit, shots)

        or start the reservation
        >>> DirectReservation(device_arn, reservation_arn="<my_reservation_arn>").start()
        ... task1 = device.run(circuit, shots)
        ... task2 = device.run(circuit, shots)

    References:

    [1] https://docs.aws.amazon.com/braket/latest/developerguide/braket-reservations.html
    """

    _is_active = False  # Class variable to track active reservation context

    def __init__(self, device: Device | str | None, reservation_arn: str | None):
        if isinstance(device, AwsDevice):
            self.device_arn = device.arn
        elif isinstance(device, str):
            self.device_arn = AwsDevice(device).arn  # validate ARN early
        elif isinstance(device, Device) or device is None:  # LocalSimulator
            warnings.warn(
                "Using a local simulator with the reservation. For a reservation on a QPU, please "
                "ensure the device matches the reserved Braket device.",
                stacklevel=2,
            )
            self.device_arn = ""  # instead of None, use empty string
        else:
            raise TypeError("Device must be an AwsDevice or its ARN, or a local simulator device.")

        self.reservation_arn = reservation_arn

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        self.stop()

    def start(self) -> None:
        """Start the reservation context."""
        if DirectReservation._is_active:
            raise RuntimeError("Another reservation is already active.")

        os.environ["AMZN_BRAKET_RESERVATION_DEVICE_ARN"] = self.device_arn
        if self.reservation_arn:
            os.environ["AMZN_BRAKET_RESERVATION_TIME_WINDOW_ARN"] = self.reservation_arn
        DirectReservation._is_active = True

    def stop(self) -> None:
        """Stop the reservation context."""
        if not DirectReservation._is_active:
            warnings.warn("Reservation context is not active.", stacklevel=2)
            return
        os.environ.pop("AMZN_BRAKET_RESERVATION_DEVICE_ARN", None)
        os.environ.pop("AMZN_BRAKET_RESERVATION_TIME_WINDOW_ARN", None)
        DirectReservation._is_active = False
