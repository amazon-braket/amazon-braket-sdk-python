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


from braket.device_schema.aqt.aqt_device_capabilities_v1 import AqtDeviceCapabilities
from braket.device_schema.ionq.ionq_device_capabilities_v1 import IonqDeviceCapabilities
from braket.device_schema.standardized_gate_model_qpu_device_properties_v1 import (
    CoherenceTime,
    Fidelity1Q,
    FidelityType,
    GateFidelity2Q,
    OneQubitProperties,
    TwoQubitProperties,
)

from braket.circuits.translations import BRAKET_GATES


def _standardize_aqt_device_properties(
    device_properties: AqtDeviceCapabilities,
) -> AqtDeviceCapabilities:
    if (
        device_properties.braketSchemaHeader.name
        != "braket.device_schema.aqt.aqt_device_capabilities"
    ):
        raise ValueError("The input must be of type AqtDeviceCapabilities.")

    standardized = device_properties.standardized

    # Create T1 and T2 coherence times using device-level values
    t1 = CoherenceTime(
        value=standardized.T1.value,
        standardError=standardized.T1.standardError,
        unit=standardized.T1.unit.value,
    )

    t2 = CoherenceTime(
        value=standardized.T2.value,
        standardError=standardized.T2.standardError,
        unit=standardized.T2.unit.value,
    )

    # Convert one qubit properties
    one_qubit_properties_v1: dict[str, OneQubitProperties] = {}
    for qubit_id, props_v3 in standardized.oneQubitProperties.items():
        one_qubit_fidelity: list[Fidelity1Q] = []
        # Add qubit-specific fidelities
        for fidelity_v3 in props_v3.oneQubitFidelity:
            fidelity_type_v1 = FidelityType(
                name=fidelity_v3.fidelityType.name.value,
                description=fidelity_v3.fidelityType.description,
            )

            one_qubit_fidelity.append(
                Fidelity1Q(
                    fidelityType=fidelity_type_v1,
                    fidelity=fidelity_v3.fidelity,
                    standardError=fidelity_v3.standardError,
                )
            )
        # Add device-level readout fidelity
        for readout_fidelity in standardized.readoutFidelity:
            fidelity_type_v1 = FidelityType(
                name="READOUT",
                description=None,
            )
            one_qubit_fidelity.append(
                Fidelity1Q(
                    fidelityType=fidelity_type_v1,
                    fidelity=readout_fidelity.fidelity,
                    standardError=readout_fidelity.standardError,
                )
            )
        one_qubit_properties_v1[qubit_id] = OneQubitProperties(
            T1=t1,
            T2=t2,
            oneQubitFidelity=one_qubit_fidelity,
        )

    two_qubit_gate_names = [
        gate
        for gate in device_properties.paradigm.nativeGateSet
        if BRAKET_GATES[gate.lower()].fixed_qubit_count() == 2
    ]

    # Assuming there is one and only one two-qubit native gate
    two_qubit_gate_name = two_qubit_gate_names[0]

    # Convert two qubit properties (device-level only in v3)
    twoQubitGateFidelity: list[GateFidelity2Q] = []

    for fidelity_v3 in standardized.twoQubitGateFidelity:
        fidelity_type_v1 = FidelityType(
            name=fidelity_v3.fidelityType.name.value,
            description=fidelity_v3.fidelityType.description,
        )
        # Create a generic two-qubit gate fidelity
        twoQubitGateFidelity.append(
            GateFidelity2Q(
                direction=None,
                gateName=two_qubit_gate_name,
                fidelity=fidelity_v3.fidelity,
                standardError=fidelity_v3.standardError,
                fidelityType=fidelity_type_v1,
            )
        )

    twoQubitProperties = TwoQubitProperties(twoQubitGateFidelity=twoQubitGateFidelity)

    num_qubits = len(one_qubit_properties_v1)
    all_edges = [f"{i}-{j}" for i in range(num_qubits) for j in range(i + 1, num_qubits)]

    device_properties.__dict__["standardized"] = {
        "braketSchemaHeader": {
            "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
            "version": "1",
        },
        "oneQubitProperties": one_qubit_properties_v1,
        "twoQubitProperties": dict.fromkeys(all_edges, twoQubitProperties),
    }

    return device_properties


def _standardize_ionq_device_properties(
    device_properties: IonqDeviceCapabilities,
) -> IonqDeviceCapabilities:
    if (
        device_properties.braketSchemaHeader.name
        != "braket.device_schema.ionq.ionq_device_capabilities"
    ):
        raise ValueError("The input must be of type IonqDeviceCapabilities.")

    device_properties_dict = device_properties.dict()
    T1 = device_properties_dict["provider"]["timing"]["T1"]
    T2 = device_properties_dict["provider"]["timing"]["T2"]
    f1q = device_properties_dict["provider"]["fidelity"]["1Q"]["mean"]
    f2q = device_properties_dict["provider"]["fidelity"]["2Q"]["mean"]
    fspam = device_properties_dict["provider"]["fidelity"]["spam"]["mean"]

    oneQubitProperties = OneQubitProperties(
        T1=CoherenceTime(value=T1, standardError=None, unit="S"),
        T2=CoherenceTime(value=T2, standardError=None, unit="S"),
        oneQubitFidelity=[
            Fidelity1Q(
                fidelityType=FidelityType(name="RANDOMIZED_BENCHMARKING", description=None),
                fidelity=f1q,
                standardError=None,
            ),
            Fidelity1Q(
                fidelityType=FidelityType(name="READOUT", description=None),
                fidelity=fspam,
                standardError=None,
            ),
        ],
    )

    two_qubit_gate_names = [
        gate
        for gate in device_properties_dict["paradigm"]["nativeGateSet"]
        if BRAKET_GATES[gate.lower()].fixed_qubit_count() == 2
    ]

    # Assuming there is one and only one two-qubit native gate
    two_qubit_gate_name = two_qubit_gate_names[0]

    twoQubitProperties = TwoQubitProperties(
        twoQubitGateFidelity=[
            GateFidelity2Q(
                direction=None,
                gateName=two_qubit_gate_name,
                fidelity=f2q,
                standardError=None,
                fidelityType=FidelityType(name="RANDOMIZED_BENCHMARKING", description=None),
            )
        ]
    )

    num_qubits = device_properties_dict["paradigm"]["qubitCount"]

    all_edges = [f"{i}-{j}" for i in range(num_qubits) for j in range(i + 1, num_qubits)]
    device_properties.__dict__["standardized"] = {
        "braketSchemaHeader": {
            "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
            "version": "1",
        },
        "oneQubitProperties": dict.fromkeys(range(num_qubits), oneQubitProperties),
        "twoQubitProperties": dict.fromkeys(all_edges, twoQubitProperties),
    }

    device_properties.paradigm.nativeGateSet = [
        gate.lower() for gate in device_properties.paradigm.nativeGateSet
    ]
    return device_properties
