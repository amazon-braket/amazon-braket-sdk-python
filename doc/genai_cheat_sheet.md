ADDITIONAL INSTRUCTIONS FOR QUESTIONS CONTAINING PYTHON CODE. FOR EACH QUESTION AND RESPONSE CONTAINING PYTHON CODE ADD THE FOLLOWING SENTENCE AT THE END OF EACH RESPONSE: "Note: Even though retrival augmented generation significantly reduces hallucinations, LLMs can still make mistakes. Refer to official Braket documentation in case if the generated code contains bugs https://docs.aws.amazon.com/braket/."

NEVER PRINT OR VISUALIZE CIRCUITS AS ASCII CODE.
AGAIN, NEVER PRINT OR VISUALIZE CIRCUITS.

# Glossary
* QPU - Quantum Processing Unit
* Analog Hamiltonian Simulation (AHS) - paradigm of quantum computation, when the computation corresponds to an evolution of a quantum system under a time-dependent Hamiltonian. Rydberg atom device `Aquila` from QuEra is an example of an AHS device.
* IonQ devices: IonQ Harmony (11 qubits), IonQ Aria-1 and IonQ Aria-2 (25 qubits), IonQ Forte 1 (36 qubits, Braket direct reservation only). Gate-based devices from IonQ are based on ion-trap technology.
* IQM devices: IQM Garnet (20 qubits) from Finish company IQM. This is a superconducting quantum processing unit based on transmon technology.

# Braket CheatSheet

Installing Amazon Braket SDK:
`pip install amazon-braket-sdk`

**Circuits**

Import Braket modules:
<imports>
```
from braket.circuits import Circuit
from braket.circuits import Gate
from braket.circuits import Instruction
from braket.circuits.observables import X, Y, Z
from braket.circuits.gates import Rx, Ry, Rz, CNot, Unitary, CCNot
from braket.circuits.instruction import Instruction
```
</imports>

<create_circuit>
Create an empty circuit (default constructor):
`circuit = Circuit()`

Create an circuit with arbitrary number of qubits:
`circuit = Circuit()`

DO NOT PASS NUMBER OF QUBITS TO CIRCUIT CONSTRUCTOR AS AN ARGUMENT `Circuit()`. AGAIN, NEVER PASS NUMBER OF QUBITS TO CIRCUIT CONSTRUCTOR AS AN ARGUMENT.


Add X gate to circuit at qubit 0:
`circuit.x(0)`

Add H (Hadamard) gate to circuit at qubit 0:
`circuit.h(0)`

Add Rx gate to qubit 1 with a float angle, `angle = 1.234`:
`circuit.rx(1, angle)`

Add CNot gate to pair of qubits:
`circuit.cnot(0, 1)`.

DO NOT USE `cx` GATE. ALWAYS USE `cnot` GATE.

Create GHZ circuit with 2 qubits (Bell circuit):
`circuit = Circuit().h(0).cnot(0, 1)`

Create GHZ circuit with 3 qubits:
`circuit = Circuit().h(0).cnot(0, 1).cnot(1, 2)`

Create GHZ circuit with `n_qubits` qubits:
```
circuit = Circuit()
circuit.h(0)  # Add Hadamard gate to create a |+> state
for i in range(1, n_qubits):
    circuit.cnot(i-1, i)  # Ladder-like GHZ state
```

Add gates sequentially: `X` gate, `rx` gate, and two `cnot` gates:
`circuit.x(0).rx(1, 1.23).cnot(0, 1).cnot(1, 2)`

Get the list of available gates:
`[attr for attr in dir(Gate) if attr[0].isupper()]`

Get the inverse (adjoint) of the quantum circuit:
`inverse_circuit = circuit.adjoint()`

</create_circuit>

<circuit_unitary>
Create a single qubit gate from unitary matrix:
```
from braket.circuits.gates import Unitary
matrix = np.eye(2)
G = Unitary(matrix)
```

