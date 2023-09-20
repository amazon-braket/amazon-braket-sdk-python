# Compilation

```{toctree}

```

This notebook collection shows how to run your circuits on Braket devices exactly as defined without any modification during the compilation process, a feature known as verbatim compilation. Usually, when you run a circuit on a QPU, behind the scenes, Amazon Braket will do a series of compilation steps to optimize your circuit and map the abstract circuit to the physical qubits on the QPU. However, in many situations, such as for error mitigation or benchmarking experiments, researchers require full control of the qubits and the gates that are being applied, thereby motivating the use of verbatim compilation.
    
OpenQASM, a popular human-readable and hardware-agnostic quantum circuit description language currently supported as an *Intermediate Representation* (IR) on Amazon Braket, is also introduced. The associated tutorials show how to submit OpenQASM tasks to various devices on Braket and introduce some OpenQASM features available on Braket. In addition, verbatim compilation can be performed with OpenQASM by specifying a verbatim pragma around a box of code.

  * [**Getting Started with OpenQASM on Braket**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-examples.git/feature/reorganized-examples?labpath=modules/Continue_Exploring/quantum_hardware/compilation/Getting_Started_with_OpenQASM_on_Braket.ipynb) 

  * [**Simulating advanced OpenQASM programs with the local simulator**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-examples.git/feature/reorganized-examples?labpath=modules/Continue_Exploring/quantum_hardware/compilation/Simulating_Advanced_OpenQASM_Programs_with_the_Local_Simulator.ipynb)

  * [**Verbatim compilation**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-examples.git/feature/reorganized-examples?labpath=modules/Continue_Exploring/quantum_hardware/compilation/Verbatim_Compilation.ipynb)
