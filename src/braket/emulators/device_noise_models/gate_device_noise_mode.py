from abc import ABC, abstractmethod
from braket.circuits.noise_model import GateCriteria, NoiseModel, ObservableCriteria
from typing import List
from dataclasses import dataclass
from typing import Dict, Tuple, List, Set, Optional
from braket.circuits import Gate
from braket.circuits.noise_model import NoiseModel
from braket.devices import Devices
from braket.aws import AwsDevice
from braket.device_schema.standardized_gate_model_qpu_device_properties_v1 import (
    StandardizedGateModelQpuDeviceProperties, OneQubitProperties, GateFidelity2Q, Fidelity1Q
)
import logging
from braket.circuits.noises import AmplitudeDamping, BitFlip, Depolarizing, PhaseDamping, TwoQubitDepolarizing

import numpy as np

@dataclass
class GateFidelity:
    gate_name: str
    fidelity:float
    
    
"""
 The following gate duration values are not available through Braket device calibration data and must
 be hardcoded. 
"""
QPU_GATE_DURATIONS = {
    Devices.Rigetti.AspenM3: {
        "single_qubit_gate_duration": 40e-9,
        "two_qubit_gate_duration": 240e-9
    }, 
    Devices.IQM.Garnet: {
        "single_qubit_gate_duration": 32e-9,
        "two_qubit_gate_duration": 60e-9
    }
}

GATE_NAME_TRANSLATIONS = {
    "CPHASE": "CPhaseShift", 
    "GPI": "GPi"
}
    
    
@dataclass
class GateDeviceCalibrationData:
    single_qubit_gate_duration: float
    two_qubit_gate_duration: float
    qubit_labels: Set[int]
    single_qubit_specs: Dict[int, Dict[str, float]]
    two_qubit_edge_specs: Dict[Tuple[int, int], List[GateFidelity]]
    
    def _validate_single_qubit_specs(self):
        for qubit in self.single_qubit_specs.keys():
            if qubit not in self.qubit_labels:
                raise ValueError(f"Invalid qubit label {qubit}")
            
    def _validate_two_qubit_specs(self):
        for edge in self.two_qubit_edge_specs.keys():
            if edge[0] not in self.qubit_labels or edge[1] not in self.qubit_labels:
                raise ValueError(f"Invalid qubit pair {edge}")
            
    def __post_init__(self):
        self._validate_single_qubit_specs()
        self._validate_two_qubit_specs()
    

