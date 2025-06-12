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

import json
from typing import Any, Dict, Optional, Union

from braket.device_schema.device_capabilities import DeviceCapabilities
from braket.device_schema.gate_model_qpu_paradigm_properties_v1 import (
    GateModelQpuParadigmProperties,
)
from braket.emulation.emulator import Emulator
from networkx import DiGraph, complete_graph, from_edgelist
from braket.emulation.device_emulator_properties import DeviceEmulatorProperties

from braket.passes.circuit_passes import (
    QubitCountValidator,
    GateValidator,
    ConnectivityValidator,
)

class LocalEmulator(Emulator):
    """
    A local emulator that mimics the restrictions and noises of a QPU based on the provided device properties.
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
            device_properties (Union[DeviceCapabilities, DeviceEmulatorProperties]): The device properties to use for emulation.
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
            device_em_properties = DeviceEmulatorProperties.from_device_properties(device_properties)
        else:
            raise ValueError(
                f"device_properties is an instance of either DeviceCapabilities or DeviceEmulatorProperties."
            )


        if backend != "braket_dm":
            raise ValueError(f"backend can only be `braket_dm`.")
        
        # Create a noise model based on the provided device properties
        noise_model = None

        # Initialize with device properties and specified backend
        emulator = cls(backend=backend, noise_model=noise_model, **kwargs)

        # Add the passes for validation
        emulator.add_pass(QubitCountValidator(device_em_properties.qubitCount))
        emulator.add_pass(GateValidator(device_em_properties.nativeGateSet))
        emulator.add_pass(
            ConnectivityValidator(
                connectivity_graph = device_em_properties.connectivityGraph,
                num_qubits = device_em_properties.qubitCount,
                qubit_labels = device_em_properties.qubit_labels,
                directed = device_em_properties.directed,
                )
            )
        # emulator.add_pass(gate_connectivity_validator(device_properties, self.topology_graph))

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

        device_emu_properties = DeviceEmulatorProperties.from_json(device_properties_json)
        return cls.from_device_properties(device_emu_properties, backend=backend, **kwargs)


    # def _construct_topology_graph(device_properties: DeviceCapabilities) -> DiGraph:
    #     """Construct topology graph. If no such metadata is available, return `None`.

    #     Returns:
    #         DiGraph: topology of QPU as a networkx `DiGraph` object.
    #     """
    #     if hasattr(device_properties, "paradigm") and isinstance(
    #         device_properties.paradigm, GateModelQpuParadigmProperties
    #     ):
    #         if device_properties.paradigm.connectivity.fullyConnected:
    #             return complete_graph(
    #                 int(self.properties.paradigm.qubitCount), create_using=DiGraph()
    #             )
    #         adjacency_lists = self.properties.paradigm.connectivity.connectivityGraph
    #         edges = []
    #         for item in adjacency_lists.items():
    #             i = item[0]
    #             edges.extend([(int(i), int(j)) for j in item[1]])
    #         return from_edgelist(edges, create_using=DiGraph())
    #     else:
    #         return None
