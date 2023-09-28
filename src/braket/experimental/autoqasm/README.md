# AutoQASM

**AutoQASM is not an officially supported AWS product.**

This experimental module offers a new quantum-imperative programming experience embedded in Python
for developing quantum programs.

All of the code in the `experimental` module is _experimental_ software. We may change, remove, or
deprecate parts of the AutoQASM API without notice. The name AutoQASM is a working title and is
also subject to change.

For a fully supported quantum developer experience,
please continue to use the rest of the Amazon Braket Python SDK by following
[these instructions](https://github.com/aws/amazon-braket-sdk-python#installing-the-amazon-braket-python-sdk).
If you are interested in our active development efforts, and you are not
afraid of a few bugs, please keep on reading!

## Why AutoQASM?

AutoQASM provides a Pythonic developer experience for writing quantum programs. The working title "AutoQASM" is derived from the name of the [AutoGraph module of TensorFlow](https://www.tensorflow.org/api_docs/python/tf/autograph). AutoQASM uses AutoGraph to construct quantum assembly (QASM) programs rather than TensorFlow graphs.

AutoQASM provides a natural interface for expressing quantum programs with mid-circuit measurements
and classical control flow using native Python language features. It allows the construction of
modular programs consisting of common programming constructs such as loops and subroutines. This
enables a more imperative programming style than constructing programs via a series of function calls
on a circuit object.

AutoQASM programs can be serialized to OpenQASM. This textual representation for quantum programs is widely supported and enables interoperability among various frameworks. A crucial part of our serialization process is that modular structures within the program, such as loops and subroutines, are preserved when serializing to OpenQASM.

Although it is still a work in progress, the intent is that AutoQASM will support any quantum programming paradigm which falls into the [OpenQASM 3.0](https://openqasm.com) language scope. AutoQASM supports serializing quantum programs to OpenQASM, which allows the programs to interoperate with any library or service that supports OpenQASM programs, such as Amazon Braket.

See the [Quick Start](#quick-start) section below, as well as the AutoQASM [example notebooks](../../../../examples/autoqasm), for examples of AutoQASM usage.


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
from braket.experimental.autoqasm.instructions import h, cnot, measure
```

To create a quantum program using the AutoQASM experience, you decorate a function with `@aq.main`.
This allows AutoQASM to hook into the program definition and generate an output format that is accepted
by quantum devices.

For instance, we can create a Bell state like so:
```
# A program that generates a maximally entangled state
@aq.main
def bell_state() -> None:
    h(0)
    cnot(0, 1)
```

You can view the output format, which is OpenQASM, by running `bell_state().to_ir()`.

AutoQASM enables users to use more complicated program constructs with a compact and readable
structure. We can demonstrate this with a program that conditionally prepares multiple Bell states
on qubit pairs (1, 2) and (3, 4).
```
@aq.main(num_qubits=5)
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

AutoQASM can support subroutines and complex control flow. You can use the Python runtime
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
written as a Python function which is decorated with `@aq.main`. When calling this
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

To run only AutoQASM tests (and skip the rest of the Amazon Braket SDK unit tests), run:
```
tox -e unit-tests -- test/unit_test/braket/experimental/autoqasm
```

Note that you may first need to run `pip install -e .[test]`. More information on running tests
can be found in the [top-level README](../../../../README.md).

## Frequently asked questions

###  1. Will AutoQASM be extended to contain a library of quantum algorithms or quantum applications?

No, we are focused on AutoQASM as an interface for low-level expression of
quantum programs: circuits, gates and pulses. Higher-level algorithm
libraries could be implemented using AutoQASM and benefit from modular
AutoQASM functionality such as subroutines.

### 2. What is the relationship between AutoQASM and OpenQASM?

AutoQASM can be seen as implementing a builder pattern for OpenQASM. It
allows you serialize your program to OpenQASM with `Program.to_ir()`. The
interface is not strongly tied to OpenQASM so we could serialize to other
formats in the future.

In other words, AutoQASM is a quantum programming interface built in Python.
OpenQASM is a quantum assembly language, often used as a serialization format
for quantum programming frameworks and quantum hardware providers. We can
represent a quantum program equivalently in either format, but using AutoQASM
allows one to also make use of Python, including the Amazon Braket SDK.

### 3. What is the relationship between AutoQASM and the Amazon Braket SDK?

AutoQASM lives alongside the Amazon Braket SDK as an experimental feature
branch. It supplements the program building experience and integrates with
Amazon Braket SDK features. For instance, one can build a program through
AutoQASM, and then use the SDK to run the program on a local simulator or on
an Amazon Braket device.

Quantum programs are serialized to OpenQASM before executing on Amazon
Braket, and AutoQASM programs can be serialized to OpenQASM. Thus, we have a
very lightweight integration to run AutoQASM programs through the Amazon
Braket SDK.

### 4. Does AutoQASM support other providers beyond Amazon Braket?

Yes. AutoQASM serializes to OpenQASM, and so it is applicable to any library
or QPU that supports OpenQASM. We do have features that use the Amazon Braket
SDK, such as [device-specific validation](../../../../examples/autoqasm/4_Native_programming.ipynb).
Because AutoQASM is open-source, anyone could
build similar integrations for another service. Reach out if you're
interested in doing this and would like support.


### 5. Does AutoQASM offer special support for device-specific programming?

Yes, AutoQASM has device-specific validation to support native programming.
We plan to expand this functionality in the future. Learn more with our
[native programming example notebook](../../../../examples/autoqasm/4_Native_programming.ipynb).

### 6. Do the devices available through Amazon Braket support all of AutoQASM's features?

No, for example, the `reset` instruction is not supported by all devices. In
general, different QPUs and QHPs support different sets of features, so
AutoQASM will often support features that a particular device doesn't
support. We intend that AutoQASM will eventually be able to generate any
program representable by OpenQASM 3.0, with additional Python-side features
such as validation and visualization.

### 7. Is there a difference between classical conditionals and quantum conditionals?

Yes. This is best demonstrated through examples.

Below, we have a classical conditional statement that will execute on the
control system of a quantum computer. A measurement occurs, and additional
statements execute if the measurement returns `1`.
```
if measure(qubit0):
   ...
```

Because AutoQASM is integrated with Python, we can also use client-side
control flow to conditionally build our program. The statement is evaluated
as soon as you run your code.

```
if device.num_qubits < 10:
    ...
```

Quantum conditionals are more often referred to as _controlled gates_. The
quintessential example is the `CNOT` gate, the controlled-NOT. It can be
understood as a gate that flips a second qubit (target) when the input qubit
(control) is in the `|1>` state.

```
cnot(control_qubit, target_qubit)
```
