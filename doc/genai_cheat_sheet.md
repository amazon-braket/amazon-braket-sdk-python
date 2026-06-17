# Braket CheatSheet

**Circuits**

***Imports:***

```
from braket.circuits import Circuit, Gate, Instruction
from braket.circuits.observables import X
```

***Create a circuit. Note that number of qubits is not passed as an argument to the circuit constructor:***

`circuit = Circuit()`

***Add gates:***

`circuit.x(0).rx(1, 1.23).cnot(0, 1)`

***Get the list of available gates:***

`[attr for attr in dir(Gate) if attr[0].isupper()]`

***Apply a unitary matrix:***

`circuit.unitary([0], matrix)`

***Get the circuit unitary:***

`circuit.to_unitary()`

***Add a result type:***

```
circuit.probability(0)
circuit.expectation(0.5 * X() @ X(), target=[0, 1])
```

***List of the available result types:***

adjoint_gradient, amplitude, density_matrix, expectation, probability, sample, state_vector, variance

***Add a verbatim box:***

`circuit.add_verbatim_box(circuit2)`

***Gate modifiers:***

`circuit.x(0, control=[1, 2], control_state=[0, 1], power=-0.5)`

***Draw a circuit:***

`print(circuit)`

***Import from OpenQASM3:***

`Circuit.from_ir(source=qasm_str)`

***Export to OpenQASM3:***

`Circuit.to_ir("OPENQASM")`

***Create an instruction:***

`inst = Instruction(Gate.CPhaseShift(1.23), target=[0, 1])`

***Add an instruction:***

`circuit.add(inst)`

**FreeParameters**

***Imports:***

`from braket.circuits import FreeParameter`

***Create a free parameter:***

`alpha = FreeParameter("alpha")`

***Use a free Parameter:***

`circuit.rx(0, alpha)`

***Free parameter algebra:***

`beta = 2 * alpha + 1`

***Bind a value:***

`circuit.make_bound_circuit({"alpha": 0.1})`

***Get the list of unbound FreeParameters:***

`circuit.parameters`

***Inline compilation:***

`device.run(circuit, inputs={"alpha": 0.1})`

**Tasks**

***Imports:***

`from braket.aws import AwsSession, AwsQuantumTask`

***Create a quantum task by executing a circuit:***

`task = device.run(circuit)`

***disable qubit rewiring:***

`device.run(circuit, disable_qubit_rewiring=True)`

***Instantiate an AwsSession:***

`session = AwsSession(...)`

***Recreate a quantum task:***

`task = AwsQuantumTask(arn[, aws_session])`

***Queue position:***

`task.queue_position()`

**Program Sets**

***Imports:***

```
from braket.program_sets import ProgramSet, CircuitBinding
from braket.circuits.observables import X, Z
```

***Bundle several circuits in one task. Circuits inside a program set cannot have result types attached:***

`program_set = ProgramSet([circuit1, circuit2], shots_per_executable=100)`

***Sweep one circuit over parameter sets:***

`binding = CircuitBinding(circuit, input_sets=[{"theta": 0.1}, {"theta": 0.2}])`

***Sweep over a Hamiltonian (observables):***

`binding = CircuitBinding(circuit, {"theta": [0.1, 0.2]}, 2.1 * X(0) @ Z(1) - 4.5 * Z(0) @ Z(1))`

***Build a program set from bindings:***

`program_set = ProgramSet(binding)`

***Pair circuits with inputs/observables:***

`ProgramSet.zip([circuit1, circuit2], observables=[X(0), Z(0)])`

***Cartesian product of circuits × observables:***

`ProgramSet.product([circuit1], [X(0), Z(0)])`

***Total number of executables:***

`program_set.total_executables`

***Run a program set:***

`task = device.run(program_set, shots=1000)`

***Expectation value of the i-th executable:***

`task.result().expectation(0)`

**Results**

***Retrieve results:***

`result = task.result()`

***Get measurement counts:***

`result.measurement_counts`

***Get measured qubits:***

`result.measured_qubits`

***Get compiled circuit:***

`result.get_compiled_circuit()`

**Device**

***Imports:***

```
from braket.aws import AwsDevice
from braket.devices import Devices
```

***Instantiate a device:***

`AwsDevice("<deviceARN>")`

