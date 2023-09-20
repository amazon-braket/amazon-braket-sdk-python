# Quantum machine learning and optimization with PennyLane

```{toctree}

```

  * [**Combining PennyLane with Amazon Braket**](https://mybinder.org/v2/gh/benhong-amzn/amazon-braket-examples.git/pure_reorg?labpath=modules/Continue_Exploring/quantum_frameworks_and_plugins/pennylane/0_Getting_started/0_Getting_started.ipynb)

    This tutorial shows you how to construct circuits and evaluate their gradients in PennyLane with execution performed using Amazon Braket.

  * [**Computing gradients in parallel with PennyLane-Braket**](https://mybinder.org/v2/gh/benhong-amzn/amazon-braket-examples.git/pure_reorg?labpath=modules/Continue_Exploring/quantum_frameworks_and_plugins/pennylane/1_Parallelized_optimization_of_quantum_circuits/1_Parallelized_optimization_of_quantum_circuits.ipynb)

    This tutorial explores how to speed up training of quantum circuits by using parallel execution on Amazon Braket. We begin by discussing why quantum circuit training involving gradients requires multiple device executions and motivate how the Braket SV1 simulator can be used to overcome this. The tutorial benchmarks SV1 against a local simulator, showing that SV1 outperforms the local simulator for both executions and gradient calculations. This illustrates how parallel capabilities can be combined between PennyLane and SV1.

  * [**Graph optimization with QAOA**](https://mybinder.org/v2/gh/benhong-amzn/amazon-braket-examples.git/pure_reorg?labpath=modules/Continue_Exploring/quantum_frameworks_and_plugins/pennylane/2_Graph_optimization_with_QAOA/2_Graph_optimization_with_QAOA.ipynb)

    This tutorial digs deeper into how quantum circuit training can be applied to a problem of practical relevance in graph optimization. We show how easy it is to train a QAOA circuit in PennyLane to solve the maximum clique problem on a simple example graph. The tutorial then extends to a more difficult 20-node graph and uses the parallel capabilities of the Amazon Braket SV1 simulator to speed up gradient calculations and hence train the quantum circuit faster, using around 1-2 minutes per iteration.

  * [**Hydrogen geometry with VQE**](https://mybinder.org/v2/gh/benhong-amzn/amazon-braket-examples.git/pure_reorg?labpath=modules/Continue_Exploring/quantum_frameworks_and_plugins/pennylane/3_Hydrogen_Molecule_geometry_with_VQE/3_Hydrogen_Molecule_geometry_with_VQE.ipynb)

    This tutorial shows how PennyLane and Amazon Braket can be combined to solve an important problem in quantum chemistry. The ground state energy of molecular hydrogen is calculated by optimizing a VQE circuit using the local Braket simulator. This tutorial highlights how qubit-wise commuting observables can be measured together in PennyLane and Braket, making optimization more efficient.

  * [**Simulation of noisy quantum circuits on Amazon Braket with PennyLane**](https://mybinder.org/v2/gh/benhong-amzn/amazon-braket-examples.git/pure_reorg?labpath=modules/Continue_Exploring/quantum_frameworks_and_plugins/pennylane/4_Simulation_of_noisy_quantum_circuits_on_Amazon_Braket_with_PennyLane/4_Simulation_of_noisy_quantum_circuits_on_Amazon_Braket_with_PennyLane.ipynb)

    This tutorial explores the impact of noise on quantum hybrid algorithms. We will take QAOA as an example to benchmark performance in the presence of noise. Additionally, the tutorial gives an overview of noise simulation on Amazon Braket with PennyLane, such that the user will be able to use PennyLane to simulate the noisy circuits, on either the local or Braket on-demand noise simulator. In particular, the notebook covers the basic concepts of noise channels and uses PennyLane to compute cost functions of noisy circuits and optimize them. 

  * [**Tracking Resource Usage with PennyLane Device Tracker**](https://mybinder.org/v2/gh/benhong-amzn/amazon-braket-examples.git/pure_reorg?labpath=modules/Continue_Exploring/quantum_frameworks_and_plugins/pennylane/5_Tracking_resource_usage/5_Tracking_resource_usage.ipynb)

    This tutorial shows how to use the PennyLane device tracker feature with Amazon Braket. Computing gradients of quantum circuits involves multiple devices executions, which can lead to a large number of executions when optimizing quantum circuits. So to help users keep track of their usage, Amazon Braket works with PennyLane to record and make available useful information during the computation. The PennyLane device resource tracker keeps a record of the usage of a device, such as numbers of circuit evaluations and shots. Amazon Braket extends this information with task IDs and simulator duration to allow further tracking. The device tracker can be combined with additional logic to monitor and limit resource usage on devices.

  * [**Adjoint gradient computation with PennyLane and Amazon Braket**](https://mybinder.org/v2/gh/benhong-amzn/amazon-braket-examples.git/pure_reorg?labpath=modules/Continue_Exploring/quantum_frameworks_and_plugins/pennylane/6_Adjoint_gradient_computation/6_Adjoint_gradient_computation.ipynb)

    This tutorial shows how to compute gradients of free parameters in a quantum circuit using PennyLane and Amazon Braket.
    