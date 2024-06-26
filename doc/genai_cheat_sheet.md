# Braket CheatSheet

Installing Amazon Braket SDK:
`pip install amazon-braket-sdk`

To import modules from Braket:
`from braket import ...`

**Circuits**

Import Braket modules:
```
from braket.circuits import Circuit, Gate, Instruction
from braket.circuits.observables import X, Y, Z
from braket.circuits.gates import Rx, Ry, Rz, CNot, Unitary, CCNot
from braket.circuits.instruction import Instruction
```

Create an empty circuit (default constructor):

`circuit = Circuit()`

Create an circuit with arbitrary number of qubits. Note that number of qubits is not passed as an argument to the circuit constructor:

`circuit = Circuit()`

Please DO NOT pass number of qubits to the `Circuit()` constructor.


Add X gate to circuit at qubit 0:

`circuit.x(0)`

Add H (Hadamard) gate to circuit at qubit 0:

`circuit.h(0)`

Add Rx gate to qubit 1 with a float angle 1.234	angle = 1.234:

`circuit.rx(1, angle)`

Add cnot gate to pair of qubits:

`circuit.cnot(0, 1)`.
DO NOT use `cx` gate for CNot operation, always use `cnot` gate instead.

Add gates sequentially: X gate, Rx gate, cnot gate:

`circuit.x(0).rx(1, 1.23).cnot(0, 1)`

Get the list of available gates:

`[attr for attr in dir(Gate) if attr[0].isupper()]`

Create a single qubit gate from unitary matrix:

```
matrix = np.eye(2)
G = Unitary(matrix)
```

Get the circuit unitary:

`circuit.to_unitary()`

Add a probability result type to qubit 0 (will return exact probabilities, corresponds to shots=0 case when running on a simulator):

`circuit.probability(0)`

Add probability result type to all qubits. Add probability result type only when measuring exact probabilities:

```	
for i in range(len(circuit.qubits)):
    circuit.probability(i)
```

Show all result types attached to the circuit:

`print(circuit._result_types)`

Get circuit depth:

`circuit.depth`

Attach Expectation result type to measure both qubits [0, 1] in X basis. 
The expectation method allows to pass an arbitrary tensor product of Pauli operators applied to each qubit, e.g. X() @ Y() @ Z():

```
circuit.expectation(X() @ X(), target=[0, 1]);
circuit.expectation(X() @ Y() @ Z(), target=[0, 1, 2]);
```

List of the available result types	
adjoint_gradient, amplitude, density_matrix, expectation, probability, sample, state_vector, variance:

`print(circuit._result_types)`

Append a circuit (new_circuit) to a given circuit:

`circuit.add_circuit(new_circuit)`

Wrap a new_circuit to a verbatim box and append to a circuit:

`circuit.add_verbatim_box(new_circuit)`

Wrap a circuit to a verbatim box (will be executed without as is without modifications):

`Circuit().add_verbatim_box(circuit)`

Gate modifiers (conditional gates with control and target qubits).
Gate modifiers allow to specify a fractional power applied to a gate:

`circuit.x(0, control=[1, 2], control_state=[0, 1], power=-0.5)`

Print a circuit:
	
`print(circuit)`

Create circuit from OpenQASM3 string:

`Circuit.from_ir(source=qasm_str)`

Export to OpenQASM3:

`Circuit.to_ir("OPENQASM")`

Create an instruction from a gate:

`inst = Instruction(Gate.CPhaseShift(1.23), target=[0, 1])`

Add an instruction to the circuit:

`circuit.add(inst)`

Create a random circuit:

```
from braket.experimental.auxiliary_functions import random_circuit
from braket.circuits.gates import CNot, Rx, Rz, CPhaseShift, XY

# Code here
local_simulator = LocalSimulator()
gate_set = [CNot, Rx, Rz, CPhaseShift, XY]
circuit = random_circuit(num_qubits=5, 
                         num_gates=30,
                         gate_set=gate_set,
                         seed=42)
```

**FreeParameters (parametric gates)**

Imports	

