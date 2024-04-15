from qiskit_braket_provider import BraketLocalBackend
from braket.reservations import reservation
from qiskit_braket_provider import BraketProvider
from braket.devices import Devices

from braket.aws import AwsDevice
from qiskit import QuantumCircuit

circuit = QuantumCircuit(3)

# Apply H-gate to the first qubit:
circuit.h(0)

# with reservation(sv1, reservation_arn=None):
#     sv1.run_batch([Circuit().h(0), Circuit().i(0)], shots=10)

# Apply a CNOT to each qubit:
for qubit in range(1, 3):

    circuit.cx(0, qubit)

local_simulator = BraketLocalBackend()

with reservation(local_simulator, reservation_arn=None):
    task = local_simulator.run(circuit, shots=1000)


provider = BraketProvider()

sv1 = provider.get_backend("SV1")
# dev = sv1._aws_device


task = sv1.run(circuit, shots=100, reservation_arn="123:123")
# print(task)
# print(task.metadata)


with reservation(sv1, reservation_arn="123:123"):
    task = sv1.run(circuit, shots=1000)
    # doesn't work because the reservation_arn isn't passed correctly
    # sv1._aws_device.run(Circuit().h(0), shots=1)  # correct, reservation_arn is passed correctly
    print(task)
    print(task.metadata)


sv1.run.assert_called_once_with("circuit", 100, reservation_arn=reservation_arn)


# to use SV1
import pennylane as qml

sv1 = qml.device(
    "braket.aws.qubit", device_arn="arn:aws:braket:::device/quantum-simulator/amazon/sv1", wires=2
)

# To use the local sim:
local = qml.device("braket.local.qubit", wires=2)


# to run a circuit:
@qml.qnode(sv1)
def circuit(x):
    qml.RZ(x, wires=0)
    qml.CNOT(wires=[0, 1])
    qml.RY(x, wires=1)
    return qml.expval(qml.PauliZ(1))


with reservation(sv1, reservation_arn="123:123"):

    result = circuit(0.543)
    # sv1.execute.assert_called_once_with(reservation_arn="123:123")
