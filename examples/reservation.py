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

from braket.aws import AwsDevice
from braket.circuits import Circuit
from braket.devices import Devices
from braket.reservations import reservation

bell = Circuit().h(0).cnot(0, 1)
device = AwsDevice(Devices.IonQ.Aria1)

# To run a task in a device reservation, change the device to the one you reserved
# and fill in your reservation ARN.
with reservation(device, reservation_arn="reservation ARN"):
    task = device.run(bell, shots=100)

print(task.result().measurement_counts)

# Alternatively, you may directly pass the reservation ARN to all quantum tasks.
task = device.run(bell, shots=100, reservation_arn="reservation ARN")
print(task.result().measurement_counts)


# A third option to run a reservation is by decorating a function.
# All tasks created within the function will use the reservation.
@reservation(device, reservation_arn="reservation ARN")
def my_function():
    task = device.run(bell, shots=100)
    print(task.result().measurement_counts)
