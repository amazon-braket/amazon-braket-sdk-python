# Getting started

```{toctree}

```

  * [**Getting started with Amazon Braket**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Getting_Started/0_Getting_started/0_Getting_started.ipynb)

    A hello-world tutorial that shows you how to build a simple circuit and run it on a local simulator.

  * [**Running quantum circuits on simulators**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Getting_Started/1_Running_quantum_circuits_on_simulators/1_Running_quantum_circuits_on_simulators.ipynb)

    This tutorial prepares a paradigmatic example for a multi-qubit entangled state, the so-called GHZ state (named after the three physicists Greenberger, Horne, and Zeilinger). The GHZ state is extremely non-classical, and therefore very sensitive to decoherence. For this reason, it is often used as a performance benchmark for today's hardware. Moreover, in many quantum information protocols it is used as a resource for quantum error correction, quantum communication, and quantum metrology.

  * [**Running quantum circuits on QPU devices**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Getting_Started/2_Running_quantum_circuits_on_QPU_devices/2_Running_quantum_circuits_on_QPU_devices.ipynb)

    This tutorial prepares a maximally-entangled Bell state between two qubits, for classical simulators and for QPUs. For classical devices, we can run the circuit on a local simulator or a cloud-based on-demand simulator. For the quantum devices, we run the circuit on the superconducting machine from Rigetti, and on the ion-trap machine provided by IonQ. As shown, one can swap between different devices seamlessly, without any modifications to the circuit definition, by re-defining the device object. We also show how to recover results using the unique Amazon resource identifier (ARN) associated with every task. This tool is useful if you must deal with potential delays, which can occur if your quantum task sits in the queue awaiting execution.  

  * [**Deep dive into the anatomy of quantum circuits**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Getting_Started/3_Deep_dive_into_the_anatomy_of_quantum_circuits/3_Deep_dive_into_the_anatomy_of_quantum_circuits.ipynb)

    This tutorial discusses in detail the anatomy of quantum circuits in the Amazon Braket SDK. Specifically, you'll learn how to build (parameterized) circuits and display them graphically, and how to append circuits to each other. We discuss the associated circuit depth and circuit size. Finally we show how to execute the circuit on a device of our choice (defining a quantum task). We then learn how to track, log, recover, or cancel such a _quantum task_ efficiently.

  * [**Getting devices and checking device properties**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Getting_Started/4_Getting_Devices_and_Checking_Device_Properties/4_Getting_Devices_and_Checking_Device_Properties.ipynb)

    This tutorial shows how to interact with the Amazon Braket GetDevice API to retrieve Amazon Braket devices (such as simulators and QPUs) programmatically, and how to gain access to their properties.
    