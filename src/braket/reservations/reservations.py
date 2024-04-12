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

from collections.abc import Callable
from contextlib import contextmanager

from braket.aws.aws_device import AwsDevice
from braket.devices.device import Device
from braket.devices.local_simulator import LocalSimulator


@contextmanager
def reservation(device: Device, reservation_arn: str | None) -> Device | None:
    """
    A context manager that temporarily modifies the `run` method of a `device` object
    to include a specified `reservation_arn` in all calls within the context. This is useful
    for ensuring that all quantum task run within the context are associated with a given
    reservation ARN (Amazon Resource Name).

    Reservations are AWS account and device specific. Only the AWS account that created the
    reservation can use your reservation ARN. Additionally, the reservation ARN is only valid on the
    reserved device at the chosen start and end times.

    Args:
        device (Device): The Braket device for which you have a reservation ARN.
        reservation_arn (str | None): The Braket Direct reservation ARN to be applied to all
            quantum tasks run within the context. Defaults to None.

    Yields:
        Device | None: The device object with a potentially modified `run` method. If the device is
        a local simulator or the reservation ARN is None, the original device is yielded without
        modification.

    Examples:
        As a context manager
        >>> with reservation(device, reservation_arn="<my_reservation_arn>"):
        ...     task1 = device.run(circuit, shots)
        ...     task2 = device.run(circuit, shots)

        or as a decorator

        >>> @reservation(device, reservation_arn="<my_reservation_arn>"):
        ... def func():
        ...     task1 = device.run(circuit, shots)
        ...     task2 = device.run(circuit, shots)
    References:
    [1] https://docs.aws.amazon.com/braket/latest/developerguide/braket-reservations.html
    """

    if isinstance(device, AwsDevice):
        original_run = device.run

        def _run_with_reservation(*args, **kwargs) -> Callable:
            kwargs["reservation_arn"] = reservation_arn
            return original_run(*args, **kwargs)

        device.run = _run_with_reservation

        try:
            yield device
        finally:
            device.run = original_run

    # Local simulators do not accept reservation ARNs
    elif isinstance(device, LocalSimulator):
        yield device
    else:
        raise TypeError(f"The provided device {device} is not a valid Braket device.")
