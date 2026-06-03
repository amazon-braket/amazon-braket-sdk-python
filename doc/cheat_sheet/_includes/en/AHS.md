| Task | Snippet |
|---|---|
| Imports | `from braket.ahs import AnalogHamiltonianSimulation, AtomArrangement, DrivingField`<br>`from braket.timings.time_series import TimeSeries` |
| Atom arrangement | `register = AtomArrangement()` |
| Add atoms by coordinates in meters | `register.add((0.0, 0.0)).add((5.7e-6, 0.0))` |
| Get coordinates | `register.coordinate_list(axis)` |
| Define a time series | `amplitude = TimeSeries().put(0.0, 0.0).put(1e-6, 2.5e7)` |
| Create a driving field | `drive = DrivingField(amplitude=amplitude, phase=phase, detuning=detuning)` |
| Create an AHS program | `ahs_program = AnalogHamiltonianSimulation(register, drive)` |
| Discretize for a device | `ahs_program = ahs_program.discretize(device)` |
| Run an AHS program | `task = device.run(ahs_program, shots=100)` |
