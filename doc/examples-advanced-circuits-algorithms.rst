################################
Advanced circuits and algorithms
################################

Learn more about working with advanced circuits and algorithms.

.. toctree::
    :maxdepth: 2

***************************************************************************************************************************************
`Grover <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/advanced_circuits_algorithms/Grover/Grover.ipynb>`_
***************************************************************************************************************************************

  This tutorial provides a step-by-step walkthrough explaining Grover's quantum algorithm. We show how to build the corresponding quantum circuit with simple modular building blocks, by means of the Amazon Braket SDK. Specifically, we demonstrate how to build custom gates that are not part of the basic gate set provided by the SDK. A custom gate can used as a core quantum gate by registering it as a subroutine.

******************************************************************************************************************************************************************************************************************
`Quantum Amplitude Amplification <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/advanced_circuits_algorithms/Quantum_Amplitude_Amplification/Quantum_Amplitude_Amplification.ipynb>`_
******************************************************************************************************************************************************************************************************************

  This tutorial provides a detailed discussion and implementation of the Quantum Amplitude Amplification (QAA) algorithm, using the Amazon Braket SDK. QAA is a routine in quantum computing which generalizes the idea behind Grover's famous search algorithm, with applications across many quantum algorithms. In short, QAA uses an iterative approach to systematically increase the probability of finding one or multiple target states in a given search space. In a quantum computer, QAA can be used to obtain a quadratic speedup over several classical algorithms.

************************************************************************************************************************************************************************************************
`Quantum Fourier Transform <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/advanced_circuits_algorithms/Quantum_Fourier_Transform/Quantum_Fourier_Transform.ipynb>`_
************************************************************************************************************************************************************************************************

  This tutorial provides a detailed implementation of the Quantum Fourier Transform (QFT) and the inverse QFT, using the Amazon Braket SDK. We provide two different implementations: with and without recursion. The QFT is an important subroutine to many quantum algorithms, most famously Shor's algorithm for factoring, and the quantum phase estimation (QPE) algorithm for estimating the eigenvalues of a unitary operator. The QFT can be performed efficiently on a quantum computer, using only O(n<sup>2</sup>) single-qubit Hadamard gates and two-qubit controlled phase shift gates, where 𝑛 is the number of qubits. We first review the basics of the quantum Fourier transform, and its relationship to the discrete (classical) Fourier transform. We then implement the QFT in code two ways: recursively and non-recursively. This notebook also showcases the Amazon Braket `circuit.subroutine` functionality, which allows one to define custom methods and add them to the Circuit class.

*********************************************************************************************************************************************************************************************
`Quantum Phase Estimation <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/advanced_circuits_algorithms/Quantum_Phase_Estimation/Quantum_Phase_Estimation.ipynb>`_
*********************************************************************************************************************************************************************************************

  This tutorial provides a detailed implementation of the Quantum Phase Estimation (QPE) algorithm, through the Amazon Braket SDK. The QPE algorithm is designed to estimate the eigenvalues of a unitary operator 𝑈; it is a very important subroutine to many quantum algorithms, most famously Shor's algorithm for factoring, and the HHL algorithm (named after the physicists Harrow, Hassidim and Lloyd) for solving linear systems of equations on a quantum computer. Moreover, eigenvalue problems can be found across many disciplines and application areas, including (for example) principal component analysis (PCA) as used in machine learning, or in the solution of differential equations as relevant across mathematics, physics, engineering and chemistry. We first review the basics of the QPE algorithm. We then implement the QPE algorithm in code using the Amazon Braket SDK, and we illustrate the application of the algorithm with simple examples. This notebook also showcases the Amazon Braket `circuit.subroutine` functionality, which allows you to use custom-built gates as if they were any other built-in gates. This tutorial is set up to run on the local simulator or the on-demand simulator. Changing between these devices requires changing only one line of code, as demonstrated below in cell.

*************************************************************************************************************************************************************************
`Randomness Generation <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/advanced_circuits_algorithms/Randomness/Randomness_Generation.ipynb>`_
*************************************************************************************************************************************************************************

  This tutorial provides a detailed implementation of a Quantum Random Number Generator (QRNG). It shows how to use two separate quantum processor units (QPUs) from different suppliers in Amazon Braket to supply two streams of weakly random bits. We then show how to generate physically secure randomness from these two weak sources by means of classical post-processing based on randomness extractors.

**********************************************************************************************************************************************************************
`Simon's Algorithm <https://github.com/amazon-braket/amazon-braket-examples/tree/main/examples/advanced_circuits_algorithms/Simons_Algorithm/Simons_Algorithm.ipynb>`_
**********************************************************************************************************************************************************************

  This tutorial provides a detailed implementation of Simon’s algorithm, which shows the first example of an exponential speedup over the best known classical algorithm by using a quantum computer to solve a particular problem. Originally published in 1994, Simon’s algorithm was a precursor to Shor’s well-known factoring algorithm, and it served as inspiration for many of the seminal works in quantum computation that followed.