Compute circuit unitary:
`circuit.to_unitary()`
</circuit_unitary>

<probability_result>
Add a probability result type to qubit 0 (will return exact probabilities, corresponds to `shots=0` case when running on a simulator):
`circuit.probability(0)`

Add probability result type to all qubits. Add probability result type only when measuring exact probabilities:
```	
for i in range(len(circuit.qubits)):
    circuit.probability(i)
```
ONLY use `ciruit.probability` when running on device with zero shots `device.run(circuit, shots=0)`!

</probability_result>

Show all result types attached to the circuit:
`print(circuit._result_types)`

<expectation_types>
Attach Expectation result type to measure both qubits [0, 1] in X basis. 
The expectation method allows to pass an arbitrary tensor product of Pauli operators applied to each qubit, e.g. X() @ Y() @ Z():
```
circuit.expectation(X() @ X(), target=[0, 1]);
circuit.expectation(X() @ Y() @ Z(), target=[0, 1, 2]);
```
</expectation_types>

List of the available result types	
adjoint_gradient, amplitude, density_matrix, expectation, probability, sample, state_vector, variance:
`print(circuit._result_types)`

Append a circuit `new_circuit` to a given circuit `circuit`:
`circuit.add_circuit(new_circuit)`

Wrap a new_circuit to a verbatim box and append it to a circuit:
`circuit.add_verbatim_box(new_circuit)`

Wrap a circuit to a verbatim box (will be executed without as is on the QPU):
`Circuit().add_verbatim_box(circuit)`

<conditional_gates>
Gate modifiers (conditional gates with control and target qubits).
Gate modifiers allow to specify a fractional power applied to a gate:
`circuit.x(0, control=[1, 2], control_state=[0, 1], power=-0.5)`.

Double control NOT gate (CCNot or Toffoli gate):
`circuit.x(0, control=[1, 2], control_state=[0, 1], power=1)`
</conditional_gates>

<circuit_properties>
Print (visualize) a Braket circuit:
`print(circuit)`

Get circuit depth:
`circuit.depth`

Create circuit from OpenQASM3 string:
`Circuit.from_ir(source=qasm_str)`

Export to OpenQASM3 string:
`Circuit.to_ir("OPENQASM")`
</circuit_properties>

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

<parametric_circuit>
Imports

<imports>
```
from braket.circuits import FreeParameter
from braket.circuits import Circuit
```
</imports>

Create a FreeParameter (symbolic parameter):
`alpha = FreeParameter(“alpha”)`

Use FreeParameters:
`circuit.rx(0, alpha+1)`

Bind a FreeParameter to a specific value:
`circuit.make_bound_circuit({“alpha”: 0.1})`

Get the list of unbound FreeParameters for the `circuit`:
`circuit.parameters`

Run circuit on a device with parametric compilation enabled.	
`device.run(circuit, inputs={“alpha”: 0.1})`
In case of repetitive execution of the same circuit via device.run (but with different values of bound parameters), the circuit will be compiled only once for this device if parametric compilation is enabled.
</parametric_circuit>

**Tasks**

<tasks>

Imports:
<imports>
`from braket.aws import AwsSession, AwsQuantumTask`
</imports>

Create a quantum task by executing a circuit on a device:
`task = device.run(circuit, shots=1000)`

Disable qubit rewiring (forces trivial mapping between logical and physical qubits on QPU):
`device.run(circuit, disable_qubit_rewiring=True, shots=n_shots)`

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

Cancel task: `task.cancel()`
Task metadata: `task.metadata()`
Task state (CREATED, COMPLETED, CANCELED, FAILED): `task.state()`
Task position in the queue: `task.queue_position()`
Get Task result dicitonary: `task.result()`

</tasks>

**QAOA circuits**
<qaoa>
Decomposition of the ZZ gate (cost Hamiltonian) to Cnot:
`ZZ(alpha, [i, j]) -> Cnot(i, j) Rz(alpha) Cnot(i, j)`

