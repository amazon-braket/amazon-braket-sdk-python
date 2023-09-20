# Variational

```{toctree}

```

  * [**QAOA**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/QAOA/QAOA_braket.ipynb)

    This tutorial shows how to (approximately) solve binary combinatorial optimization problems, using the Quantum Approximate Optimization Algorithm (QAOA). The QAOA algorithm belongs to the class of _hybrid quantum algorithms_ (leveraging classical and quantum computers), which are widely believed to be the working horse for the current NISQ (noisy intermediate-scale quantum) era. In this NISQ era, QAOA is also an emerging approach for benchmarking quantum devices. It is a prime candidate for demonstrating a practical quantum speed-up on near-term NISQ device. To validate our approach, we benchmark our results with exact results as obtained from classical QUBO solvers.

  * [**VQE transverse Ising**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/VQE_Transverse_Ising/VQE_Transverse_Ising_Model.ipynb)

    This tutorial shows how to solve for the ground state of the Transverse Ising Model, which is arguably one of the most prominent, canonical quantum spin systems, using the variational quantum eigenvalue solver (VQE). The VQE algorithm belongs to the class of _hybrid quantum algorithms_ (leveraging classical andquantum computers), which are widely believed to be the working horse for the current NISQ (noisy intermediate-scale quantum) era. To validate our approach, we benchmark our results with exact results as obtained from a Jordan-Wigner transformation.

  * [**VQE chemistry**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/VQE_Chemistry/VQE_chemistry_braket.ipynb)

    This tutorial shows how to implement the Variational Quantum Eigensolver (VQE) algorithm in Amazon Braket SDK to compute the potential energy surface (PES) for the Hydrogen molecule. Specifically, we illustrate the following features of Amazon Braket SDK: `LocalSimulator` which allows one to simulate quantum circuits on their local machine; construction of the ansatz circuit for VQE in Braket SDK; and computing expectation values of the individual terms in the Hamiltonian in Braket SDK.

  * [**Amazon Braket Hybrid Jobs**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/hybrid_jobs)
  
    Examples that illustrate the use of Amazon Braket Hybrid Jobs (Braket Jobs for short).

      * [**When to use Braket Jobs**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/hybrid_jobs/README_hybrid_jobs.md)

      * [**Getting started with Braket Jobs**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/hybrid_jobs/0_Creating_your_first_Hybrid_Job/Creating_your_first_Hybrid_Job.ipynb)

        This notebook provides a demonstration of running a simple Braket Job. You will learn how to create a Braket Job using the Braket SDK or the Braket console, how to set the output S3 folder for a job, and how to retrieve results. You will also learn how to specify the Braket device to run your job on simulators or QPUs. Finally, you will learn how to use local mode to quickly debug your code.

      * [**Quantum machine learning in Braket Jobs**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/hybrid_jobs/1_Quantum_machine_learning_in_Amazon_Braket_Hybrid_Jobs/Quantum_machine_learning_in_Amazon_Braket_Hybrid_Jobs.ipynb)

        This notebook shows a typical quantum machine learning workflow using Braket Jobs. In the process, you will learn how to upload input data, how to set up hyperparameters for your job, and how to retrieve and plot metrics. Finally, you will see how to run multiple Braket Jobs in parallel with different sets of hyperparameters.

      * [**QAOA with Braket Jobs and PennyLane**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/hybrid_jobs/2_Using_PennyLane_with_Braket_Jobs/Using_PennyLane_with_Braket_Jobs.ipynb)

        This notebook shows how to run the QAOA algorithm with PennyLane (similar to a [previous notebook](examples/pennylane/2_Graph_optimization_with_QAOA.ipynb)), but this time using Braket Jobs. In the process, you will learn how to select a container image that supports PennyLane, and how to use checkpoints to save and load training progress of a job.

      * [**Bring your own containers to Braket Jobs**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/hybrid_jobs/3_Bring_your_own_container/bring_your_own_container.ipynb)

        This notebook demonstrates the use of the Bring-Your-Own-Container (BYOC) functionality of Braket Jobs. While Amazon Braket has pre-configured environments which support most use cases of Braket Jobs, BYOC enables you to define fully customizable environments using Docker containers. You will learn how to use BYOC, including preparing a Dockerfile, creating a private Amazon Elastic Container Registry (ECR), building the container, and submitting a Braket Job using the custom container.

      * [**Embedded simulators in Braket Jobs**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/hybrid_jobs/4_Embedded_simulators_in_Braket_Jobs/Embedded_simulators_in_Braket_Jobs.ipynb)

        This notebook introduces embedded simulators in Braket Jobs. An embedded simulator is a local simulator that runs completely within a job instance, i.e., the compute resource that is running your algorithm script. In contrast, [on-demand simulators](https://docs.aws.amazon.com/braket/latest/developerguide/braket-devices.html#braket-simulator-sv1), such as SV1, DM1, or TN1, calculate the results of a quantum circuit on dedicated compute infrastructure on-demand by Amazon Braket. By using embedded simulators, we keep all computations in the same environment. This allows the optimization algorithm to access advanced features supported by the embedded simulator. Furthermore, with the [Bring Your Own Container (BYOC)](https://docs.aws.amazon.com/braket/latest/developerguide/braket-jobs-byoc.html) feature of Jobs, users may choose to use open source simulators or their own proprietary simulation tools.

      * [**Parallelize training for quantum machine learning**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/hybrid_jobs/5_Parallelize_training_for_QML/Parallelize_training_for_QML.ipynb)

        This notebook shows how to use [SageMaker's distributed data parallel library](https://docs.aws.amazon.com/sagemaker/latest/dg/data-parallel.html) in Braket Jobs to accelerate the training of your quantum model. We go through examples to show you how to parallelize trainings across multiple GPUs in an instance, and even multiple GPUs over multiple instances. 

      * [**Benchmarking QN-SPSA optimizer with Braket Jobs and embedded simulators**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/hybrid_jobs/6_QNSPSA_optimizer_with_embedded_simulator/qnspsa_with_embedded_simulator.ipynb)

        This notebook demonstrates how to implement and benchmark the QN-SPSA optimizer, a novel quantum optimization algorithm proposed by Gacon et al. Following this example, we will show how you can use Amazon Braket Hybrid Jobs to iterate faster on variational algorithm research, discuss best practices, and help you scale up your simulations with embedded simulators.

      * [**Running notebooks as hybrid jobs with Amazon Braket**](https://mybinder.org/v2/gh/amazon-braket/amazon-braket-sdk-python.git/feature/read-the-docs?labpath=modules/Continue_Exploring/quantum_algorithms_and_protocols/variational/hybrid_jobs/7_Running_notebooks_as_jobs/Running_notebooks_as_jobs.ipynb)

        This notebook shows how users can run notebooks on different quantum hardware with priority access by using Amazon Braket Hybrid Jobs.
        