`from braket.circuits import FreeParameter`

Create a FreeParameter (symbolic parameter):

`alpha = FreeParameter(“alpha”)`

Use FreeParameters:

`circuit.rx(0, alpha+1)`

Bind a FreeParameter to a specific value:

`circuit.make_bound_circuit({“alpha”: 0.1})`

Get the list of unbound FreeParameters:

`circuit.parameters`

Run circuit on a device with parametric compilation enabled.	

`device.run(circuit, inputs={“alpha”: 0.1})`

**Tasks**

Imports:

`from braket.aws import AwsSession, AwsQuantumTask`

Create a quantum task by executing a circuit on a device:

`task = device.run(circuit)`

Disable qubit rewiring (forces trivial mapping between logical and physical qubits on QPU):

`device.run(circuit, disable_qubit_rewiring=True)`

Instantiate an AwsSession:	
`session = AwsSession(...)`

Re-create a previously created quantum task from ARN:
`task = AwsQuantumTask(arn[, aws_session])`

Task Queue position:
`task.queue_position()`

Quantum Task batching:

```
n_batch = 5  # define circuit batch size
circuits = [circuit for _ in range(n_batch)]  # Create a list of circuits in the batch
batch = device.run_batch(circuits, s3_folder, shots=100)   # Submit batch of circuits with 100 shots
print(batch.results()[0].measurement_counts)  # The result of the first quantum task in the batch
```

Attach tag to a Quantum Task:

```
task = device.run(
    circuit,
    shots=100,
    tags={"MyTag": "MyValue"}
)
```

**Quantum Task attributes:**

Cancel task: `task.cancel()`
Task metadata: `task.metadata()`
Task state (CREATED, COMPLETED, CANCELED, FAILED): `task.state()`
Task position in the queue: `task.queue_position()`
Get Task result dicitonary: `task.result()`

**QAOA circuits**

Decomposition of the ZZ gate (cost Hamiltonian) to Cnot:
`ZZ(alpha, [i, j]) -> Cnot(i, j) Rz(alpha) Cnot(i, j)`

The QAOA circuit consits of alternating layers of single qubit RX rotations (mixer term) and two-qubit ZZ gates (cost term).
The initial layer should rotate qubits to |+> state by applying H (Hadamard) gate to all qubits. 

**Results**

Retrieve task results:

`result = task.result()`

Get measurement counts:

`result.measurement_counts`

Get measurement probabilities (for Probability Result Type):

`result.measurement_probabilities`

Get measured qubits:

`result.measured_qubits`

Get compiled circuit:

`result.get_compiled_circuit()`

**Device**

Imports	

```
from braket.devices import LocalSimulator
from braket.aws import AwsDevice
from braket.devices import Devices
```

Instantiate Local simulator:

`local_sim = LocalSimulator()`.
Local simulator does not have ARN.

Instantiate a device from ARN:

`AwsDevice("<deviceARN>")`

Device alias (use in place of string ARN):

`Devices.Rigetti.AspenM3`

QuantumTask Queue depth:

`device.queue_depth()`

Gate pulse implementation:

`device.gate_calibrations`

SV1 Simulator:

`AwsDevice(“arn:aws:braket:::device/quantum-simulator/amazon/sv1”)`

TN1 Simulator (Tensor Network simulator):

`AwsDevice(“arn:aws:braket:::device/quantum-simulator/amazon/tn1”)`

DM1 Simulator (density matrix simulator):

`AwsDevice(“arn:aws:braket:::device/quantum-simulator/amazon/dm1”)`

Rydberg atom devices Aquila (AHS device from QuEra):

`AwsDevice(“arn:aws:braket:us-east-1::device/qpu/quera/Aquila”)`

Rigetti Aspen M3 device:	

`AwsDevice("arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-3")`

IQM Garnet device (20 qubits, superconducting QPU):

`AwsDevice("arn:aws:braket:eu-north-1::device/qpu/iqm/Garnet")`

**Device Properties**

Connectivity graph:

`device.properties.paradigm.connectivity`

