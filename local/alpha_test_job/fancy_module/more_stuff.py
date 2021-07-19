# You could define some more methods here

import boto3

from braket.annealing import Problem, ProblemType
from braket.aws import AwsDevice
from braket.circuits import Circuit

# Change this

shots = 100

# Enable debug logging for boto3 to see raw request and response
boto3.set_stream_logger(name="botocore")
s3_folder = ("amazon-braket-318845237731", "testJobs")


def solve_circuit():
    bell = Circuit().h(0).cnot(0, 1)
    print(bell.diagram())
    device = AwsDevice("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
    task = device.run(bell, s3_folder, shots=shots)
    return task


def solve_annealing_problem():
    problem = Problem(
        ProblemType.ISING,
        linear={1: 3.14},
        quadratic={(0, 4): 10.08},
    )
    device = AwsDevice("arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6")
    task = device.run(
        problem,
        s3_folder,
        device_parameters={"providerLevelParameters": {"postprocessingType": "SAMPLING"}},
    )
    return task


def run():
    task = solve_circuit()
    # task = solve_annealing_problem()
    print(f"Created task: {task.metadata()}")
    print(f"Task result: {task.result()}")
