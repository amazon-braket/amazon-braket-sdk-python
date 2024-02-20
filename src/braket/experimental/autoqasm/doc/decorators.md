# AutoQASM decorators

AutoQASM function decorators allow us to override the normal behavior of the decorated code. This is how we are able to hook into normal Python control flow statements and add them to the quantum program within our wrapped functions, for instance.

There are a handful of decorators available through AutoQASM. Each one attaches its own special behaviors to the function it wraps. If you are new to AutoQASM, you can just use `@aq.main`! The other decorators unlock further capabilities, when you need it.

## `@aq.main`

This decorator marks the entry point to a quantum program.

You can include gates, pulse control, classical control and subroutine calls. The function wrapped by `@aq.main` is converted into a `Program` object. The `Program` object can be executed on [devices available through Amazon Braket](https://docs.aws.amazon.com/braket/latest/developerguide/braket-devices.html), including local simulators. The code snippet below creates a quantum program with `@aq.main` and runs it on the `Device` instantiated as `device`.

```
size = 5

@aq.main(num_qubits=size)
def ghz_state():
    """Create a GHZ state of the specified size."""
    h(0)
    for i in aq.range(1, size):
        cnot(0, i)
    measure(range(size))

device.run(ghz_state)
```

When you run your quantum program, the Amazon Braket SDK automatically serializes the program to OpenQASM before sending it to the local simulator or the Amazon Braket service. In AutoQASM, you can optionally view the OpenQASM script of your quantum program before submitting to a device by calling `display()` on the `Program` object.

```
ghz_state.display()
```

## `@aq.subroutine`

This decorator declares a function to be a quantum program subroutine.

Like any subroutine, `@aq.subroutine` is often used to simplify repeated code and increase the readability of a program. A subroutine must be called at least once from within an `@aq.main` function or another `@aq.subroutine` function in order to be included in a program.

Because AutoQASM supports strongly-typed serialization formats such as OpenQASM, you must provide type hints for the inputs of your subroutine definitions.

Our example below uses a subroutine to make Bell states on two pairs of qubits.
```
@aq.subroutine
def bell(q0: int, q1: int) -> None:
    h(q0)
    cnot(q0, q1)

@aq.main(num_qubits=4)
def two_bell() -> None:
    bell(0, 1)
    bell(2, 3)
```

Let's take a look at the serialized output from `two_bell.to_ir()`, which shows that the modularity of the subroutine is preserved.

```
OPENQASM 3.0;
def bell(int[32] q0, int[32] q1) {
    h __qubits__[q0];
    cnot __qubits__[q0], __qubits__[q1];
}
qubit[4] __qubits__;
bell(0, 1);
bell(2, 3);
```

## `@aq.gate`

Represents a gate definition.

Gate definitions define higher-level gates in terms of other gates, and are often used to decompose a gate into the native gates of a device.

The body of a gate definition can only contain gates. Qubits used in the body of a gate definition must be passed as input arguments, with the type hint `aq.Qubit`. Like subroutines, a gate definition must be called from within the context of a main quantum program or subroutine in order to be included in the program.

```
@aq.gate
def ch(q0: aq.Qubit, q1: aq.Qubit):
    """Define a controlled-Hadamard gate."""
    ry(q1, -math.pi / 4)
    cz(q0, q1)
    ry(q1, math.pi / 4)
    
@aq.main(num_qubits=2)
def my_program():
    h(0)
    ch(0, 1)
```


## `@aq.gate_calibration`

This decorator allows you to register a calibration for a gate. A gate calibration is a device-specific, low-level, pulse implementation for a logical gate operation.

At the pulse level, qubits are no longer interchangable. Each one has unique properties. Thus, a gate calibration is usually defined for a concrete set of qubits and parameters, but you can use input arguments to your function as well.

The body of a function decorated with `@aq.gate_calibration` must only contain pulse operations.

The first argument to the `@aq.gate_calibration` decorator must be the gate function that the calibration will be registered to. Concrete values for the qubits and parameters are supplied as keyword arguments to the decorator.
Every qubit and angle parameter of the gate being implemented must appear either as an argument to the `@aq.gate_calibration` decorator, or as a parameter of the decorated function.

For example, the gate `rx` takes two arguments, target and angle. Each arguments must be either set in the decorator or declared as an input parameter to the decorated function.

```
# This calibration only applies to physical qubit zero, so we
# mark that in the decorator call
@aq.gate_calibration(implements=rx, target="$0")
def cal_1(angle: float):
    # The calibration is applicable for any rotation angle,
    # so we accept it as an input argument
    pulse.barrier("$0")
    pulse.shift_frequency(q0_rf_frame, -321047.14178613486)
    pulse.play(q0_rf_frame, waveform(angle))
    pulse.shift_frequency(q0_rf_frame, 321047.14178613486)
    pulse.barrier("$0")
```

To add the gate calibration to your program, use the `with_calibrations` method of the main program.

```
@aq.main
def my_program():
    rx("$0", 0.123)
    measure("$0")

my_program.with_calibrations([cal_1])
```
