from collections.abc import Iterator 
from braket.circuits.gate import Gate
from braket.circuits.compiler_directives import StartVerbatimBox, EndVerbatimBox
from braket.emulators.criteria import EmulatorCriterion
from braket.circuits import Circuit
from braket.circuits.translations import BRAKET_GATES

class NativeGateCriterion(EmulatorCriterion):
    
    def __init__(self, native_gates: Iterator[str]):
        """
        args: 
            native_gates (Iterator[str]): A list of native gates supported by the emulator. 
            Validating native gates is relevant when considering whether or not a verbatim box in a program 
            is possible on a given device.
        """
        if len(native_gates) == 0:
            raise ValueError("At least one native gate must be provided.")
        try:
            self._native_gates = set(BRAKET_GATES[gate] for gate in native_gates) 
        except KeyError as e:
            raise ValueError(f"Input {str(e)} is not a valid Braket gate name.")


    def validate(self, circuit: Circuit) -> None: 
        for idx in range(len(circuit.instructions)): 
            instruction = circuit.instructions[idx]
            if isinstance(instruction.operator, StartVerbatimBox):
                idx += 1
                while idx < len(circuit.instructions) and not isinstance(circuit.instructions[idx].operator, EndVerbatimBox):
                    instruction = circuit.instructions[idx]
                    if isinstance(instruction.operator, Gate):
                        gate = instruction.operator
                        if  type(gate) in self._native_gates:
                            idx += 1
                            continue
                        raise ValueError(f"Gate {gate.name} is not a native gate supported by this emulator.")    
                    idx += 1

                if not isinstance(circuit.instructions[idx].operator, EndVerbatimBox):
                    raise ValueError(f"No end verbatim box found at index {idx} in the circuit.")
                idx += 1
                
                
    def __eq__(self, other: EmulatorCriterion) -> bool:
        return  isinstance(other, NativeGateCriterion) and \
                self._native_gates == other._native_gates
    