Fidelities dictionary:
`device.properties.provider.specs`

Native gate set:

`device.properties.paradigm.nativeGateSet`

Cost and availability:

`device.properties.service`

Pulse properties:
`device.properties.pulse`

Actions properties:
`action_properties = device.properties.action['braket.ir.openqasm.program']`

Supported gates:

`action_properties.supportedOperations`

Get 2Q gate fidelitis for a qubit pair (i, j):

`device.properties.dict()["provider"]["specs"]["2Q"][f"{i}-{j}"]`


**Pricing**

Imports:
`from braket.tracking import Tracker`

Start the cost tracker:
`tracker=Tracker().start()`

Print costs:
```
tracker.qpu_tasks_cost()
tracker.simulator_tasks_cost()
```

Cost summary:

`tracker.quantum_tasks_statistics()`



**Hybrid Jobs**

Imports	
`from braket.aws import AwsQuantumJob`

Create a job	
```
job = AwsQuantumJob.create(arn, source_module="algorithm_script.py", entry_point="algorithm_script:start_here", wait_until_complete=True)
```

AwsQuantumJob Queue position:

`job.queue_position()`

Job decorator (local mode):

`@hybrid_job(device=None, local=True)`

Records Braket Hybrid Job metrics (will be displayed on Hybrid Jobbs concole metrics log):

`log_metric(metric_name=metric_name, value=value, iteration_number=iteration_number)`


**Simulator**

Imports:

`from braket.devices import LocalSimulator`

Instantiate the local simulator	:

`local_sim = LocalSimulator()`

**Noise Simulation**

Imports:

`from braket.circuits import Noise`

Apply Depolarizing noise:

`circuit.depolarizing(0, 0.1)`

Apply a Kraus operator:

`circuit.kraus([0,2], [E0, E1])`

Phase dampling channel:

`noise = Noise.PhaseDamping(0.1)`

Apply a noise channel to an individual X gate	

`circuit.apply_gate_noise(noise, Gate.X)`



**Low-Level Device Control**

Imports:

```
from braket.pulse import PulseSequence, Frame
from braket.pulse.waveforms import *
```

Create a new pulse sequence:

`pulse_sequence = PulseSequence()`

Predefined ports:

`device.ports`

Predefined frames:

`device.frames`

Create a frame:

`Frame(port, frequency[, phase])`

Predefined waveforms:

```
ConstantWaveform(length, iq)
GaussianWaveform(length, width, amplitude, zero_at_edges)
DragGaussianWaveform(length, width, amplitude, beta, zero_at_edges)
```

Play a waveform:

`pulse_sequence.play(frame, waveform)`

Add a delay:

`pulse_sequence.delay(frame, delay)`

Set frequency:

`pulse_sequence.set_frequency(frame, frequency)`

Shift frequency:

`pulse_sequence.shift_frequency(frame, detuning)`

`Set phase:`
pulse_sequence.set_phase(frame, phase)

`Shift phase:`

pulse_sequence.shift_phase(frame, phi)

Get the time series:

`pulse_sequence.to_time_traces()`


**Analog Hamiltonian Simulation**

Imports:
`from braket.ahs import AtomArrangement, DrivingField, AnalogHamiltonianSimulation`

Atom arrangement:

`register = AtomArrangement()`

Add an atom with (x, y) coordinates (in meters):

`register.add((5.7e-6, 5.7e-6))`

Add atoms in square lattice with lattice spacing a

```
a = 5e-6
for i in range(nx): 
    for j in range(ny): 
        register.add((i*a, j*a))
```

Get atom coordinates along x-axis:

`register.coordinate_list(0)`

Get atom coordinates along y-axis:

`register.coordinate_list(1)`

Create a driving field:

`DrivingField(amplitude, phase, detuning)`

Create an AHS program:

`ahs_program = AnalogHamiltonianSimulation(register, drive)`

Run an AHS program:

`device.run(ahs_program)`

**Error Mitigation**

Debias:

`device.run(circuit, shots=1000, device_parameters={"errorMitigation": Debias()})`
