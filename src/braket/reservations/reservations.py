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
from contextlib import AbstractContextManager

from braket.aws import AwsDevice
from braket.devices import Device


class DirectReservation(AbstractContextManager):
    """
    Modify AwsQuantumTasks created within this context to run on a device with a reservation
    ARN.This is useful for ensuring that all quantum task

    Reservations are AWS account and device specific. Only the AWS account that created the
    reservation can use your reservation ARN. Additionally, the reservation ARN is only valid on the
    reserved device at the chosen start and end times.

    Args:
        device (Device | str): The Braket device for which you have a reservation ARN, or
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

    def __init__(self, device_arn: Device | str, reservation_arn: str | None) -> Device | None:
        if isinstance(device_arn, AwsDevice):
            self.device_arn = device_arn._arn
        elif isinstance(device_arn, str):
            self.device_arn = device_arn
        elif isinstance(device_arn, Device):
            self.device_arn = None
        else:
            raise ValueError("Device ARN must be a device or string.")
        self.context_active = False
        self.reservation_arn = reservation_arn

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()

    def start(self) -> None:
        """Start the reservation context."""
        if self.context_active:
            raise RuntimeError("Context is already active")

        if self.device_arn:
            os.environ["AMZN_BRAKET_DEVICE_ARN_TEMP"] = self.device_arn
            os.environ["AMZN_BRAKET_RESERVATION_ARN_TEMP"] = self.reservation_arn
            self.context_active = True
        else:
            raise ValueError("Device ARN must not be None")

    def stop(self) -> None:
        """Stop the reservation context."""
        if not self.context_active:
            raise RuntimeError("Context is not active")

        os.environ.pop("AMZN_BRAKET_DEVICE_ARN_TEMP", None)
        os.environ.pop("AMZN_BRAKET_RESERVATION_ARN_TEMP", None)
        self.context_active = False
