##############################
Simple circuits and algorithms
##############################

Learn more about working with advanced circuits and algoritms.

.. toctree::
    :maxdepth: 2
  
***************
Getting started
***************

A hello-world tutorial that shows you how to build a simple circuit and run it on a local simulator.

***************
Running quantum circuits on simulators
***************

This tutorial prepares a paradigmatic example for a multi-qubit entangled state, 
the so-called GHZ state (named after the three physicists Greenberger, Horne, and Zeilinger). 
The GHZ state is extremely non-classical, and therefore very sensitive to decoherence. 
It is often used as a performance benchmark for today's hardware. In many quantum information 
protocols it is used as a resource for quantum error correction, quantum communication, 
and quantum metrology.

***************
Running quantum circuits on QPU devices
***************

This tutorial prepares a maximally-entangled Bell state between two qubits, 
for classical simulators and for QPUs. For classical devices, we can run the circuit on a 
local simulator or a cloud-based managed simulator. For the quantum devices, 
we run the circuit on the superconducting machine from Rigetti, and on the ion-trap 
machine provided by IonQ. 

***************
Deep Dive into the anatomy of quantum circuits
***************

This tutorial discusses in detail the anatomy of quantum circuits in the Amazon 
Braket SDK. You will learn how to build (parameterized) circuits and display them 
graphically, and how to append circuits to each other. Nex, learn
more about circuit depth and circuit size. Finally you will learn how to execute 
the circuit on a device of our choice (defining a quantum task) and how to track, log, 
recover, or cancel a quantum task efficiently.

***************
Superdense coding
***************

This tutorial constructs an implementation of the superdense coding protocol using  
the Amazon Braket SDK. Superdense coding is a method of transmitting two classical 
bits by sending only one qubit. Starting with a pair of entanged qubits, the sender 
(aka Alice) applies a certain quantum gate to their qubit and sends the result 
to the receiver (aka Bob), who is then able to decode the full two-bit message.

