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

from collections.abc import Callable
from contextlib import contextmanager

from braket.aws.aws_device import AwsDevice, AwsDeviceType
from braket.devices.device import Device
from braket.devices.local_simulator import LocalSimulator


@contextmanager
def Reservation(device: Device, reservation_arn: str | None = None) -> Device | None:
    """
    A context manager that temporarily modifies the `run` method of a `device` object
    to include a specified `reservation_arn` in all calls within the context. This is useful
    for ensuring that all quantum task run within the context are associated with a given
    reservation ARN (Amazon Resource Name).

    Args:
        device (Device): The Braket device for which you have a reservation ARN.
        reservation_arn (str | None): The Braket Direct reservation ARN to be applied to all
            quantum tasks run within the context. Defaults to None.

    Yields:
        Device | None: The device object with a potentially modified `run` method. If the device is
        a local simulator or the reservation ARN is None, the original device is yielded without
        modification.

    Examples:
        >>> with Reservation(device, reservation_arn="<my_reservation_arn>"):
        ...     task1 = device.run(circuit, shots)
        ...     task2 = device.run(circuit, shots)
    """

    if not isinstance(device, Device):
        raise ValueError("The provided device is not a valid Braket device.")

    # Local simulators do not accept reservation ARNs
    if isinstance(device, LocalSimulator) or device.type == AwsDeviceType.SIMULATOR:
        yield device

    elif isinstance(device, AwsDevice):
        # on-demand simulators do not accept reservation ARNs
        if device.type == AwsDeviceType.SIMULATOR:
            yield device

        elif device.type == AwsDeviceType.QPU:
            original_run = device.run

            def _run_with_reservation(*args, **kwargs) -> Callable:
                kwargs["reservation_arn"] = reservation_arn
                return original_run(*args, **kwargs)

            device.run = _run_with_reservation

            try:
                yield device
            finally:
                device.run = original_run
