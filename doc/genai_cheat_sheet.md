# Amazon Braket SDK Cheat Sheet

Generated from `doc/cheat_sheet/_data/blocks.yml` and `_includes/en/`.

## What is Amazon Braket?

[Amazon Braket](https://aws.amazon.com/braket/) is a fully managed AWS service for building, testing, and running quantum algorithms on managed simulators, local simulators, emulators, and supported quantum hardware.

| Need | Start with |
|---|---|
| Build a circuit | `from braket.circuits import Circuit` |
| Run on AWS | `from braket.aws import AwsDevice` |
| Run locally | `from braket.devices import LocalSimulator` |
| Run many parameter sets together | `from braket.program_sets import CircuitBinding, ProgramSet` |
| Run quantum-classical code | `from braket.jobs import hybrid_job` |

## Circuits

| Task | Snippet |
|---|---|
| Imports | `from braket.circuits import Circuit, Gate, Instruction, observables` |
| Create a circuit | `circuit = Circuit()` |
| Add gates | `circuit.h(0).rx(1, 1.23).cnot(0, 1)` |
| Build an instruction | `inst = Instruction(Gate.CPhaseShift(1.23), target=[0, 1])`<br>`circuit.add(inst)` |
| Apply a unitary matrix | `circuit.unitary(matrix, targets=[0])` |
| Gate modifiers | `circuit.x(0, control=[1, 2], control_state=[0, 1], power=-0.5)` |
| Add result types | `circuit.probability(target=[0])`<br>`circuit.expectation(observable=observables.X(0) @ observables.X(1))` |
| Exact-state result types | `amplitude`, `density_matrix`, `probability`, `state_vector` |
| Sampled result types | `expectation`, `probability`, `sample`, `variance` |
| Draw a circuit | `print(circuit)` |
| Export to OpenQASM 3 | `circuit.to_ir("OPENQASM")` |
| Import from OpenQASM 3 | `Circuit.from_ir(source=qasm_source)` |
| Add a verbatim box | `circuit.add_verbatim_box(native_circuit)` |

## Free parameters

| Task | Snippet |
|---|---|
| Imports | `from braket.circuits import Circuit, FreeParameter` |
| Create a free parameter | `theta = FreeParameter("theta")` |
| Use a free parameter | `circuit = Circuit().rx(0, theta)` |
| Free parameter algebra | `phi = 2 * theta + 1` |
| Bind locally | `bound = circuit.make_bound_circuit({"theta": 0.1})` |
| List unbound parameters | `circuit.parameters` |
| Bind at task creation | `task = device.run(circuit, shots=100, inputs={"theta": 0.1})` |

## Program sets

| Task | Snippet |
|---|---|
| Imports | `from braket.program_sets import CircuitBinding, ProgramSet`<br>`from braket.circuits import Circuit, FreeParameter, observables` |
| Sweep one circuit | `theta = FreeParameter("theta")`<br>`circuit = Circuit().rx(0, theta)`<br>`binding = CircuitBinding(circuit, input_sets={"theta": [0.1, 0.2]})` |
| Create a program set | `program_set = ProgramSet(binding, shots_per_executable=100)` |
| Run a program set | `task = device.run(program_set)` |
| Mix circuits and bindings | `program_set = ProgramSet([Circuit().h(0), binding], shots_per_executable=100)` |
| Pair circuits, inputs, and observables | `ProgramSet.zip([circuit], input_sets=[{"theta": 0.1}], observables=[observables.Z(0)])` |
| Cartesian product with observables | `ProgramSet.product([circuit], observables=[observables.X(0), observables.Z(0)], shots_per_executable=100)` |
| Inspect size | `program_set.total_executables`<br>`program_set.total_shots` |
| Result lookup | `result = task.result()`<br>`first_entry = result[0][0]`<br>`first_entry.counts` |

Program sets run multiple executables in one quantum task. Do not attach regular circuit result types to circuits that are placed in a `ProgramSet`; use `CircuitBinding` observables when measuring observables.

## Quantum tasks

| Task | Snippet |
|---|---|
| Imports | `from braket.aws import AwsQuantumTask, AwsSession` |
| Create a quantum task | `task = device.run(circuit, shots=100)` |
| Run a batch | `batch = device.run_batch([circuit1, circuit2], shots=100)` |
| Disable qubit rewiring | `task = device.run(circuit, shots=100, disable_qubit_rewiring=True)` |
| Set task tags | `task = device.run(circuit, shots=100, tags={"project": "demo"})` |
| Poll with a custom timeout | `task = device.run(circuit, shots=100, poll_timeout_seconds=86400)` |
| Recreate a task from ARN | `task = AwsQuantumTask(arn, aws_session=AwsSession())` |
| Inspect queue position | `task.queue_position()` |
| Inspect state and metadata | `task.state()`<br>`task.metadata()` |
| Cancel a task | `task.cancel()` |

## Results

| Task | Snippet |
|---|---|
| Retrieve task results | `result = task.result()` |
| Retrieve batch results | `results = batch.results()` |
| Measurement counts | `result.measurement_counts` |
| Measurement probabilities | `result.measurement_probabilities` |
| Measured qubits | `result.measured_qubits` |
| Result-type values | `result.values` |
| Value by result type | `result.get_value_by_result_type(result_type)` |
| Compiled circuit, if returned by the provider | `result.get_compiled_circuit()` |
| Program set result entry | `program_result = result[0]`<br>`entry = program_result[0]` |

## Devices

| Task | Snippet |
|---|---|
| Imports | `from braket.aws import AwsDevice, AwsDeviceType`<br>`from braket.devices import Devices` |
| Managed simulator | `device = AwsDevice(Devices.Amazon.SV1)` |
| QPU alias | `device = AwsDevice(Devices.IonQ.Forte1)` |
| ARN string | `device = AwsDevice("arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1")` |
| Search devices | `AwsDevice.get_devices(types=[AwsDeviceType.QPU], statuses=["ONLINE"])` |
| Queue depth | `device.queue_depth()` |
| Device status | `device.status` |
| Device ARN | `device.arn` |
| QPU emulator | `emulator = device.emulator()` |
| Pulse frames and ports | `device.frames`<br>`device.ports` |

## Device properties

| Property | Access |
|---|---|
| Connectivity graph | `device.properties.paradigm.connectivity` |
| Native gate set | `device.properties.paradigm.nativeGateSet` |
| Service metadata | `device.properties.service` |
| Provider metadata | `device.properties.provider` |
| Pulse properties | `device.properties.pulse` |
| Supported actions | `device.properties.action` |
| OpenQASM action properties | `device.properties.action["braket.ir.openqasm.program"]` |
| Program set action properties | `device.properties.action["braket.ir.openqasm.program_set"]` |
| Supported operations | `device.properties.action["braket.ir.openqasm.program"].supportedOperations` |

## Reservations

| Task | Snippet |
|---|---|
| Imports | `from braket.aws import DirectReservation` |
| Run tasks in a reservation context | `with DirectReservation(device, reservation_arn=reservation_arn):`<br>`    task = device.run(circuit, shots=100)` |
| Start and stop explicitly | `reservation = DirectReservation(device, reservation_arn=reservation_arn)`<br>`reservation.start()`<br>`task = device.run(circuit, shots=100)`<br>`reservation.stop()` |
| Pass the reservation directly | `task = device.run(circuit, shots=100, reservation_arn=reservation_arn)` |
| Use with the hybrid job decorator | `@hybrid_job(device=Devices.IonQ.Forte1, reservation_arn=reservation_arn)` |
| Use with `AwsQuantumJob.create` | `AwsQuantumJob.create(device=Devices.IonQ.Forte1, source_module="job.py", entry_point="job:run", reservation_arn=reservation_arn)` |

Reservation ARNs are device and AWS account specific. Use the same device that was reserved for the reservation window.

## Hybrid Jobs

| Task | Snippet |
|---|---|
| Imports | `from braket.aws import AwsDevice, AwsQuantumJob`<br>`from braket.devices import Devices`<br>`from braket.jobs import get_job_device_arn, hybrid_job` |
| Create a script-based job | `job = AwsQuantumJob.create(device=Devices.Amazon.SV1, source_module="algorithm_script.py", entry_point="algorithm_script:run", wait_until_complete=True)` |
| Decorate an entry point | `@hybrid_job(device=Devices.Amazon.SV1, wait_until_complete=True)`<br>`def run_hybrid_job(num_tasks=1):`<br>`    device = AwsDevice(get_job_device_arn())` |
| Local decorator mode | `@hybrid_job(device=None, local=True)` |
| Pass dependencies | `@hybrid_job(device=Devices.Amazon.SV1, dependencies="requirements.txt")` |
| Use a reservation | `@hybrid_job(device=Devices.IonQ.Forte1, reservation_arn=reservation_arn)` |
| Log metrics inside a job | `from braket.jobs.metrics import log_metric`<br>`log_metric(metric_name="loss", value=loss, iteration_number=i)` |
| Read job output | `job.result()` |
| Queue position | `job.queue_position()` |

## Simulators

| Task | Snippet |
|---|---|
| Imports | `from braket.devices import LocalSimulator`<br>`from braket.aws import AwsDevice`<br>`from braket.devices import Devices` |
| Local state-vector simulator | `device = LocalSimulator()` |
| Local density-matrix simulator | `device = LocalSimulator("braket_dm")` |
| Run locally | `result = device.run(circuit, shots=100).result()` |
| Exact local simulation | `result = device.run(circuit).result()` |
| Local batch | `batch = device.run_batch([circuit1, circuit2], shots=100)` |
| Installed local backends | `LocalSimulator.registered_backends()` |
| Managed state-vector simulator | `device = AwsDevice(Devices.Amazon.SV1)` |
| Managed density-matrix simulator | `device = AwsDevice(Devices.Amazon.DM1)` |
| Managed tensor-network simulator | `device = AwsDevice(Devices.Amazon.TN1)` |

## Emulators

| Task | Snippet |
|---|---|
| Imports | `from braket.emulation.local_emulator import LocalEmulator` |
| Create from an AWS QPU | `emulator = device.emulator()` |
| Create from device properties | `emulator = LocalEmulator.from_device_properties(device.properties)` |
| Create from JSON properties | `emulator = LocalEmulator.from_json(device_properties_json)` |
| Validate without running | `emulator.validate(circuit)` |
| Transform before running | `compiled = emulator.transform(circuit)` |
| Run through emulator backend | `result = emulator.run(circuit, shots=100).result()` |
| Add custom validation passes | `from braket.emulation import PassManager` |

Emulators mimic QPU restrictions and noise on a local simulator backend. They are useful for checking device compatibility before submitting to hardware.

## Noise simulation

| Task | Snippet |
|---|---|
| Imports | `from braket.circuits import Circuit, Gate, Noise`<br>`from braket.circuits.noise_model import GateCriteria, NoiseModel` |
| Add inline bit-flip noise | `circuit.bit_flip(0, probability=0.1)` |
| Add inline depolarizing noise | `circuit.depolarizing(0, probability=0.1)` |
| Add Kraus noise | `circuit.kraus([0, 2], [E0, E1])` |
| Create a noise channel | `noise = Noise.PhaseDamping(gamma=0.1)` |
| Apply noise after gates | `circuit.apply_gate_noise(noise, Gate.X)` |
| Build a noise model | `noise_model = NoiseModel().add_noise(Noise.BitFlip(0.05), GateCriteria(Gate.H))` |
| Run with local density-matrix simulator | `device = LocalSimulator("braket_dm", noise_model=noise_model)` |

## Experimental capabilities

| Task | Snippet |
|---|---|
| Imports | `from braket.experimental_capabilities import EnableExperimentalCapability`<br>`from braket.circuits import Circuit` |
| Enable inside a block | `with EnableExperimentalCapability():`<br>`    circuit = Circuit().measure_ff(0, 0).cc_prx(1, 1.57, 0.0, 0)` |
| IQM feed-forward measurement | `circuit.measure_ff(target=0, feedback_key=0)` |
| IQM classically controlled PRx | `circuit.cc_prx(target=1, angle_1=1.57, angle_2=0.0, feedback_key=0)` |
| Use with verbatim execution | `wrapped = Circuit().add_verbatim_box(circuit)` |

Experimental capabilities are opt-in and may change. The SDK raises an error if experimental operators are constructed outside `EnableExperimentalCapability`.

## Pulse control

| Task | Snippet |
|---|---|
| Imports | `from braket.pulse import Frame, PulseSequence`<br>`from braket.pulse.waveforms import ConstantWaveform, DragGaussianWaveform, GaussianWaveform` |
| Create a pulse sequence | `pulse_sequence = PulseSequence()` |
| Use predefined ports | `ports = device.ports` |
| Use predefined frames | `frames = device.frames` |
| Create a frame | `frame = Frame(port, frequency, phase=0)` |
| Constant waveform | `waveform = ConstantWaveform(length, iq)` |
| Gaussian waveform | `waveform = GaussianWaveform(length, width, amplitude, zero_at_edges=True)` |
| DRAG Gaussian waveform | `waveform = DragGaussianWaveform(length, width, amplitude, beta, zero_at_edges=True)` |
| Play a waveform | `pulse_sequence.play(frame, waveform)` |
| Delay a frame | `pulse_sequence.delay(frame, delay)` |
| Shift frequency or phase | `pulse_sequence.shift_frequency(frame, detuning)`<br>`pulse_sequence.shift_phase(frame, phi)` |
| View time traces | `pulse_sequence.to_time_traces()` |

## Analog Hamiltonian Simulation

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

## Error mitigation

| Task | Snippet |
|---|---|
| Imports | `from braket.error_mitigation import Debias` |
| Debias | `task = device.run(circuit, shots=2500, device_parameters={"errorMitigation": Debias()})` |
| Sharpened probabilities, if returned | `task.result().additional_metadata.ionqMetadata.sharpenedProbabilities` |

## Cost tracking

| Task | Snippet |
|---|---|
| Imports | `from braket.tracking import Tracker` |
| Start the cost tracker | `tracker = Tracker().start()` |
| Print costs | `tracker.qpu_tasks_cost()`<br>`tracker.simulator_tasks_cost()` |
| Cost summary | `tracker.quantum_tasks_statistics()` |

## Console

The [Amazon Braket console](https://console.aws.amazon.com/braket/home) shows current service and device information.

| Area | Use |
|---|---|
| Devices | Status, availability windows, properties, connectivity |
| Notebooks | Managed Jupyter notebook instances |
| Braket Direct | Reservations, expert advice, office hours |
| Jobs | Hybrid job creation and run history |
| Quantum tasks | Submitted task history and details |

## Service API calls

| Operation | API |
|---|---|
| Cancel a Braket hybrid job | CancelJob |
| Cancel the specified task | CancelQuantumTask |
| Create a Braket hybrid job | CreateJob |
| Create a quantum task | CreateQuantumTask |
| Retrieve one device | GetDevice |
| Retrieve the specified Braket hybrid job | GetJob |
| Retrieve the specified quantum task | GetQuantumTask |
| Show the tags associated with this resource | ListTagsForResource |
| Search for devices using the specified filters | SearchDevices |
| Search for Braket hybrid jobs that match the specified filter values | SearchJobs |
| Search for tasks that match the specified filter values | SearchQuantumTasks |
| Add a tag to the specified resource | TagResource |
| Remove tags from a resource | UntagResource |

## Qiskit provider

Qiskit support is provided by the separate [qiskit-braket-provider](https://github.com/qiskit-community/qiskit-braket-provider) package.

| Task | Snippet |
|---|---|
| Imports | `from qiskit_braket_provider import AWSBraketProvider` |
| Instantiate a provider | `provider = AWSBraketProvider()` |
| Instantiate a backend | `provider.get_backend(name)` |

## Resources

- [Amazon Braket](https://aws.amazon.com/braket/)
- [Official documentation](https://docs.aws.amazon.com/braket/)
- [Amazon Braket Python SDK API reference](https://amazon-braket-sdk-python.readthedocs.io/)
- [AWS Quantum blog](https://aws.amazon.com/blogs/quantum-computing/)
- [Braket Python SDK source](https://github.com/amazon-braket/amazon-braket-sdk-python)
- [Default simulator source](https://github.com/amazon-braket/amazon-braket-default-simulator-python)
- [Notebook examples](https://github.com/amazon-braket/amazon-braket-examples)
- [Algorithm library](https://github.com/amazon-braket/amazon-braket-algorithm-library/tree/main)
- [Pennylane plugin](https://github.com/amazon-braket/amazon-braket-pennylane-plugin-python)
- [Qiskit-Braket plugin](https://github.com/qiskit-community/qiskit-braket-provider)
- [Braket Julia SDK](https://github.com/amazon-braket/Braket.jl)
