| Task | Code |

|---|---|

| Imports | `from braket.experimental\_capabilities import EnableExperimentalCapability` |

| Enable experimental capabilities temporarily | `with EnableExperimentalCapability():` |

| Add IQM feed-forward measurement | `circuit.measure\_ff(0, feedback\_key=0)` |

| Add IQM classically controlled PRx | `circuit.cc\_prx(0, angle\_1=0.15, angle\_2=0.25, feedback\_key=0)` |

| Pass experimental capabilities to a task | `task = device.run(circuit, shots=100, experimental\_capabilities="ALL")` |

| Note | Experimental capabilities may change between SDK releases. Check device support and provider restrictions before production use. |

