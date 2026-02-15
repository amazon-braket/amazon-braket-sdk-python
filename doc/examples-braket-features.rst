################################
Amazon Braket features
################################

Learn more about the indivudal features of Amazon Braket.

.. toctree::
    :maxdepth: 2

*************************************************************************************************************************************************************************************
`Getting Started with OpenQASM on Braket <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Getting_Started_with_OpenQASM_on_Braket.ipynb>`_
*************************************************************************************************************************************************************************************

  This tutorial demonstrates how to submit OpenQASM quantum tasks to various devices on Braket and introduce some OpenQASM features available on Braket. OpenQASM is a popular, open source, human-readable and hardware-agnostic quantum circuit description language.

*****************************************************************************************************************************************************************************************************************************************************************
`Getting notifications when a quantum task completes <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Getting_notifications_when_a_quantum_task_completes/Getting_notifications_when_a_quantum_task_completes.ipynb>`_
*****************************************************************************************************************************************************************************************************************************************************************

  This tutorial illustrates how Amazon Braket integrates with Amazon EventBridge for event-based processing. In the tutorial, you will learn how to configure Amazon Braket and Amazon Eventbridge to receive text notification about quantum task completions on your phone. Of course, EventBridge also allows you to build full, event-driven applications based on events emitted by Amazon Braket.

*************************************************************************************************************************************************************************
`Adjoint Gradient Result Type <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Using_The_Adjoint_Gradient_Result_Type.ipynb>`_
*************************************************************************************************************************************************************************

  This tutorial introduces the AdjointGradient result type, discusses what a gradient is and how to compute one on a quantum circuit, explains how they can be used to accelerate your workflows, and shows an example of gradients in action on a hybrid quantum algorithm.

***********************************************************************************************************************************************
`Verbatim Compilation <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Verbatim_Compilation.ipynb>`_
***********************************************************************************************************************************************

  This tutorial explains how to use _verbatim compilation_ to run your circuits exactly as defined without any modification during the compilation process that's usually done behind-the-scenes when you run your circuits.

*************************************************************************************************************************************************************************************************************************
`Advanced OpenQASM programs using the Local Simulator <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Simulating_Advanced_OpenQASM_Programs_with_the_Local_Simulator.ipynb>`_
*************************************************************************************************************************************************************************************************************************

  This notebook serves as a reference of OpenQASM features supported by Braket with the LocalSimulator.

***********************************************************************************************************************************************************************************
`Using the experimental local simulator <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Using_the_experimental_local_simulator.ipynb>`_
***********************************************************************************************************************************************************************************

  This tutorial serves as an introduction to the experimental v2 local simulator for Amazon Braket. This tutorial explains how to use the v2 local simulator and the performance difference you can expect to see.

***********************************************************************************************************************************************************************************
`Using the tensor network simulator TN1 <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Using_the_tensor_network_simulator_TN1.ipynb>`_
***********************************************************************************************************************************************************************************

  This notebook introduces the Amazon Braket on-demand tensor network simulator, TN1. You will learn about how TN1 works, how to use it, and which problems are best suited to run on TN1.

**********************************************************************************************************************************************************************************
`TN1 and Hayden-Preskill circuits <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/TN1_demo_local_vs_non-local_random_circuits.ipynb>`_
**********************************************************************************************************************************************************************************

  This tutorial dives into showing the degree to which the tensor network simulator is capable of detecting a hidden local structure in a quantum circuit by working with Hayden-Preskill circuits, which are a class of unstructured, random quantum circuits.

*************************************************************************************************************************************************************************
`Simulating noise on Amazon Braket <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Simulating_Noise_On_Amazon_Braket.ipynb>`_
*************************************************************************************************************************************************************************

  This notebook provides a detailed overview of noise simulation on Amazon Braket. You will learn how to define noise channels, apply noise to new or existing circuits, and run those circuits on the Amazon Braket noise simulators.

****************************************************************************************************************************************************************
`Error Mitigation on IonQ <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Error_Mitigation_on_Amazon_Braket.ipynb>`_
****************************************************************************************************************************************************************

  This tutorial explains how to get started with using error mitigation on IonQ’s Aria QPU. You’ll learn how Aria’s two built-in error mitigation techniques work, how to switch between them, and the performance difference you can expect to see with and without these techniques for some problems.

******************************************************************************************************************************************************************************
`Noise Models on Amazon Braket <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Noise_models/Noise_models_on_Amazon_Braket.ipynb>`_
******************************************************************************************************************************************************************************

  This tutorial shows how to create noise models containing different types of noise and instructions for how to apply the noise to a circuit. A noise model encapsulates the assumptions on quantum noise channels and how they act on a given circuit. Simulating this noisy circuit gives information about much the noise impacts the results of the quantum computation. By incrementally adjusting the noise model, the impact of noise can be understood on a variety of quantum algorithms.

*****************************************************************************************************************************************************
`IQM Garnet Native Gates <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/IQM_Garnet_Native_Gates.ipynb>`_
*****************************************************************************************************************************************************

  This tutorial explores the functionality of the native gates of IQM Garnet.

*****************************************************************************************************************************************
`IonQ Native Gates <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/IonQ_Native_Gates.ipynb>`_
*****************************************************************************************************************************************

  This tutorial goes into details of IonQ’s native gates and their functionalities, enabling us to realize direct control over the quantum operations on the computer without compiler optimizations or error mitigation. It will discuss the native gates available on IonQ, their mathematical representations, and how they can be used for applications such as the quantum Fourier transform (QFT).

***********************************************************************************************************************************************************************
`Allocating Qubits on QPU Devices <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Allocating_Qubits_on_QPU_Devices.ipynb>`_
***********************************************************************************************************************************************************************

  This tutorial explains how you can use the Amazon Braket SDK to allocate the qubit selection for your circuits manually, when running on QPUs.

***************************************************************************************************************************************************************************************************
`Getting Devices and Checking Device Properties <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Getting_Devices_and_Checking_Device_Properties.ipynb>`_
***************************************************************************************************************************************************************************************************

  This example shows how to interact with the Amazon Braket GetDevice API to retrieve Amazon Braket devices (such as simulators and QPUs) programmatically, and how to gain access to their properties.

*******************************************************************************************************************************************************************************************************
`Getting started with Amazon Braket program sets <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/program_sets/01_Getting_started_with_program_sets.ipynb>`_
*******************************************************************************************************************************************************************************************************

  Amazon Braket's program sets feature enables efficient batch processing of quantum computations by allowing multiple quantum circuits to be executed together. The feature provides various ways to combine circuits, parameters, and observables through methods like `CircuitBinding`, `product()`, and `zip()`, making it particularly useful for variational algorithms and parameter sweeps. Program sets can significantly reduce overhead and costs compared to running individual quantum tasks, while maintaining the same computational results.

*********************************************************************************************************************************************************************************************************
`Using the local emulator <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Device_emulation/01_Local_Emulation_for_Verbatim_Circuits_on_Amazon_Braket.ipynb>`_
*********************************************************************************************************************************************************************************************************

  This tutorial serves as an introduction to the local emulator for validating and debugging verbatim circuits for gate-based devices. This tutorial explains how to instantiate local emulator from up-to-date device calibration data and customize it for emulating verbatim circuits locally.

********************************************************************************************************************************************************************************
`Introduction to Amazon Braket spending limits <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/braket_features/Spending_Limits_Introduction.ipynb>`_
********************************************************************************************************************************************************************************

  Amazon Braket spending limits allow for setting optional budget caps on individual QPUs that automatically validate and reject tasks exceeding the configured spending threshold.

