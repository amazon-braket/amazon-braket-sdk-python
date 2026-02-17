| Imports | `from braket.ahs import AtomArrangement, DrivingField, AnalogHamiltonianSimulation` |
| Atom arrangement | `register = AtomArrangement()` |
| Add an atom by coordinates (in meters) | `register.add((5.7e-6, 5.7e-6))` |
| Get coordinates | `register.coordinate_list(axis)` |
| Create a driving field | `DrivingField(amplitude, phase, detuning)` |
| Create an AHS program | `ahs_program = AnalogHamiltonianSimulation(register, drive)` |
| Run an AHS program | `device.run(ahs_program)` |
