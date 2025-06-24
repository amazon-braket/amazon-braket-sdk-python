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

from typing import Any, Union

from braket.device_schema.device_capabilities import DeviceCapabilities

from braket.circuits.noise_model import GateCriteria, NoiseModel, ObservableCriteria
from braket.circuits.noises import (
    BitFlip,
    Depolarizing,
    TwoQubitDepolarizing,
)
from braket.circuits.translations import BRAKET_GATES
from braket.emulation.device_emulator_properties import DeviceEmulatorProperties
from braket.emulation.emulator import Emulator
from braket.passes.circuit_passes import GateValidator, QubitCountValidator
from braket.passes.device_emulator_validators import (
    set_up_connectivity_validator,
    set_up_gate_connectivity_validator,
)


class LocalEmulator(Emulator):
    """
    A local emulator that mimics the restrictions and noises of a QPU based on the provided device
    properties.
    """

    @classmethod
    def from_device_properties(
        cls,
        device_properties: Union[DeviceCapabilities, DeviceEmulatorProperties],
        backend: str = "braket_dm",
        **kwargs: Any,
    ) -> LocalEmulator:
        """Create a LocalEmulator instance from device properties.

        Args:
            device_properties (Union[DeviceCapabilities, DeviceEmulatorProperties]): The device
                properties to use for emulation.
            backend (str): The backend to use for simulation. Default is "braket_dm".
            **kwargs (Any): Additional keyword arguments to pass to the LocalEmulator constructor.

        Returns:
            LocalEmulator: A new LocalEmulator instance configured with the given properties.

        Raises:
            ValueError: If the backend is not the local density matrix simulator
        """

        # Instantiate an instance of DeviceEmulatorProperties
        if isinstance(device_properties, DeviceEmulatorProperties):
            device_em_properties = device_properties
        elif isinstance(device_properties, DeviceCapabilities):
            device_em_properties = DeviceEmulatorProperties.from_device_properties(
                device_properties
            )
        else:
            raise TypeError(
                f"device_properties must be an instance of either DeviceCapabilities or "
                f"DeviceEmulatorProperties, not {type(device_properties)}."
            )

        if backend != "braket_dm":
            raise ValueError("backend can only be `braket_dm`.")

        # Create a noise model based on the provided device properties
        noise_model = cls._setup_basic_noise_model_strategy(device_em_properties)

        # Initialize with device properties and specified backend
        emulator = cls(backend=backend, noise_model=noise_model, **kwargs)

        # Add the passes for validation
        emulator.add_pass(QubitCountValidator(device_em_properties.qubitCount))
        emulator.add_pass(GateValidator(native_gates=device_em_properties.nativeGateSet))
        emulator.add_pass(set_up_connectivity_validator(device_em_properties))
        emulator.add_pass(set_up_gate_connectivity_validator(device_em_properties))

        return emulator

    @classmethod
    def from_json(
        cls,
        device_properties_json: str,
        backend: str = "braket_dm",
        **kwargs: Any,
    ) -> LocalEmulator:
        """Create a LocalEmulator instance from a device properties JSON string.

        Args:
            device_properties_json (str): Device properties JSON string.
            backend (str): The backend to use for simulation. Defaults to "braket_dm".
            **kwargs (Any): Additional keyword arguments to pass to the Emulator constructor.

        Returns:
            LocalEmulator: A new LocalEmulator instance configured with the given properties.

        Raises:
            ValueError: If the JSON string is invalid.
        """

        device_emu_properties = DeviceEmulatorProperties._from_json(device_properties_json)
        return cls.from_device_properties(device_emu_properties, backend=backend, **kwargs)

    @classmethod
    def _setup_basic_noise_model_strategy(
        cls, device_em_properties: DeviceEmulatorProperties
    ) -> NoiseModel:
        """
        Apply a basic noise model strategy consisting of:
            - 1 Qubit RB Depolarizing Noise
            - 1 Qubit Readout Error
            - 2 Qubit Gate Depolarizing Noise
        """
        noise_model = NoiseModel()
        for qubit_str, data in device_em_properties.oneQubitProperties.items():
            qubit = int(qubit_str)
            oneQubitProperty = data.oneQubitFidelity
            fidelity_names = {
                fidelity.fidelityType.name: ind for ind, fidelity in enumerate(oneQubitProperty)
            }

            # Apply one qubit RB Depolarizing Noise
            if "RANDOMIZED_BENCHMARKING" in fidelity_names:
                one_qubit_fidelity = oneQubitProperty[
                    fidelity_names["RANDOMIZED_BENCHMARKING"]
                ].fidelity
            elif "SIMULTANEOUS_RANDOMIZED_BENCHMARKING" in fidelity_names:
                one_qubit_fidelity = oneQubitProperty[
                    fidelity_names["SIMULTANEOUS_RANDOMIZED_BENCHMARKING"]
                ].fidelity
            else:
                raise ValueError(
                    f"No valid one-qubit RB data found for qubit {qubit} in oneQubitProperties."
                )

            one_qubit_depolarizing_rate = 1 - one_qubit_fidelity
            noise_model.add_noise(
                Depolarizing(one_qubit_depolarizing_rate), GateCriteria(qubits=qubit)
            )

            # Apply one qubit READOUT noise
            readout_error_rate = 1 - oneQubitProperty[fidelity_names["READOUT"]].fidelity
            noise_model.add_noise(BitFlip(readout_error_rate), ObservableCriteria(qubits=qubit))

        for edge, data in device_em_properties.twoQubitProperties.items():
            qubits = [int(qubit) for qubit in edge.split("-")]
            twoQubitGateFidelity = data.twoQubitGateFidelity

            valid_gate_names = {
                gate_fidelity.gateName.lower(): ind
                for ind, gate_fidelity in enumerate(twoQubitGateFidelity)
                if gate_fidelity.gateName.lower() in BRAKET_GATES
            }

            if len(valid_gate_names) == 0:
                raise ValueError(
                    f"No valid two-qubit RB data found for edge {edge} in twoQubitProperties."
                )

            # Apply two qubit RB Depolarizing Noise
            for gate_name, gate_ind in valid_gate_names.items():
                gate_fidelity = twoQubitGateFidelity[gate_ind]
                two_qubit_depolarizing_rate = 1 - gate_fidelity.fidelity
                gate = BRAKET_GATES[gate_name]
                noise_model.add_noise(
                    TwoQubitDepolarizing(two_qubit_depolarizing_rate),
                    GateCriteria(gate, [(qubits[0], qubits[1]), (qubits[1], qubits[0])]),
                )

        return noise_model
