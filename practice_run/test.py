from braket.aws import AwsDevice
from braket.circuits import Circuit
from braket.circuits.serialization import IRType

circuit = Circuit().y(0)
print(f"{circuit.to_ir(ir_type=IRType.OPENQASM).source}")

d = AwsDevice("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
task = d.run(circuit.to_ir(ir_type=IRType.OPENQASM), shots=10)
print(f"{task.id}")
res = task.result()
print(res)
