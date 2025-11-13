from braket.aws import AwsDevice
from braket.circuits import Circuit
from braket.program_sets import ProgramSet

emerald = AwsDevice("arn:aws:braket:eu-north-1::device/qpu/iqm/Emerald")

emu = emerald.emulator()

circ = Circuit().add_verbatim_box(Circuit().prx(2, 0.001, 0.001)).measure(2)

ps = ProgramSet([circ], shots_per_executable=100)


res = emu.run(ps, shots=100).result()
print(res)
for circ in ps:
    print(emu.transform(circ))
    print(emu.run(circ, shots=100).result())
