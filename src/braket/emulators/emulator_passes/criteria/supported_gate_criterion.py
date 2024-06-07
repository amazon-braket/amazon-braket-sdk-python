from collections.abc import Iterator 
from braket.circuits.gate import Gate
from braket.emulators.criteria import EmulatorCriterion
from braket.circuits import Circuit
from braket.circuits.translations import BRAKET_GATES


class SupportedGateCriterion(EmulatorCriterion):
    def __init__(self, supported_gates: Iterator[str]):
        """
        args: 
            supported_gates (Iterator[str]): A list of gates supported by the emulator. A gate can
            be a QASM symbol, a Braket gate name, or a Braket gate instance. 
        """
        if len(supported_gates) == 0:
            raise ValueError("At least one supported gate must be provided.")
            
        try:
            self._supported_gates = set(BRAKET_GATES[gate] for gate in supported_gates) 
        except KeyError as e:
            raise ValueError(f"Input {str(e)} is not a valid Braket gate name.")

    def validate(self, circuit: Circuit) -> None: 
        for instruction in circuit.instructions: 
            if isinstance(instruction.operator, Gate):
                gate = instruction.operator
                if  type(gate) in self._supported_gates:
                    continue
                else:
                    raise ValueError(f"Gate {gate.name} is not supported by this emulator.")
                
    def __eq__(self, other: EmulatorCriterion) -> bool:
        return  isinstance(other, SupportedGateCriterion) and \
                self._supported_gates == other._supported_gates
    