***Device alias (use in place of string ARN):***

`Devices.Rigetti.Cepheus1108Q`

***Queue depth:***

`device.queue_depth()`

***Gate pulse implementation:***

`device.gate_calibrations`

**Reservations**

***Imports:***

`from braket.aws import AwsDevice, DirectReservation`

***Reserve via a context manager. Every task created inside the context is submitted against the reservation:***

```
with DirectReservation(device, reservation_arn="<arn>"):
    task = device.run(circuit, shots=100)
```

***Start / stop a reservation explicitly:***

```
res = DirectReservation(device, reservation_arn="<arn>")
res.start()
res.stop()
```

***Apply to a single quantum task:***

`device.run(circuit, shots=100, reservation_arn="<arn>")`

***Apply to a hybrid job:***

`@hybrid_job(device=Devices.IQM.Garnet, reservation_arn="<arn>")`

**Device Properties**

***Connectivity graph:***

`device.properties.paradigm.connectivity`

***Fidelities dictionary:***

`device.properties.provider.specs`

***Native gate set:***

`device.properties.paradigm.nativeGateSet`

***Cost and availability:***

`device.properties.service`

***Pulse properties:***

`device.properties.pulse`

***Actions properties:***

`action_properties = device.properties.action['braket.ir.openqasm.program']`

***Supported gates:***

`action_properties.supportedOperations`

**Experimental Capabilities**

***Imports:***

```
import math
from braket.circuits import Circuit
from braket.experimental_capabilities import EnableExperimentalCapability
```

***Enable experimental capabilities. Experimental operations raise an error unless created inside this context manager:***

```
with EnableExperimentalCapability():
    circuit = Circuit()
```

***Mid-circuit measurement into a feedback register (IQM):***

`circuit.measure_ff(0, feedback_key=0)`

***Classically-controlled PRx, conditioned on a feedback key (IQM):***

`circuit.cc_prx(1, math.pi / 2, math.pi / 4, feedback_key=0)`

***Available on:***

IQM devices (e.g. `Devices.IQM.Garnet`)

**Pricing**

***Imports:***

`from braket.tracking import Tracker`

***Start the cost tracker:***

`tracker=Tracker().start()`

***Print costs:***

```
tracker.qpu_tasks_cost()
tracker.simulator_tasks_cost()
```

***Cost summary:***

`tracker.quantum_tasks_statistics()`

**Hybrid Jobs**

***Imports:***

```
from braket.aws import AwsQuantumJob
from braket.devices import Devices
from braket.jobs import hybrid_job, save_job_result
from braket.jobs.metrics import log_metric
```

***Create a script-based job:***

`job = AwsQuantumJob.create(Devices.Amazon.SV1, source_module="algorithm_script.py", entry_point="algorithm_script:start_here", wait_until_complete=True)`

***Decorate an entry point. The job is created when the decorated function is called:***

```
@hybrid_job(device=Devices.Amazon.SV1)
def my_job():
    return save_job_result({"theta": 0.5})
```

***Run the job (creates it):***

`job = my_job()`

***Run locally without creating an AWS job:***

`@hybrid_job(device=None, local=True)`

***Add Python dependencies:***

`@hybrid_job(device=Devices.Amazon.SV1, dependencies="requirements.txt")`

***Include extra source modules:***

`@hybrid_job(device=Devices.Amazon.SV1, include_modules=["my_module"])`

***Pass input data:***

`@hybrid_job(device=Devices.Amazon.SV1, input_data="s3://my-bucket/input")`

***Use a reservation:***

`@hybrid_job(device=Devices.IQM.Garnet, reservation_arn="<arn>")`

***Record metrics inside the job:***

`log_metric(metric_name="loss", value=0.123, iteration_number=0)`

***Retrieve the result:***

`job.result()`

***Queue position:***

`job.queue_position()`

**Simulators**

***Imports:***

`from braket.devices import LocalSimulator`

***Instantiate the local simulator:***

`local_sim = LocalSimulator()`

**Emulators**

***Imports:***

```
from braket.aws import AwsDevice
from braket.devices import Devices, LocalSimulator
from braket.emulation import Emulator
from braket.emulation.local_emulator import LocalEmulator
```

***Get an emulator for a QPU. Emulators are only available for QPUs; requesting one from a managed simulator raises an error:***

