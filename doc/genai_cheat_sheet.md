# Amazon Braket SDK Cheat Sheet

## What is…?

[Amazon Braket](https://aws.amazon.com/braket/) is a fully managed AWS service that helps researchers, scientists, and developers get started with quantum computing. Quantum computing has the potential to solve some computational problems that are beyond the reach of classical computers because it harnesses the laws of quantum mechanics to process information in new ways.

## Circuits

| Imports | `from braket.circuits import Circuit, Gate, Instruction`<br>`from braket.circuits.observables import X` |
| Create a circuit | `circuit = Circuit()` |
| Add gates | `circuit.x(0).rx(1, 1.23).cnot(0, 1)` |
| Get the list of available gates | `[attr for attr in dir(Gate) if attr[0].isupper()]` |
| Apply a unitary matrix | `circuit.unitary(matrix, [0])` |
| Get the circuit unitary | `circuit.to_unitary()` |
| Add a result type | `circuit.probability(0)`<br>`circuit.expectation(0.5 * X() @ X(), target=[0, 1])` |
| List available result types | `adjoint_gradient`, `amplitude`, `density_matrix`, `expectation`, `probability`, `sample`, `state_vector`, `variance` |
| Add a verbatim box | `circuit.add_verbatim_box(circuit2)` |
| Gate modifiers | `circuit.x(0, control=[1, 2], control_state=[0, 1], power=-0.5)` |
| Draw a circuit | `print(circuit)` |
| Import from OpenQASM3 | `Circuit.from_ir(source=qasm_str)` |
| Export to OpenQASM3 | `circuit.to_ir("OPENQASM")` |
| Create an instruction | `inst = Instruction(Gate.CPhaseShift(1.23), target=[0, 1])` |
| Add an instruction | `circuit.add_instruction(inst)` |

## FreeParameters

| Imports | `from braket.circuits import FreeParameter` |
| Create a free parameter | `alpha = FreeParameter("alpha")` |
| Use a free Parameter | `circuit.rx(0, alpha)`| 
| Free parameter algebra | `beta = 2 * alpha + 1`| 
| Bind a value | `circuit.make_bound_circuit({"alpha": 0.1})`| 
| Get the list of unbound FreeParameters| `circuit.parameters`| 
| Inline compilation| `device.run(circuit, inputs={"alpha": 0.1})`|

## Tasks

| Imports | `from braket.aws import AwsSession, AwsQuantumTask` |
| Create a quantum task by executing a circuit | `task = device.run(circuit)` |
| Disable qubit rewiring|  `device.run(circuit, disable_qubit_rewiring=True)` |
| Instantiate an AwsSession|  `session = AwsSession(...)` |
| Recreate a quantum task | `task = AwsQuantumTask(arn, aws_session=session)` |
| Queue position|  `task.queue_position()` |
| Get task ID | `task.id` |
| Get task state | `task.state()` |
| Get task result | `result = task.result()` |
| Get task metadata | `task.metadata()` |
| Cancel a task | `task.cancel()` |

## Program Sets

| Task | Code |
|---|---|
| Import ProgramSet | `from braket.program_sets import ProgramSet` |
| Import CircuitBinding | `from braket.program_sets import CircuitBinding` |
| Import ParameterSets | `from braket.program_sets import ParameterSets` |
| Create parameter sets | `params = ParameterSets({"theta": [0.1, 0.2, 0.3]})` |
| Create circuit binding | `binding = CircuitBinding(circuit, input_sets=params)` |
| Create program set | `program_set = ProgramSet([circuit])` |
| Set shots per executable | `program_set = ProgramSet([circuit], shots_per_executable=100)` |
| Zip circuits with matching observables | `program_set = ProgramSet.zip(circuits=[circuit], observables=[observable])` |
| Create Cartesian product with observables | `program_set = ProgramSet.product(circuits=[circuit], observables=[observable], shots_per_executable=100)` |
| Run locally | `result = LocalSimulator().run(program_set, shots=100).result()` |
| Run on a device | `task = device.run(program_set, shots=100)` |
| Emulate a program set | `task = emulator.run(program_set, shots=100)` |
| Note | Circuits used in program sets cannot have result types attached. |

## Results

| Retrieve results | `result = task.result()` |
| Get measurement counts | `result.measurement_counts` |
| Get measured qubits | `result.measured_qubits` |
| Get compiled circuit | `result.get_compiled_circuit()` |

## Device

| Imports | `from braket.aws import AwsDevice`<br>`from braket.devices import Devices` |
| Instantiate a device | `device = AwsDevice("<deviceARN>")` |
| Device alias, use in place of string ARN | `Devices.Amazon.SV1` |
| Queue depth | `device.queue_depth()` |
| Gate pulse implementation, if available | `device.gate_calibrations` |

## Device Properties

| Connectivity graph | `device.properties.paradigm.connectivity` |
| Provider specs, if available | `device.properties.provider.specs` |
| Native gate set | `device.properties.paradigm.nativeGateSet` |
| Cost and availability | `device.properties.service` |
| Pulse properties | `device.properties.pulse` |
| OpenQASM action properties | `action_properties = device.properties.action["braket.ir.openqasm.program"]` |
| Supported gates | `action_properties.supportedOperations` |

## Pricing

| Imports | `from braket.tracking import Tracker`<br>`from braket.tracking.pricing import Pricing` |
| Start the cost tracker | `tracker = Tracker().start()` |
| Get QPU task cost | `tracker.qpu_tasks_cost()` |
| Get simulator task cost | `tracker.simulator_tasks_cost()` |
| Get task statistics | `tracker.quantum_tasks_statistics()` |
| Search pricing data | `Pricing().price_search(**filters)` |

## Hybrid Jobs

| Task | Code |
|---|---|
| Imports | `from braket.aws import AwsQuantumJob`<br>`from braket.jobs import hybrid_job`<br>`from braket.jobs.metrics import log_metric` |
| Create a job from a script | `job = AwsQuantumJob.create(device=device_arn, source_module="algorithm_script.py", entry_point="algorithm_script:start_here", wait_until_complete=True)` |
| Queue position | `job.queue_position()` |
| Define a local hybrid job | `@hybrid_job(device=None, local=True)` |
| Define an AWS hybrid job | `@hybrid_job(device=device_arn)` |
| Add job dependencies | `@hybrid_job(device=device_arn, dependencies="requirements.txt")` |
| Include local modules | `@hybrid_job(device=device_arn, include_modules="my_module")` |
| Pass input data | `@hybrid_job(device=device_arn, input_data={"input": "data.csv"})` |
| Use a reservation ARN | `@hybrid_job(device=device_arn, reservation_arn=reservation_arn)` |
| Record Braket Hybrid Job metrics | `log_metric(metric_name="loss", value=loss, iteration_number=step)` |

## Reservations

| Task | Code |
|---|---|
| Imports | `from braket.aws import DirectReservation` |
| Use reservation as a context manager | `with DirectReservation(device, reservation_arn=reservation_arn):` |
| Start reservation context manually | `reservation = DirectReservation(device, reservation_arn=reservation_arn).start()` |
| Stop manual reservation context | `reservation.stop()` |
| Pass reservation ARN directly to a task | `task = device.run(circuit, shots=100, reservation_arn=reservation_arn)` |
| Use reservation with hybrid job decorator | `@hybrid_job(device=device_arn, reservation_arn=reservation_arn)` |
| Note | Reservation examples require AWS credentials, a configured AWS region, and a valid Braket Direct reservation ARN. |

## Simulators

| Imports | `from braket.devices import LocalSimulator` |
| Instantiate the local simulator | `local_sim = LocalSimulator()` |
| Instantiate with backend | `local_sim = LocalSimulator("default")` |
| Instantiate with noise model | `local_sim = LocalSimulator(noise_model=noise_model)` |
| Run a local task | `task = local_sim.run(circuit, shots=100)` |
| Run a local batch | `batch = local_sim.run_batch([circuit1, circuit2], shots=100)` |
| Get available local backends | `LocalSimulator.registered_backends()` |
| Get simulator properties | `local_sim.properties` |

## Emulators

| Task | Code |
|---|---|
| Import LocalEmulator | `from braket.emulation.local_emulator import LocalEmulator` |
| Import LocalSimulator | `from braket.devices import LocalSimulator` |
| Get emulator from AWS device | `emulator = device.emulator` |
| Create emulator from device properties | `emulator = LocalEmulator.from_device_properties(device.properties)` |
| Create emulator from device properties JSON | `emulator = LocalEmulator.from_json(device_properties_json)` |
| Run a circuit on an emulator | `task = emulator.run(circuit, shots=100)` |
| Validate a circuit before running | `emulator.validate(circuit)` |
| Transform a circuit before running | `compiled_circuit = emulator.transform(circuit)` |
| Generic local simulation | `task = LocalSimulator().run(circuit, shots=100)` |
| Note | Creating an emulator from an AWS device may require AWS credentials and a configured AWS region because device properties must be loaded. |

## Noise Simulation

| Imports | `from braket.circuits import Gate, Noise` |
| Depolarizing noise | `circuit.depolarizing(0, probability=0.1)` |
| Apply a Kraus operator | `circuit.kraus([0, 2], matrices=[E0, E1])` |
| Phase damping channel | `noise = Noise.PhaseDamping(0.1)` |
| Apply a noise channel | `circuit.apply_gate_noise(noise, target_gates=Gate.X)` |

## Experimental Features

| Task | Code |
|---|---|
| Imports | `from braket.experimental_capabilities import EnableExperimentalCapability` |
| Enable experimental capabilities temporarily | `with EnableExperimentalCapability():` |
| Add IQM feed-forward measurement | `circuit.measure_ff(0, feedback_key=0)` |
| Add IQM classically controlled PRx | `circuit.cc_prx(0, angle_1=0.15, angle_2=0.25, feedback_key=0)` |
| Pass experimental capabilities to a task | `task = device.run(circuit, shots=100, experimental_capabilities="ALL")` |
| Note | Experimental capabilities may change between SDK releases. Check device support and provider restrictions before production use. |

## Low-Level Device Control

| Imports | `from braket.pulse import PulseSequence, Frame`<br>`from braket.pulse.waveforms import ConstantWaveform, GaussianWaveform, DragGaussianWaveform` |
| Create a new pulse sequence | `pulse_sequence = PulseSequence()` |
| Predefined ports | `device.ports` |
| Predefined frames | `device.frames` |
| Create a frame | `frame = Frame(port, frequency, phase)` |
| Predefined waveforms | `ConstantWaveform(length, iq)`<br>`GaussianWaveform(length, width, amplitude, zero_at_edges)`<br>`DragGaussianWaveform(length, width, amplitude, beta, zero_at_edges)` |
| Play a waveform | `pulse_sequence.play(frame, waveform)` |
| Add a delay | `pulse_sequence.delay(frame, delay)` |
| Set frequency | `pulse_sequence.set_frequency(frame, frequency)` |
| Shift frequency | `pulse_sequence.shift_frequency(frame, frequency_shift)` |
| Set phase | `pulse_sequence.set_phase(frame, phase)` |
| Shift phase | `pulse_sequence.shift_phase(frame, phase_shift)` |
| Swap phases | `pulse_sequence.swap_phases(frame_1, frame_2)` |
| Set scale | `pulse_sequence.set_scale(frame, scale)` |
| Add a barrier | `pulse_sequence.barrier([frame_1, frame_2])` |
| Capture from a frame | `pulse_sequence.capture_v0(frame)` |
| Bind pulse parameters | `pulse_sequence.make_bound_pulse_sequence({"theta": 0.1})` |
| Export to OpenPulse IR | `pulse_sequence.to_ir()` |
| Get the time trace | `pulse_sequence.to_time_trace()` |

## Analog Hamiltonian Simulation

| Imports | `from braket.ahs import AtomArrangement, DrivingField, AnalogHamiltonianSimulation` |
| Atom arrangement | `register = AtomArrangement()` |
| Add an atom by coordinates, in meters | `register.add((5.7e-6, 5.7e-6))` |
| Get coordinates | `register.coordinate_list(axis)` |
| Create a driving field | `drive = DrivingField(amplitude, phase, detuning)` |
| Create an AHS program | `ahs_program = AnalogHamiltonianSimulation(register, hamiltonian)` |
| Export to AHS IR | `ahs_program.to_ir()` |
| Import from AHS IR | `AnalogHamiltonianSimulation.from_ir(source)` |
| Discretize for a device | `ahs_program.discretize(device)` |
| Run an AHS program | `device.run(ahs_program)` |

## Error Mitigation

| Task | Code |
|---|---|
| Import Debias | `from braket.error_mitigation import Debias` |
| Use debias error mitigation | `device.run(circuit, shots=2500, device_parameters={"errorMitigation": Debias()})` |
| Get sharpened probabilities, if returned | `result.additional_metadata.ionqMetadata.sharpenedProbabilities` |

## Console

The Amazon Braket console is a web interface for viewing service resources, device information, notebooks, reservations, and managed jobs.

| Console area | Use |
|---|---|
| Devices | View device summaries, status, connectivity, properties, and availability |
| Notebooks | Create and manage Braket notebook instances |
| Braket Direct | Manage device reservations, expert advice, and office hours |
| Quantum tasks | View, search, and inspect submitted quantum tasks |
| Hybrid jobs | View, search, and inspect Braket Hybrid Jobs |

## API Calls

| Cancel a Braket hybrid job | CancelJob |
| Cancel the specified task | CancelQuantumTask |
| Create a Braket hybrid job | CreateJob |
| Create a quantum task | CreateQuantumTask |
| Retrieve the devices available in Braket | GetDevice |
| Retrieve the specified Braket hybrid job | GetJob |
| Retrieve the specified quantum task | GetQuantumTask |
| Show the tags associated with this resource | ListTagsForResource |
| Search for devices using the specified filters | SearchDevices |
| Search for Braket hybrid jobs that match the specified filter values | SearchJobs |
| Search for tasks that match the specified filter values | SearchQuantumTasks |
| Add a tag to the specified resource | TagResource |
| Remove tags from a resource | UntagResource |

## Qiskit Provider

| Imports | `from qiskit_braket_provider import BraketProvider` |
| Instantiate a provider | `provider = BraketProvider()` |
| Instantiate a backend | `backend = provider.get_backend("SV1")` |

## Resources

- [Amazon Braket](https://aws.amazon.com/braket/)
- [Official documentation](https://docs.aws.amazon.com/braket/)
- [AWS Quantum blog](https://aws.amazon.com/blogs/quantum-computing/)
- [Braket Python SDK source](https://github.com/amazon-braket/amazon-braket-sdk-python)
- [Default simulator source](https://github.com/amazon-braket/amazon-braket-default-simulator-python)
- [Notebook examples](https://github.com/amazon-braket/amazon-braket-examples)
- [Algorithm library](https://github.com/amazon-braket/amazon-braket-algorithm-library/tree/main)
- [Pennylane plugin](https://github.com/amazon-braket/amazon-braket-pennylane-plugin-python)
- [Qiskit-Braket plugin](https://github.com/qiskit-community/qiskit-braket-provider)
- [Braket Julia SDK](https://github.com/amazon-braket/Braket.jl)