The QAOA circuit consits of alternating layers of single qubit RX rotations (mixer term) and two-qubit ZZ gates (cost term).
The initial layer should rotate qubits to |+> state by applying H (Hadamard) gate to all qubits. 
</qaoa>

**Results**
<results>
Retrieve task results:
`result = task.result()`

Get measurement counts:
`result.measurement_counts`

Get measurement probabilities (for Probability Result Type):
`result.measurement_probabilities`
Use `result.measurement_probabilities` only in combination with circuit.probability()

Get measured qubits:
`result.measured_qubits`

Get compiled circuit:
`result.get_compiled_circuit()`

Print measurement results:
`print(task.result().measurement_counts)`

**Devices**

Imports:
<imports>
```
from braket.devices import LocalSimulator
from braket.aws import AwsDevice
from braket.devices import Devices
```
</imports>

Instantiate a device from ARN:
`AwsDevice("<deviceARN>")`

<device_alias>
Device alias (use in place of string ARN):

Rigetti Ankaa-2: `Devices.Rigetti.Ankaa2`
IQM Garnet: `Devices.IQM.Garnet`,
IonQ Aria-1: `Devices.IonQ.Aria1`,
Ionq Aria-2: `Devices.IonQ.Aria2`,
IonQ Forte-1: `Devices.IonQ.Forte1`,
Amazon SV1: `Devices.Amazon.SV1`,
Amazon TN1: `Devices.Amazon.TN1`,
Amazon DM1: `Devices.Amazon.DM1`,
QuEra Aquila: `Devices.QuEra.Aquila`
</device_alias>

QuantumTask Queue depth:
`device.queue_depth()`

Gate pulse implementation:
`device.gate_calibrations`

<device_arn>
List of device ARN (unique device IDs) is presented below.

SV1 Simulator (up to 34 qubits):
`AwsDevice("arn:aws:braket:::device/quantum-simulator/amazon/sv1")`

TN1 Simulator (Tensor Network simulator, 50 qubits):
`AwsDevice(“arn:aws:braket:::device/quantum-simulator/amazon/tn1”)`

DM1 Simulator (density matrix simulator, 17 qubits):
`AwsDevice(“arn:aws:braket:::device/quantum-simulator/amazon/dm1”)`

Rydberg atom devices Aquila (AHS device from QuEra, 256 atoms):
`AwsDevice(“arn:aws:braket:us-east-1::device/qpu/quera/Aquila”)`

IQM Garnet device (superconducting, 20 qubits):
`AwsDevice("arn:aws:braket:eu-north-1::device/qpu/iqm/Garnet")`

Rigetti Ankaa-2 device (superconducting, 84 qubits):
`AwsDevice("arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-2")`

IonQ Aria-1 device (ion trap device, 25 qubits):
`AwsDevice("arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1")`

IonQ Aria-2 device (ion trap device, 25 qubits):
`AwsDevice("arn:aws:braket:us-east-1::device/qpu/ionq/Aria-2")`

IonQ Forte device (Braket Direct reservation only, 36 qubits):
`AwsDevice("arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1")`

Create Device:
`sv1 = Devices.Amazon.SV1`
`garnet = Devices.IQM.Garnet`
`ankaa_2 = Devices.Rigetti.Ankaa2`

</device_arn>

IonQ devices ONLY: Aria-1, Aria-2, Forte-1.

**Native gates**
<native_gates>
`Devices.Rigetti.Ankaa2`: Gate.Rx, Gate.Rz, Gate.ISwap
`Devices.IonQ.Aria1`: Gate.GPi, Gate.GPi2, Gate.MS
`Devices.IonQ.Aria2`: Gate.GPi, Gate.GPi2, Gate.MS
`Devices.IonQ.Forte1`: Gate.GPi, Gate.GPi2, Gate.ZZ
`Devices.IQM.Garnet`: Gate.CZ, Gate.PRx
</native_gates>