`emulator = AwsDevice(Devices.IQM.Garnet).emulator`

***Validate a circuit against device constraints:***

`emulator.validate(circuit)`

***Compile a circuit to the device's native gates and connectivity:***

`compiled = emulator.transform(circuit)`

***Run on the emulated backend (applies device noise):***

`result = emulator.run(circuit, shots=100).result()`

***Inspect the device noise model:***

`emulator.noise_model`

***Build a custom emulator:***

`emulator = Emulator(backend=LocalSimulator("braket_dm"))`

***Emulator from a device-properties JSON:***

`emulator = LocalEmulator.from_json(properties_json)`

**Noise Simulation**

***Imports:***

`from braket.circuits import Noise, Gate`

***Depolarizing noise:***

`circuit.depolarizing(0, 0.1)`

***Apply a Kraus operator:***

`circuit.kraus([0,2], [E0, E1])`

***Phase damping channel:***

`noise = Noise.PhaseDamping(0.1)`

***Apply a noise channel:***

`circuit.apply_gate_noise(noise, Gate.X)`

**Low-Level Device Control**

***Imports:***

```
from braket.pulse import PulseSequence, Frame
from braket.pulse.waveforms import *
```

***Create a new pulse sequence:***

`pulse_sequence = PulseSequence()`

***Predefined ports:***

`device.ports`

***Predefined frames:***

`device.frames`

***Create a frame:***

`Frame(port, frequency[, phase])`

***Predefined waveforms:***

```
ConstantWaveform(length, iq)
GaussianWaveform(length, width, amplitude, zero_at_edges)
DragGaussianWaveform(length, width, amplitude, beta, zero_at_edges)
```

***Play a waveform:***

`pulse_sequence.play(frame, waveform)`

***Add a delay:***

`pulse_sequence.delay(frame, delay)`

***Set frequency:***

`pulse_sequence.set_frequency(frame, frequency)`

***Shift frequency:***

`pulse_sequence.shift_frequency(frame, detuning)`

***Set phase:***

`pulse_sequence.set_phase(frame, phase)`

***Shift phase:***

`pulse_sequence.shift_phase(frame, phi)`

***Get the time series:***

`pulse_sequence.to_time_traces()`

**Analog Hamiltonian Simulation**

***Imports:***

`from braket.ahs import AtomArrangement, DrivingField, AnalogHamiltonianSimulation`

***Atom arrangement:***

`register = AtomArrangement()`

***Add an atom by coordinates (in meters):***

`register.add((5.7e-6, 5.7e-6))`

***Get coordinates:***

`register.coordinate_list(axis)`

***Create a driving field:***

`DrivingField(amplitude, phase, detuning)`

***Create an AHS program:***

`ahs_program = AnalogHamiltonianSimulation(register, drive)`

***Run an AHS program:***

`device.run(ahs_program)`

**Error Mitigation**

***Debias:***

`device.run(circuit, shots=2500, device_parameters={"errorMitigation": Debias()})`

***Sharpening (if debiasing used):***

`result.additional_metadata.ionqMetadata.sharpenedProbabilities`

**Console**

***Device tab:***

```
Device summary
Connectivity
```

***Notebook:***

Jupyter hub

***Braket Direct:***

```
Device reservation
Office hours
```

**API Calls**

***Cancel a Braket hybrid job:***

CancelJob

***Cancel the specified task:***

CancelQuantumTask

***Create a Braket hybrid job:***

CreateJob

***Create a quantum task:***

CreateQuantumTask

***Retrieve the devices available in Braket:***

GetDevice

***Retrieve the specified Braket hybrid job:***

GetJob

***Retrieve the specified quantum task:***

GetQuantumTask

***Show the tags associated with this resource:***

ListTagsForResource

***Search for devices using the specified filters:***

SearchDevices

***Search for Braket hybrid jobs that match the specified filter values:***

SearchJobs

***Search for tasks that match the specified filter values:***

SearchQuantumTasks

***Add a tag to the specified resource:***

TagResource

***Remove tags from a resource:***

UntagResource

**Qiskit Provider**

***Imports:***

`from qiskit_braket_provider import AWSBraketProvider`

***Instantiate a provider:***

`provider = AWSBraketProvider()`

***Instantiate a backend:***

`provider.get_backend(name)`
