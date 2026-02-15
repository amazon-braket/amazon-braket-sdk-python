################################
Amazon Braket Hybrid Jobs
################################

Learn more about hybrid jobs on Amazon Braket.

.. toctree::
    :maxdepth: 2

******************************************************************************************************************************************************************************************************************
`Getting started with Amazon Braket Hybrid Jobs <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/hybrid_jobs/0_Creating_your_first_Hybrid_Job/0_Creating_your_first_Hybrid_Job.ipynb>`_
******************************************************************************************************************************************************************************************************************

  This notebook provides a demonstration of running a simple Braket Hybrid Job. You will learn how to create a Braket Hybrid Job using the Braket SDK or the Braket console, how to set the output S3 folder for a hybrid job, and how to retrieve results. You will also learn how to specify the Braket device to run your hybrid job on simulators or QPUs. Finally, you will learn how to use local mode to quickly debug your code.

*********************************************************************************************************************************************************************************************************************************************************************
`Quantum machine learning in Amazon Braket Hybrid Jobs <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/hybrid_jobs/1_Quantum_machine_learning_in_Amazon_Braket_Hybrid_Jobs/Quantum_machine_learning_in_Amazon_Braket_Hybrid_Jobs.ipynb>`_
*********************************************************************************************************************************************************************************************************************************************************************

  This notebook shows a typical quantum machine learning workflow using Braket Hybrid Jobs. In the process, you will learn how to upload input data, how to set up hyperparameters for your hybrid job, and how to retrieve and plot metrics. Finally, you will see how to run multiple Braket Hybrid Jobs in parallel with different sets of hyperparameters.

*************************************************************************************************************************************************************************************************************************************
`QAOA with Amazon Braket Hybrid Jobs and PennyLane <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/hybrid_jobs/2_Using_PennyLane_with_Braket_Hybrid_Jobs/Using_PennyLane_with_Braket_Hybrid_Jobs.ipynb>`_
*************************************************************************************************************************************************************************************************************************************

  This notebook shows how to run the QAOA algorithm with PennyLane (similar to a [previous notebook](examples/pennylane/2_Graph_optimization_with_QAOA/2_Graph_optimization_with_QAOA.ipynb)), but this time using Braket Hybrid Jobs. In the process, you will learn how to select a container image that supports PennyLane, and how to use checkpoints to save and load training progress of a hybrid job.

*****************************************************************************************************************************************************************************************************
`Bring your own containers to Braket Hybrid Jobs <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/hybrid_jobs/3_Bring_your_own_container/bring_your_own_container.ipynb>`_
*****************************************************************************************************************************************************************************************************

  This notebook demonstrates the use of the Bring-Your-Own-Container (BYOC) functionality of Braket Hybrid Jobs. While Amazon Braket has pre-configured environments which support most use cases of Braket Hybrid Jobs, BYOC enables you to define fully customizable environments using Docker containers. You will learn how to use BYOC, including preparing a Dockerfile, creating a private Amazon Elastic Container Registry (ECR), building the container, and submitting a Braket Hybrid Job using the custom container.

*********************************************************************************************************************************************************************************************************************************
`Embedded simulators in Braket Hybrid Jobs <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/hybrid_jobs/4_Embedded_simulators_in_Braket_Hybrid_Jobs/Embedded_simulators_in_Braket_Hybrid_Jobs.ipynb>`_
*********************************************************************************************************************************************************************************************************************************

  This notebook shows how to use embedded simulators in Braket Hybrid Jobs. An embedded simulator is a local simulator that runs completely within a hybrid job instance, i.e., the compute resource that is running your algorithm script. In contrast, on-demand simulators, such as SV1, DM1, or TN1, calculate the results of a quantum circuit on dedicated compute infrastructure on-demand by Amazon Braket. Hybrid workloads usually consist of iterations of quantum circuit executions and variational parameter optimizations. By using embedded simulators, we keep all computations in the same environment. This allows the optimization algorithm to access advanced features supported by the embedded simulator.

***************************************************************************************************************************************************************************************************************
`Parallelize training for Quantum Machine Learning <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/hybrid_jobs/5_Parallelize_training_for_QML/Parallelize_training_for_QML.ipynb>`_
***************************************************************************************************************************************************************************************************************

  This notebook introduces using data parallelism for Quantum Machine Learning (QML) workloads.

*************************************************************************************************************************************************************************************************************************
`QN-SPSA optimizer using an Embedded Simulator <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/hybrid_jobs/6_QNSPSA_optimizer_with_embedded_simulator/qnspsa_with_embedded_simulator.ipynb>`_
*************************************************************************************************************************************************************************************************************************

  This notebook demonstrates how to implement and benchmark the QN-SPSA optimizer, a novel quantum optimization algorithm.

***************************************************************************************************************************************************************************************************************
`Running Jupyter notebooks as a Hybrid Job <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/hybrid_jobs/7_Running_notebooks_as_hybrid_jobs/Running_notebooks_as_hybrid_jobs.ipynb>`_
***************************************************************************************************************************************************************************************************************

  This tutorial is a step-by-step guide for running a Jupyter notebook as a Hybrid Job.

******************************************************************************************************************************************************************************************
`Creating Hybrid Job Scripts <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/hybrid_jobs/8_Creating_Hybrid_Job_Scripts/Creating_your_first_Hybrid_Job.ipynb>`_
******************************************************************************************************************************************************************************************

  This notebook shows an alternate way to create a Hybrid Job without using a @hybrid_job decorator. The demonstrated method may be useful in some circumstances, such as using older versions of Python.