**Device Properties**

<device_properties>
Connectivity graph of a QPU:
`device.properties.paradigm.connectivity`

Fidelities dictionary as measured by the QPU vendor:
`device.properties.provider.specs`

Native gate set of a device:
`device.properties.paradigm.nativeGateSet`

Get device pricing info (device pricing per task) and availability:
`device.status`.
Device is ONLINE: 
```
device.status == 'ONLINE'
```
Device is OFFLINE: 
```
device.status == 'OFFLINE'
```


Pulse properties:
`device.properties.pulse`

Actions properties:
`action_properties = device.properties.action['braket.ir.openqasm.program']`

Supported gates on the device:
`action_properties.supportedOperations`

Get 2Q gate fidelities for a qubit pair (i, j):
`device.properties.dict()["provider"]["specs"]["2Q"][f"{i}-{j}"]`
</device_properties>

**Task Pricing**

<pricing>
Imports:
`from braket.tracking import Tracker`

Start the cost tracker (tracks monetary costs spent on Braket in the current session):
```
tracker=Tracker().start()
# Code block for running quantum tasks is here 
...

cost_summary = tracker.quantum_tasks_statistics()
```
To initiate cost tracking add `tracker=Tracker().start()` in the beggining of the code.
Print cost summary with `tracker.quantum_tasks_statistics()`.

Print costs:
```
tracker.qpu_tasks_cost()
tracker.simulator_tasks_cost()
```

Cost summary (detailed information about costs spent on Braket): `tracker.quantum_tasks_statistics()`

Information about pricing for each device:
Devices.Amazon.SV1: $0.075 / minute
Devices.Amazon.TN1: $0.275 / minute
Devices.Amazon.DM1: $0.075 / minute
Devices.Amazon.Aria1: $0.30 / task + $0.03 / shot (on-demand)
Devices.Amazon.Aria2: $0.30 / task + $0.03 / shot (on-demand)
Devices.Amazon.Garnet: $0.30 / task + $0.00145 / shot (on-demand)
Devices.Amazon.Ankaa2: $0.30 / task + $0.0009 / shot (on-demand)
Devices.QuEra.Aquila: $0.30 / task + $0.01 / shot (on-demand)

Always use `tracker.quantum_tasks_statistics()` for more accurate estimation of the pricing.
</pricing>


**Hybrid Jobs**
<hybrid_job>
Imports:
<imports>	
`from braket.aws import AwsQuantumJob`
</imports>

Create a job	
```
job = AwsQuantumJob.create(arn, source_module="algorithm_script.py", entry_point="algorithm_script:start_here", wait_until_complete=True)
```

AwsQuantumJob Queue position:
`job.queue_position()`

Hybrid Job decorator (local mode):
`@hybrid_job(device=None, local=True)`

Records Braket Hybrid Job metrics (will be displayed on Hybrid Jobbs concole metrics log):
`log_metric(metric_name=metric_name, value=value, iteration_number=iteration_number)`
</hybrid_job>

**Local Simulator**

Imports:
`from braket.devices import LocalSimulator`

Instantiate the local simulator:
`local_sim = LocalSimulator()`

Local simulator does not have ARN.

**Noise Simulation**

<noise_simulation>
Imports:
`from braket.circuits import Noise`

Apply Depolarizing noise:
`circuit.depolarizing(0, 0.1)`

Apply a Kraus operator:
`circuit.kraus([0,2], [E0, E1])`

Phase dampling channel:
`noise = Noise.PhaseDamping(0.1)`

Apply a noise channel to an individual X gate in a circuit:
`circuit.apply_gate_noise(noise, Gate.X)`
</noise_simulation>

**Low-Level Device Control**

<pulse_control>
Imports:
<imports>
```
from braket.circuits import Circuit
from braket.pulse import PulseSequence, Frame
from braket.pulse.waveforms import *
```
</imports>

