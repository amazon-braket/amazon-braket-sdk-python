#!/usr/bin/env python
# coding: utf-8

# # Generative modelling with quantum circuits
#
# ## Overview
# This notebook demonstrates unsupervised generative modelling of a classical probability distribution associated with a data set, by training a parameterized quantum circuit on Amazon Braket Hybrid Jobs.
#
# ## Background: Generative modelling
# Generative modelling is an unsupervised learning task where the goal is to generate new synthetic samples from an unknown probability distribution. We denote the target probability distribution as $p(x)$, and the estimated distribution as $p_{\theta}(x)$. The goal is to learn an $p_{\theta}(x)$ that closely resembles the target $p(x)$.  One metric to quantify the difference between probability distributions is the Kullback–Leibler (KL) divergence:
#
# $$
# D(p ||  q) = \sum_x p(x) \log \frac{p(x)}{q(x)}
# $$
# which is zero if and only if $p(x)=q(x)$ for all $x$. If $p(x)$ is not in the support of $q(x)$, the KL divergence is infinite.
#
# Learning a good approximation $p_{\theta}$ depends on the *expressibility* of the model, the effectiveness of the training algorithm, and the ability to sample efficiently.
#
# ## Quantum Circuit Born Machine
# Quantum circuits are a natural fit for generative modeling
# because they are inherently probabilistic; the wavefunction encodes a probability according to the Born rule:
# $$
# p(x) = | \langle x| \psi \rangle|^2
# $$
#
# In quantum mechanics, we do not have access to $p(x)$ directly, but we can efficiently sample using projective measurements. This is an *implicit* generative model similar to generative adversarial networks (GANs). As a generative model, quantum circuits allow fast sampling from a high-dimension distribution, and have expressive power that is greater than corresponding classical models.
#
#
#
# ### References
# [1] Benedetti, Marcello, Erika Lloyd, Stefan Sack, and Mattia Fiorentini. “Parameterized Quantum Circuits as Machine Learning Models.” Quantum Science and Technology 4, no. 4 (November 13, 2019): 043001. https://doi.org/10.1088/2058-9565/ab4eb5.
#
# [2] Benedetti, Marcello, Delfina Garcia-Pintos, Oscar Perdomo, Vicente Leyton-Ortega, Yunseong Nam, and Alejandro Perdomo-Ortiz. “A Generative Modeling Approach for Benchmarking and Training Shallow Quantum Circuits.” Npj Quantum Information 5, no. 1 (May 27, 2019): 1–9. https://doi.org/10.1038/s41534-019-0157-8.
#
# [3] Liu, Jin-Guo, and Lei Wang. “Differentiable Learning of Quantum Circuit Born Machine.” Physical Review A 98, no. 6 (December 19, 2018): 062324. https://doi.org/10.1103/PhysRevA.98.062324.
#

# In[1]:


import time

# import matplotlib.pyplot as plt
import numpy as np

interface = "autograd"
device_arn = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"

# aws_session = AwsSession()
# bucket = aws_session.default_bucket()
# print(bucket)


# In[2]:


# 0. Set parameters
n_qubits = 4


# As an example, let's consider the case of learning a Gaussian distribution. Here $p(x)$ is a Gaussian on 4 bits, with mean at $\mu=1$, and $sigma=1$.

# In[3]:


# 1. Generate dataset
def gaussian_pdf(n_qubits, mu, sigma=1):
    x = np.arange(2 ** n_qubits)
    gaussian = 1.0 / np.sqrt(2 * np.pi * sigma ** 2) * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2))
    return gaussian / gaussian.sum()


p_data = gaussian_pdf(n_qubits, mu=1, sigma=1)
p_data = p_data / sum(p_data)
print(p_data)


# Now to run our algorithm as a Hybrid Job, we need to upload the datset to Amazon S3. The first function saves the `p_data` numpy array into a file and uploads it, the second function just provides a convenience wrapper to uploading the data in Hybrid Jobs.

# In[4]:


print(setup_input_stream())
print(input_data())


# In[5]:


# 3. Declare hyperparameters for QCBM
hyperparams = {"n_qubits": str(n_qubits), "n_layers": "4"}

import pennylane as qml


# In[ ]:


# 4. Submit Amazon Braket Hybrid Job
