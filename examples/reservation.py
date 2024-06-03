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

from braket.aws import AwsDevice, DirectReservation
from braket.circuits import Circuit
from braket.devices import Devices

bell = Circuit().h(0).cnot(0, 1)
device = AwsDevice(Devices.IonQ.Aria1)

# To run a task in a device reservation, change the device to the one you reserved
# and fill in your reservation ARN.
with DirectReservation(device, reservation_arn="<my_reservation_arn>"):
    task = device.run(bell, shots=100)
print(task.result().measurement_counts)

# Alternatively, you may start the reservation globally
reservation = DirectReservation(device, reservation_arn="<my_reservation_arn>").start()
task = device.run(bell, shots=100)
print(task.result().measurement_counts)
reservation.stop()  # stop creating tasks in the reservation

# Lastly, you may pass the reservation ARN directly to a quantum task
task = device.run(bell, shots=100, reservation_arn="<my_reservation_arn>")
print(task.result().measurement_counts)