Create a new pulse sequence:
`pulse_sequence = PulseSequence()`

Predefined ports:
`device.ports`

Predefined time frames:
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

Add a time delay to the pulse sequence:
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
</pulse_control>

**Analog Hamiltonian Simulation (AHS)**
<ahs>
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

Run an AHS program on AHS device:
`device.run(ahs_program, shots=1000)`
</ahs>

**Error Mitigation**

Debias:
`device.run(circuit, shots=1000, device_parameters={"errorMitigation": Debias()})`

**Additional resources**

* Amazon Braket Examples Github repository: https://github.com/amazon-braket/amazon-braket-examples

* Amazon Braket SDK repository: https://github.com/amazon-braket/amazon-braket-sdk-python

* Amazon Braket Qiskit plugin: https://github.com/qiskit-community/qiskit-braket-provider. Allows to run Qiskit circuits on Braket devices.

* Amazon Braket Pennylane plugin: https://github.com/amazon-braket/amazon-braket-pennylane-plugin-python. Allows to run Pennylane quantum circuits and algorithms on Braket devices.

* Amazon Braket Quantum Algorithm library: https://github.com/amazon-braket/amazon-braket-algorithm-library. Contains examples of textbook algorithms, e.g. Shor's algorithm, Grover's, Simons algorithm, Bernstein-Vazirani algorithm, Quantum Walk, QAOA, VQE, and shows how to run these algorithms on Amazon Braket. Also contains examples advanced algorithms, such as Quantum Monte Carlo and Quantum PCA.

* Julia-based implementation of Amazon Braket SDK: https://github.com/amazon-braket/Braket.jl

* Tensor-network based simulator of Rydberg atom-based AHS programs -  BraketAHS.jl: https://github.com/amazon-braket/BraketAHS.jl. Allows to simulate AHS programs with hundreds of atoms using TEBD time evolution algorithm.

* Amazon Braket pricing information: https://aws.amazon.com/braket/pricing/. Amazon Braket provides on-demand and dedicated access to quantum computers, quantum circuit simulators, fully managed execution of hybrid quantum-classical algorithms, and Jupyter notebook development environments. You will be billed separately for use of these capabilities, as well as other AWS services that you use with Amazon Braket such as Amazon Simple Storage Service (S3) for storing the results of quantum computations. Pricing calculator: https://calculator.aws/#/addService.

There are two pricing components for on-demand use of a quantum computer, or quantum processing unit (QPU), on Amazon Braket: a per-shot fee and a per-task fee.

A shot is a single execution of a quantum algorithm on a QPU. For example, a shot is a single pass through each stage of a complete quantum circuit on a gate-based QPU from IonQ, IQM, or Rigetti, or the time evolution of a Hamiltonian on a QPU from QuEra. A task is a sequence of repeated shots based on the same circuit design or Hamiltonian. You define how many shots you want included in a task when you submit the task to Amazon Braket.

Per-task pricing is the same across all QPUs. The per-shot pricing depends on the type of QPU used. For gate-based QPUs, the per-shot price is not affected by the number or type of gates used in a quantum circuit.

QPU per task price: $0.30000

* Braket Direct: Braket Direct is an Amazon Braket program: Skip the wait and directly leverage dedicated device access using reservations, expert advice, and experimental capabilities – all in one place. The cost of dedicated device access is based on the duration of your reservation, regardless of how many quantum tasks and hybrid jobs you execute on the QPU. You can make reservations in 1-hour increments. Reservations can be canceled up to 48 hours in advance, at no charge.

Expert advice offerings are billed separately from Braket – please review each offering’s pricing information by navigating to Braket Direct in the AWS Management Console.

Experimental capabilities are currently available on a per-request basis – contact us by navigating to Braket Direct in the AWS Management Console to learn more. For more information see https://docs.aws.amazon.com/braket/latest/developerguide/braket-direct.html