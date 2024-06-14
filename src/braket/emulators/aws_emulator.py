from __future__ import annotations

from braket.emulators.emulater_interface import EmulatorInterface
from braket.circuits.noise_model import NoiseModel
from braket.aws import AwsDevice, AwsSession
from braket.emulators.emulator_passes import (
    EmulatorCriterion,
    NativeGateCriterion, 
    SupportedGateCriterion,
    ConnectivityCriterion
)
from braket.emulators.device_noise_models import GateDeviceNoiseModel
from braket.device_schema import DeviceActionType
from braket.device_schema import (
            DeviceCapabilities, 
            DeviceConnectivity, 
            DeviceActionType
)


from typing import Optional 


class AwsEmulator(AwsDevice, EmulatorInterface):
    """
    An emulator whose structure and constraints and defined by an AWS Braket Device. An AWS Emulator is created by passing a valid device ARN. 
    Device metadata is used to instantiate the emulator criteria. 
    """

    def __init__(self, 
                 arn: str,
                 backend: str = "default", 
                 aws_session: Optional[AwsSession] = None, 
                 noise_model: Optional[NoiseModel] = None
    ):
        EmulatorInterface.__init__(self)
        AwsDevice.__init__(self, arn, aws_session, noise_model)
        self._backend = backend
        self._initialize_gate_set_criteria()
        self._initialize_connectivity_criteria()
        self._initialize_emulator_noise_model()
        


    def _initialize_gate_set_criteria(self):
        """
        Initializes the emulator to support only the gate set and native gate set supported by the target device.
        args: 
            aws_device (AwsDevice): The Braket AwsDevice from which to copy the supported and native gate sets from.         
        """
        
        #create native gate criterion to validate gates inside of a verbatim box
        native_gates = self.properties.paradigm.nativeGateSet
        native_gate_criterion = NativeGateCriterion(native_gates)
        self.add_pass(native_gate_criterion)

        #create supported gate criterion to validate gates outside of a verbatim box
        supported_gates = self.properties.action[DeviceActionType.OPENQASM].supportedOperations
        supported_gates_criterion = SupportedGateCriterion(supported_gates)
        self.add_pass(supported_gates_criterion)


    def _initialize_connectivity_criteria(self): 
        self.add_pass(ConnectivityCriterion(self.topology_graph))

    def _initialize_emulator_noise_model(self):
        emulator_noise_model = GateDeviceNoiseModel(self._arn, self.properties)
        self._emulator_noise_model = emulator_noise_model
        
        
    