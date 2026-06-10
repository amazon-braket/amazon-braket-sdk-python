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

from braket.circuits import Circuit

circuit = (
    Circuit()
    .h(0)
    .cnot(0, 1)
    .add_verbatim_box(Circuit().rx(0, 0.25).cz(0, 1))
    .probability(target=[0, 1])
)

device_metadata = {
    "H": {"fidelity": 0.9991},
    "CNot": {"fidelity": 0.982, "duration": "120 ns"},
    "Rx": {"fidelity": 0.998},
    "CZ": {"fidelity": 0.985, "duration": "140 ns"},
}

figure = circuit.show("interactive", device_metadata=device_metadata)
figure.write_html("plotly_circuit_visualization.html", include_plotlyjs="cdn")
