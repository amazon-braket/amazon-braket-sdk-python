########################################################
Quantum machine learning and optimization with PennyLane
########################################################

Learn more about how to combine PennyLane with Amazon Braket.

.. toctree::
    :maxdepth: 2

**************************************************************************************************************************************************************************
`Combining PennyLane with Amazon Braket <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/pennylane/0_Getting_started/0_Getting_started.ipynb>`_
**************************************************************************************************************************************************************************

  This tutorial shows you how to construct circuits and evaluate their gradients in PennyLane with execution performed using Amazon Braket.

*****************************************************************************************************************************************************************************************************************************************************
`Computing gradients in parallel with PennyLane-Braket <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/pennylane/1_Parallelized_optimization_of_quantum_circuits/1_Parallelized_optimization_of_quantum_circuits.ipynb>`_
*****************************************************************************************************************************************************************************************************************************************************

  In this tutorial, we explore how to speed up training of quantum circuits by using parallel execution on Amazon Braket. We begin by discussing why quantum circuit training involving gradients requires multiple device executions and motivate how the Braket SV1 simulator can be used to overcome this. The tutorial benchmarks SV1 against a local simulator, showing that SV1 outperforms the local simulator for both executions and gradient calculations. This illustrates how parallel capabilities can be combined between PennyLane and SV1.

******************************************************************************************************************************************************************************************
`Graph optimization with QAOA <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/pennylane/2_Graph_optimization_with_QAOA/2_Graph_optimization_with_QAOA.ipynb>`_
******************************************************************************************************************************************************************************************

  In this tutorial we dig deeper into how quantum circuit training can be applied to a problem of practical relevance in graph optimization. We show how easy it is to train a QAOA circuit in PennyLane to solve the maximum clique problem on a simple example graph. The tutorial then extends to a more difficult 20-node graph and uses the parallel capabilities of the Amazon Braket SV1 simulator to speed up gradient calculations and hence train the quantum circuit faster, using around 1-2 minutes per iteration.

******************************************************************************************************************************************************************************************************
`Hydrogen geometry with VQE <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/pennylane/3_Hydrogen_Molecule_geometry_with_VQE/3_Hydrogen_Molecule_geometry_with_VQE.ipynb>`_
******************************************************************************************************************************************************************************************************

  In this tutorial, we see how PennyLane and Amazon Braket can be combined to solve an important problem in quantum chemistry. The ground state energy of molecular hydrogen is calculated by optimizing a VQE circuit using the local Braket simulator. This tutorial highlights how qubit-wise commuting observables can be measured together in PennyLane and Braket, making optimization more efficient.

************************************************************************************************************************************************************************************************************************************************************************************************
`Simulation of Noisy Circuits with PennyLane-Braket <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/pennylane/4_Simulation_of_noisy_quantum_circuits_on_Amazon_Braket_with_PennyLane/4_Simulation_of_noisy_quantum_circuits_on_Amazon_Braket_with_PennyLane.ipynb>`_
************************************************************************************************************************************************************************************************************************************************************************************************

  In this tutorial, we explore the impact of noise on quantum hybrid algorithms and overview of noise simulation on Amazon Braket with PennyLane. The tutorial shows how to use PennyLane to simulate the noisy circuits, on either the local or Braket on-demand noise simulator, and covers the basic concepts of noise channels, using PennyLane to compute cost functions of noisy circuits and optimize them.

***************************************************************************************************************************************************************************
`Tracking Resource Usage <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/pennylane/5_Tracking_resource_usage/5_Tracking_resource_usage.ipynb>`_
***************************************************************************************************************************************************************************

  In this tutorial, we see how to use the PennyLane device tracker feature with Amazon Braket. The PennyLane device resource tracker keeps a record of the usage of a device, such as numbers of circuit evaluations and shots. Amazon Braket extends this information with quantum task IDs and simulator duration to allow further tracking. The device tracker can be combined with additional logic to monitor and limit resource usage on devices.

******************************************************************************************************************************************************************************************
`Adjoint Gradient Computation <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/pennylane/6_Adjoint_gradient_computation/6_Adjoint_gradient_computation.ipynb>`_
******************************************************************************************************************************************************************************************

  In this tutorial, we will show you how to compute gradients of free parameters in a quantum circuit using PennyLane and Amazon Braket. Adjoint differentiation is a technique used to compute gradients of parametrized quantum circuits. It can be used when shots=0 and is available on Amazon Braket’s on-demand state vector simulator, SV1. The adjoint differentiation method allows you to compute the gradient of a circuit with P parameters in only 1+1 circuit executions (one forward and one backward pass, similar to backpropagation), as opposed to the parameter-shift or finite-difference methods, both of which require 2P circuit executions for every gradient calculation. The adjoint method can lower the cost of running variational quantum workflows, especially for circuits with a large number of parameters.

