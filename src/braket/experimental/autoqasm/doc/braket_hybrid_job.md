# AutoQASM with Amazon Braket Hybrid Job

Amazon Braket Hybrid Jobs provides a solution for executing hybrid quantum-classical algorithms that utilize both classical computing resources and Quantum Processing Units (QPUs). This service efficiently manages the allocation of classical compute resources, executing your algorithm, and then freeing up those resources upon completion, ensuring cost-effectiveness by charging only for the resources used. It's perfectly suited for iterative algorithms that span lengthy durations and require the integration of classical and quantum computing.

## Using `AwsQuantumJob.create`

This [documentation page](https://docs.aws.amazon.com/braket/latest/developerguide/braket-jobs-first.html#braket-jobs-first-create) show you how to create a hybrid job with `AwsQuantumJob.create`. To use hybrid job with AutoQASM, simply use AutoQASM in your algorithm script. Because AutoQASM is currently not installed in the default job container, be sure to include the AutoQASM feature branch in the requirements.txt of your source module, or add AutoQASM as a dependency when you build your own container. Below is an example algorithm script to get you started.
```
import os

from braket.devices import LocalSimulator
from braket.circuits import Circuit
import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.instructions import measure, h, cnot

def start_here():
    print("Test job started!")

    # Use the device declared in the job script
    device = LocalSimulator()

    @aq.main
    def bell():
        h(0)
        cnot(0, 1)
        c = measure([0, 1])

    for count in range(5):
        task = device.run(bell, shots=100)
        print(task.result().measurements)

    print("Test job completed!")
```
Save this algorithm script as "algorithm_script.py" and run this code snippet below to create your first hybrid job with AutoQASM!
```
from braket.aws import AwsQuantumJob

job = AwsQuantumJob.create(
    device="local:braket_simulator",
    source_module="algorithm_script.py",
    entry_point="algorithm_script:start_here",
    wait_until_complete=True
)
```

## Using `hybrid_job` decorator

Alternatively, you can also use the `hybrid_job` decorator to create a hybrid job with AutoQASM. Because AutoQASM is currently not installed in the default job container, be sure to include the AutoQASM feature branch in the `dependencies` keyword of the `hybrid_job` decorator, or add AutoQASM as a dependency when you build your own container. 

One of the core mechanisms of AutoQASM is source code analysis. When calling AutoQASM decorated function, the source code of the function is analyzed and converted into a transformed Python function by autograph. Under the `hybrid_job` decorator, the access to source code is limited. The source code of the function defined inside the `hybrid_job` decorated function is separately saved as an input data to the job. When [AutoQASM decorators](decorators.md) wraps these functions, it will retrieve the source code from the separately saved input data. If you wrap AutoQASM decorator over functions that are defined outside of the `hybrid_job` decorated function, it may not work properly. When your application requires functions to be defined outside of `hybrid_job` decorated function, we recommend you to use the option described in "Using `AwsQuantumJob.create`" to create the hybrid job. 

Below is a working example to create an AutoQASM job with `hybrid_job` decorator.
```
from braket.jobs import hybrid_job
from braket.devices import LocalSimulator
import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.instructions import measure, h, cnot

@hybrid_job(
    device="local:braket_simulator",
    dependencies=["git+https://github.com/amazon-braket/amazon-braket-sdk-python.git@feature/autoqasm#egg=amazon-braket-sdk"],
) 
def bell_circuit_job():
    device = LocalSimulator()

    @aq.main
    def bell():
        h(0)
        cnot(0, 1)
        c = measure([0, 1])

    for count in range(5):
        task = device.run(bell, shots=100)
        print(task.result().measurements)

bell_circuit_job()

```
