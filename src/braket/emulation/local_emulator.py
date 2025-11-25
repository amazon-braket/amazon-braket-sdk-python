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

from braket.device_schema.device_capabilities import DeviceCapabilities

from braket.circuits.noise_model import GateCriteria, NoiseModel, ObservableCriteria
from braket.circuits.noise_model.measure_criteria import MeasureCriteria
from braket.circuits.noises import (
    BitFlip,
    Depolarizing,
    TwoQubitDepolarizing,
)
from braket.circuits.translations import BRAKET_GATES
from braket.devices.local_simulator import LocalSimulator
from braket.emulation.device_emulator_properties import DeviceEmulatorProperties
from braket.emulation.emulator import Emulator
from braket.emulation.passes._device_emulator_validators import (
    _set_up_connectivity_validator,
    _set_up_gate_connectivity_validator,
)
from braket.emulation.passes.circuit_passes import (
    GateValidator,
    QubitCountValidator,
    ResultTypeValidator,
    _NotImplementedValidator,
)


class LocalEmulator(Emulator):
    """
    A local emulator that mimics the restrictions and noises of a QPU based on the provided device
    properties.
    """

    @classmethod
    def from_device_properties(
        cls,
        device_properties: DeviceCapabilities | DeviceEmulatorProperties,
        backend: str = "braket_dm",
        **kwargs,
    ) -> LocalEmulator:
        """Create a LocalEmulator instance from device properties.

        Args:
            device_properties (DeviceCapabilities, DeviceEmulatorProperties): The device
                properties to use for emulation.
            backend (str): The backend to use for simulation. Default is "braket_dm".
            **kwargs: Additional keyword arguments to pass to the LocalEmulator constructor.

        Returns:
            LocalEmulator: A new LocalEmulator instance configured with the given properties.

        Raises:
            TypeError: If the device_properties is not a DeviceCapabilities or
                DeviceEmulatorProperties object
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

        # Create a noise model based on the provided device properties
        noise_model = cls._setup_basic_noise_model_strategy(device_em_properties)

        passes = [
            _NotImplementedValidator(),
            QubitCountValidator(device_em_properties.qubit_count),
            GateValidator(native_gates=device_em_properties.native_gate_set),
            _set_up_connectivity_validator(device_em_properties),
            _set_up_gate_connectivity_validator(device_em_properties),
            ResultTypeValidator(
                device_em_properties.supported_result_types,
                device_em_properties.connectivity_graph,
            ),
        ]

        local_backend = LocalSimulator(backend=backend, noise_model=noise_model)
        return cls(backend=local_backend, noise_model=noise_model, passes=passes, **kwargs)

    @classmethod
    def from_json(
        cls,
        device_properties_json: str,
        backend: str = "braket_dm",
        **kwargs,
    ) -> LocalEmulator:
        """Create a LocalEmulator instance from a device properties JSON string.

        Args:
            device_properties_json (str): Device properties JSON string.
            backend (str): The backend to use for simulation. Defaults to "braket_dm".
            **kwargs: Additional keyword arguments to pass to the LocalEmulator constructor.

        Returns:
            LocalEmulator: A new LocalEmulator instance configured with the given properties.
        """

        device_emu_properties = DeviceEmulatorProperties.from_json(device_properties_json)
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

        Args:
            device_em_properties (DeviceEmulatorProperties): The device emulator properties.

        Returns:
            NoiseModel: A noise model configured with the appropriate noise channels.
        """
        noise_model = NoiseModel()

        # Add one-qubit noise channels
        cls._add_one_qubit_noise(noise_model, device_em_properties)

        # Add two-qubit noise channels
        cls._add_two_qubit_noise(noise_model, device_em_properties)

        return noise_model

    @classmethod
    def _add_one_qubit_noise(
        cls, noise_model: NoiseModel, device_em_properties: DeviceEmulatorProperties
    ) -> None:
        """
        Add one-qubit noise channels to the noise model:
        - One-qubit depolarizing noise based on RB fidelity
        - One-qubit readout error

        Args:
            noise_model (NoiseModel): The noise model to add noise channels to.
            device_em_properties (DeviceEmulatorProperties): The device emulator properties.
        """
        for qubit_str, data in device_em_properties.one_qubit_properties.items():
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

            # Notes for the scaling factor 3/2:
            # For a given input density matrix rho, and error rate p,
            # Depolarizing(p, rho) = (1-4p/3)rho + (4p/3)(I/2) where (I/2) is the one
            # qubit maximally mixed state. Then for a pure state rho = |0><0|, or
            # generally |ψ><ψ|, the input-output state fidelity reads 1-2p/3.
            # Hence, for a "target one qubit gate average gate fidelity" q,
            # which is the spec in the device property, the corresponing
            # "target one qubit gate average error rate" is (1-q) * 3/2, not (1-q).
            one_qubit_depolarizing_rate = (1 - one_qubit_fidelity) * 3 / 2

            noise_model.add_noise(
                Depolarizing(one_qubit_depolarizing_rate), GateCriteria(qubits=qubit)
            )

            # Apply one qubit READOUT noise
            readout_error_rate = 1 - oneQubitProperty[fidelity_names["READOUT"]].fidelity
            noise_model.add_noise(BitFlip(readout_error_rate), ObservableCriteria(qubits=qubit))
            noise_model.add_noise(BitFlip(readout_error_rate), MeasureCriteria(qubits=qubit))

    @classmethod
    def _add_two_qubit_noise(
        cls, noise_model: NoiseModel, device_em_properties: DeviceEmulatorProperties
    ) -> None:
        """
        Add two-qubit noise channels to the noise model:
        - Two-qubit depolarizing noise based on gate fidelity

        Args:
            noise_model (NoiseModel): The noise model to add noise channels to.
            device_em_properties (DeviceEmulatorProperties): The device emulator properties.
        """
        for edge, data in device_em_properties.two_qubit_properties.items():
            qubits = [int(qubit) for qubit in edge.split("-")]
            twoQubitGateFidelity = data.twoQubitGateFidelity

            valid_gate_names = {
                gate_fidelity.gateName.lower(): ind
                for ind, gate_fidelity in enumerate(twoQubitGateFidelity)
                if gate_fidelity.gateName.lower() in BRAKET_GATES
            }

            if not valid_gate_names:
                raise ValueError(
                    f"No valid two-qubit RB data found for edge {edge} in twoQubitProperties."
                )

            # Apply two qubit RB Depolarizing Noise
            for gate_name, gate_ind in valid_gate_names.items():
                gate_fidelity = twoQubitGateFidelity[gate_ind]

                # Notes for the scaling factor 5/4:
                # For a given input density matrix rho, and error rate p,
                # TwoQubitDepolarizing(p, rho) = (1-16p/15)rho + (16p/15)(I/4) where (I/4) is
                # the two qubit maximally mixed state. Then for a pure state rho = |00><00|,
                # or generally |ψ><ψ|, the input-output state fidelity reads 1-4p/5.
                # Hence, for a "target two qubit gate average gate fidelity" q,
                # which is the spec in the device property, the corresponing
                # "target two qubit gate average error rate" is (1-q) * 5/4, not (1-q).
                two_qubit_depolarizing_rate = (1 - gate_fidelity.fidelity) * 5 / 4

                gate = BRAKET_GATES[gate_name]
                noise_model.add_noise(
                    TwoQubitDepolarizing(two_qubit_depolarizing_rate),
                    GateCriteria(gate, [(qubits[0], qubits[1]), (qubits[1], qubits[0])]),
                )
