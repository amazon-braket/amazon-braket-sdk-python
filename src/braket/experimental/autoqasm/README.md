# AutoQASM

**AutoQASM is not an officially supported AWS product.**

This experimental module offers a new quantum-imperative programming experience embedded in Python
for developing quantum programs.

All of the code in the `experimental` module is _experimental_ software. We may change, remove, or
deprecate parts of the AutoQASM API without notice. The name AutoQASM is a working title and is
also subject to change. The name is inspired by the
[AutoGraph module of TensorFlow](https://www.tensorflow.org/api_docs/python/tf/autograph),
which we have used as a foundation for this project.

For a fully supported quantum developer experience,
please continue to use the rest of the Amazon Braket Python SDK by following
[these instructions](https://github.com/aws/amazon-braket-sdk-python#installing-the-amazon-braket-python-sdk).
If you are interested in our active development efforts, and you are not
afraid of a few bugs, please keep on reading!

## Installation

AutoQASM is an experimental module and is not yet part of the released Amazon Braket SDK.
To use AutoQASM, you'll need to install directly from the `feature/autoqasm` branch:
```
git clone https://github.com/aws/amazon-braket-sdk-python.git
cd amazon-braket-sdk-python
git checkout feature/autoqasm
pip install -e .
```

## Quick start

In this section, we will show how to get started with AutoQASM. AutoQASM allows you to build
quantum programs with a simplified syntax and run the programs on the service. It uses the circuit
model programming paradigm that is also used in the Amazon Braket SDK.

First, import the following modules and functions:
```
import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.gates import h, cnot, measure
```

To create a quantum program using the AutoQASM experience, you decorate a function with `@aq.function`.
This allows AutoQASM to hook into the program definition and generate an output format that is accepted
by quantum devices.

For instance, we can create a Bell state like so:
```
# A program that generates a maximally entangled state
@aq.function
def bell_state() -> None:
    h(0)
    cnot(0, 1)
```

You can view the output format, which is OpenQASM, by running `bell_state().to_ir()`.

AutoQASM enables users to use more complicated program constructs with a compact and readable
structure. We can demonstrate this with a program that conditionally prepares multiple Bell states
on qubit pairs (1, 2) and (3, 4).
```
@aq.function(num_qubits=5)
def conditional_multi_bell_states() -> None:
    h(0)
    if measure(0):
        for i in aq.range(2):
            qubit = 2 * i + 1
            h(qubit)
            cnot(qubit, qubit+1)

    measure([0,1,2,3,4])

my_bell_program = conditional_multi_bell_states()
```

AutoQASM can support nested subroutines and complex control flow. You can use the Python runtime
and quantum runtime side-by-side. For the moment, we support only a few quantum operations such as
`h`, `x`, `cnot`, and `measure`. There are rough edges at the moment, but we're actively smoothing
them out!

The Amazon Braket local simulator supports AutoQASM programs as input.
Let's simulate the `my_bell_program`:

```
from braket.devices.local_simulator import LocalSimulator

device = LocalSimulator()
task = device.run(my_bell_program, shots=100)
result = task.result()
```

For more example usage of AutoQASM, visit the [example notebooks](../../../../examples/autoqasm).

## Architecture

AutoQASM is built on top of the `autograph` component of TensorFlow. A quantum program is
written as a Python function which includes an `@aq.function` decorator. When calling this
decorated function, the user’s Python function is converted into a transformed Python function
by `autograph`. This transformed function is then executed to produce an AutoQASM `Program`
object which can be simulated and/or serialized to OpenQASM.

The conversion process allows AutoQASM to provide custom handling for native Python control
flow keywords such as `if`, `for`, and `while` and to preserve this control flow in the resulting
quantum program in order to realize functionality such as classical feedback on mid-circuit
measurement, efficient representation of loops, and modularity of subroutine definitions.

## Plans

The AutoQASM project is undergoing rapid development.
The current status and future plans are tracked in
the [AutoQASM GitHub project](https://github.com/orgs/amazon-braket/projects/2/).

## Contributing and sharing feedback

We welcome feature requests, bug reports, or
general feedback, which you can share with us by
[opening up an issue](https://github.com/aws/amazon-braket-sdk-python/issues/new/choose). We also
welcome pull requests, examples, and documentation -- please open an issue describing your work
when you get started, or comment on an existing issue with your intentions. Pull requests should be
targeted to the feature/autoqasm branch of the https://github.com/aws/amazon-braket-sdk-python
repository. For more details on contributing to the Amazon Braket SDK, please read the
[contributing guidelines](../../../../CONTRIBUTING.md).

For questions, you can get help via the Quantum Technologies section of
[AWS RePost](https://repost.aws/topics/TAxin6L9GYR5a3NElq8AHIqQ/quantum-technologies).
Please tag your question with "Amazon Braket" and mention AutoQASM in the question title.

## Tests

To run only AutoQASM tests (and skip the rest of the unit tests), run:
```
tox -e unit-tests -- test/unit_test/braket/experimental/autoqasm
```

Note that you may first need to run `pip install -e .[test]`. More information on running tests
can be found in the [top-level README](../../../../README.md).