class GateDeviceNoiseModel(NoiseModel):
    def __init__(self, arn: str, aws_device: AwsDevice = None):
        super().__init__()
        self._arn = arn
        device_properties = (aws_device or AwsDevice(self._arn)).properties
        self._gate_calibration_data = self._setup_device_calibration_data(device_properties)
        self._setup_basic_noise_model_strategy()
    
    def _setup_device_calibration_data(self, device_properties) -> GateDeviceCalibrationData:
        if hasattr(device_properties, "standardized") and isinstance(
            device_properties.standardized, StandardizedGateModelQpuDeviceProperties
        ):
            return self._setup_standardized_calibration_data(device_properties)
        elif self._arn in Devices.IonQ:
            return self._setup_ionq_device_calibration_data(device_properties)
        
    
    def _setup_standardized_calibration_data(self, device_properties) -> GateDeviceCalibrationData:
        gate_durations = QPU_GATE_DURATIONS.get(self._arn, None)
        if not gate_durations:
            raise ValueError(f"Gate durations are not available for device {self._arn}")
        single_qubit_gate_duration = gate_durations["single_qubit_gate_duration"]
        two_qubit_gate_duration = gate_durations["two_qubit_gate_duration"]
        
        standardized_properties = device_properties.standardized
        one_qubit_properties = standardized_properties.oneQubitProperties
        qubit_labels = set(int(qubit) for qubit in one_qubit_properties.keys())
        single_qubit_specs = {int(qubit): self._create_qubit_specs(one_qubit_properties[qubit]) for qubit in one_qubit_properties.keys()}
            
        
        two_qubit_properties = standardized_properties.twoQubitProperties
        two_qubit_edge_specs = {
            tuple(int(qubit) for qubit in edge.split("-")[0:2]): self._create_edge_specs(gate_fidelities.twoQubitGateFidelity)
            for edge, gate_fidelities in two_qubit_properties.items()}
        return GateDeviceCalibrationData(
            single_qubit_gate_duration,
            two_qubit_gate_duration,
            qubit_labels,
            single_qubit_specs,
            two_qubit_edge_specs
        )
        
    def _create_qubit_specs(self, qubit_properties: OneQubitProperties) -> Dict[str, int]:
        T1 = qubit_properties.T1.value
        T2 = qubit_properties.T2.value
        qubit_fidelities = qubit_properties.oneQubitFidelity
        one_qubit_fidelities = {
            qubit_fidelity.fidelityType.name : qubit_fidelity.fidelity for qubit_fidelity in qubit_fidelities
        }
        one_qubit_fidelities["T1"] = T1
        one_qubit_fidelities["T2"] = T2
        return one_qubit_fidelities
    
    def _create_edge_specs(self, edge_properties: List[GateFidelity2Q]) -> List[GateFidelity]:
        return [
            GateFidelity(GATE_NAME_TRANSLATIONS.get(gate_fidelity.gateName, gate_fidelity.gateName), gate_fidelity.fidelity)
            for gate_fidelity in edge_properties
        ]
    
    
    def _setup_ionq_device_calibration_data(self, device_properties):
        """
            IonQ's Trapped Ion Devices do not have per-qubit calibration data and instead
            provide averaged qubit and two-qubit gate fidelities across the device. All qubits
            are connected in a trapped ion device.
            
            We instead copy the averaged fidelities to each qubit and qubit edge pair. 
        """
        calibration_data = device_properties.provider
        fidelity_data = calibration_data.fidelity
        timing_data = calibration_data.timing
        qubit_count = device_properties.paradigm.qubitCount
        native_gates = device_properties.paradigm.nativeGateSet
        single_qubit_gate_duration = timing_data["1Q"]
        two_qubit_gate_duration = timing_data["2Q"]
        average_active_reset_fidelity = timing_data["reset"]
        average_T1 = timing_data["T1"]
        average_T2 = timing_data["T2"]
        single_qubit_rb_fidelity = fidelity_data["1Q"]["mean"]
        two_qubit_rb_fidelity = fidelity_data["2Q"]["mean"]
        average_readout_fidelity = fidelity_data["spam"]["mean"]

        native_gate_fidelities = [
            GateFidelity(GATE_NAME_TRANSLATIONS.get(native_gate, native_gate), two_qubit_rb_fidelity) for native_gate in native_gates
        ]
        
        single_qubit_specs = {}
        two_qubit_edge_specs = {}
        for ii in range(qubit_count):
            qubit_spec = {
                "RANDOMIZED_BENCHMARKING": single_qubit_rb_fidelity, 
                "SIMULTANEOUS_RANDOMIZED_BENCHMARKING": None,
                "READOUT": average_readout_fidelity,
                "T1": average_T1,
                "T2": average_T2,
                "ACTIVE_RESET": average_active_reset_fidelity
            }
            single_qubit_specs[ii] = qubit_spec
            
            for jj in range(ii + 1, qubit_count):
                two_qubit_edge_specs[(ii, jj)] = native_gate_fidelities
        
        return GateDeviceCalibrationData(
            single_qubit_gate_duration,
            two_qubit_gate_duration,
            set(range(qubit_count)),
            single_qubit_specs,
            two_qubit_edge_specs
        )
        
        
    def _setup_basic_noise_model_strategy(self):
        """
            Apply a basic noise model strategy consisting of: 
                - T1 Dampening
                - T2 Phase Dampening
                - 1 Qubit RB Depolarizing Noise 
                - 1 Qubit Readout Error
                - 2 Qubit Gate Depolarizing Noise
        """
        gate_duration_1Q = self._gate_calibration_data.single_qubit_gate_duration
        gate_duration_2Q = self._gate_calibration_data.two_qubit_gate_duration
        for qubit, data in self._gate_calibration_data.single_qubit_specs.items():
            #T1 dampening
            T1 = data["T1"]
            damping_prob = 1 - np.exp(-(gate_duration_1Q/T1))
            self.add_noise(AmplitudeDamping(damping_prob), GateCriteria(qubits=qubit))
            
            #T2 Phase Dampening
            T2 = data["T2"]
            dephasing_prob = 0.5 * (1 - np.exp(-(gate_duration_1Q/T2)))
            self.add_noise(PhaseDamping(dephasing_prob), GateCriteria(qubits=qubit))
            
            #1 Qubit RB Depolarizing Noise
            if "SIMULTANEOUS_RANDOMIZED_BENCHMARKING" in data:
                benchmark_fidelity = data["SIMULTANEOUS_RANDOMIZED_BENCHMARKING"]
            else:
                benchmark_fidelity = data.get(["RANDOMIZED_BENCHMARKING"])
            if benchmark_fidelity:
                depolarizing_rate = 1 - benchmark_fidelity
                self.add_noise(Depolarizing(depolarizing_rate), GateCriteria(qubits=qubit))
            
            #1 Qubit Readout Error
            readout_error_rate = 1 - data["READOUT"]
            self.add_noise(BitFlip(readout_error_rate), ObservableCriteria(qubits=qubit))
            
        for edge, data in self._gate_calibration_data.two_qubit_edge_specs.items():
            for gate_fidelity in data:
                rate = 1 - gate_fidelity.fidelity
                gate_name = gate_fidelity.gate_name
                if hasattr(Gate, gate_name):
                    gate = getattr(Gate, gate_name)
                else:
                    # raise ValueError(f"Cannot find gate {gate_name}.")
                    logging.warning(f"Cannot find gate {gate_name}.")
                    continue
                self.add_noise(TwoQubitDepolarizing(rate), GateCriteria(gate, [(edge[0], edge[1]), (edge[1], edge[0])]))
        
            