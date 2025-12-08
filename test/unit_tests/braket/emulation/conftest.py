# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import json
import numpy as np
import pytest
import datetime

from braket.circuits import Circuit
from braket.device_schema.standardized_gate_model_qpu_device_properties_v1 import (
    CoherenceTime,
    Fidelity1Q,
    FidelityType,
    OneQubitProperties,
    TwoQubitProperties,
    GateFidelity2Q,
)
from braket.device_schema.ionq.ionq_device_capabilities_v1 import IonqDeviceCapabilities
from braket.device_schema.aqt.aqt_device_capabilities_v1 import AqtDeviceCapabilities

#################################################
# Common test data for device property fixtures
#################################################


def create_one_qubit_properties(fidelity_types):
    """
    Create OneQubitProperties with specified fidelity types.

    Args:
        fidelity_types (list): List of fidelity type names to include

    Returns:
        dict: OneQubitProperties as a dictionary
    """
    fidelities = []

    for fidelity_type in fidelity_types:
        fidelities.append(
            Fidelity1Q(
                fidelityType=FidelityType(name=fidelity_type, description=None),
                fidelity=0.99 if fidelity_type != "READOUT" else 0.9795,
                standardError=None,
            )
        )

    return OneQubitProperties(
        T1=CoherenceTime(value=2e-5, standardError=None, unit="S"),
        T2=CoherenceTime(value=8e-6, standardError=None, unit="S"),
        oneQubitFidelity=fidelities,
    ).dict()


def create_two_qubit_properties(gate_names):
    """
    Create TwoQubitProperties with specified gate names.

    Args:
        gate_names (list): List of gate names to include

    Returns:
        dict: TwoQubitProperties as a dictionary
    """
    gate_fidelities = []

    for gate_name in gate_names:
        gate_fidelities.append(
            GateFidelity2Q(
                direction=None,
                gateName=gate_name,
                fidelity=0.99,
                standardError=0.0009,
                fidelityType=FidelityType(name="RANDOMIZED_BENCHMARKING", description=None),
            )
        )

    return TwoQubitProperties(twoQubitGateFidelity=gate_fidelities).dict()


# Valid one-qubit properties with RANDOMIZED_BENCHMARKING fidelity
valid_oneQubitProperties = create_one_qubit_properties(["RANDOMIZED_BENCHMARKING", "READOUT"])

# Valid one-qubit properties with SIMULTANEOUS_RANDOMIZED_BENCHMARKING fidelity
valid_oneQubitProperties_v2 = create_one_qubit_properties([
    "SIMULTANEOUS_RANDOMIZED_BENCHMARKING",
    "READOUT",
])

# Valid two-qubit properties with CZ and ISwap gates
valid_twoQubitProperties = create_two_qubit_properties(["CZ", "ISwap"])

# Common supported result types
valid_supportedResultTypes = [
    {"maxShots": 20000, "minShots": 1, "name": "Probability", "observables": None}
]

# Common native gate sets
valid_nativeGateSet = ["cz", "prx"]

#################################################
# Invalid device properties for testing
#################################################

# Invalid one-qubit properties without 1q rb data
invalid_oneQubitProperties = create_one_qubit_properties(["READOUT"])

# Invalid two-qubit properties without valid Braket gates
invalid_twoQubitProperties = create_two_qubit_properties(["not_a_braket_gate"])

# Invalid device properties with missing one-qubit RB data
invalid_device_properties_dict_1 = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.iqm.iqm_device_capabilities",
        "version": "1",
    },
    "service": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.device_service_properties",
            "version": "1",
        },
        "executionWindows": [],
        "shotsRange": [1, 20000],
        "updatedAt": "2024-04-04T01:10:02.869136",
    },
    "deviceParameters": {},
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "supportedOperations": [],
            "supportedResultTypes": valid_supportedResultTypes,
            "version": ["1.0"],
        }
    },
    "paradigm": {
        "connectivity": {"connectivityGraph": {}, "fullyConnected": False},
        "nativeGateSet": valid_nativeGateSet,
        "qubitCount": 2,
    },
    "standardized": {
        "oneQubitProperties": {
            "0": invalid_oneQubitProperties,
            "1": valid_oneQubitProperties,
        },
        "twoQubitProperties": {
            "0-1": valid_twoQubitProperties,
        },
    },
}

# Invalid device properties with invalid two-qubit gate names
invalid_device_properties_dict_2 = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.iqm.iqm_device_capabilities",
        "version": "1",
    },
    "service": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.device_service_properties",
            "version": "1",
        },
        "executionWindows": [],
        "shotsRange": [1, 20000],
        "updatedAt": "2024-04-04T01:10:02.869136",
    },
    "deviceParameters": {},
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "supportedOperations": [],
            "supportedResultTypes": valid_supportedResultTypes,
            "version": ["1.0"],
        }
    },
    "paradigm": {
        "connectivity": {"connectivityGraph": {}, "fullyConnected": False},
        "nativeGateSet": valid_nativeGateSet,
        "qubitCount": 2,
    },
    "standardized": {
        "oneQubitProperties": {
            "0": valid_oneQubitProperties,
            "1": valid_oneQubitProperties,
        },
        "twoQubitProperties": {
            "0-1": invalid_twoQubitProperties,
        },
    },
}

#################################################
# IQM device property fixtures
#################################################

# IQM device properties with simple connectivity
reduced_standardized_gate_model_qpu_device_properties_dict = {
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "supportedOperations": [],
            "supportedResultTypes": valid_supportedResultTypes,
            "version": ["1"],
        }
    },
    "braketSchemaHeader": {
        "name": "braket.device_schema.iqm.iqm_device_capabilities",
        "version": "1",
    },
    "deviceParameters": {},
    "paradigm": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.gate_model_qpu_paradigm_properties",
            "version": "1",
        },
        "connectivity": {"connectivityGraph": {"0": ["1"]}, "fullyConnected": False},
        "nativeGateSet": ["cz", "prx"],
        "qubitCount": 2,
    },
    "service": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.device_service_properties",
            "version": "1",
        },
        "executionWindows": [],
        "shotsRange": [1, 20000],
        "updatedAt": "2024-04-04T01:10:02.869136",
    },
    "standardized": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
            "version": "1",
        },
        "oneQubitProperties": {
            "0": valid_oneQubitProperties,
            "1": valid_oneQubitProperties_v2,
        },
        "twoQubitProperties": {"0-1": valid_twoQubitProperties},
    },
}

# IQM device properties with directed connectivity
reduced_standardized_gate_model_qpu_device_properties_dict_non_fully_connected_directed = {
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "supportedOperations": [],
            "supportedResultTypes": valid_supportedResultTypes,
            "version": ["1"],
        }
    },
    "braketSchemaHeader": {
        "name": "braket.device_schema.iqm.iqm_device_capabilities",
        "version": "1",
    },
    "deviceParameters": {},
    "paradigm": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.gate_model_qpu_paradigm_properties",
            "version": "1",
        },
        "connectivity": {"connectivityGraph": {"0": ["1"], "1": ["2"]}, "fullyConnected": False},
        "nativeGateSet": ["cz", "prx"],
        "qubitCount": 3,
    },
    "service": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.device_service_properties",
            "version": "1",
        },
        "executionWindows": [],
        "shotsRange": [1, 20000],
    },
    "standardized": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
            "version": "1",
        },
        "oneQubitProperties": {
            "0": valid_oneQubitProperties,
            "1": valid_oneQubitProperties,
            "2": valid_oneQubitProperties,
        },
        "twoQubitProperties": {
            "0-1": valid_twoQubitProperties,
            "1-2": valid_twoQubitProperties,
        },
    },
}


@pytest.fixture
def reduced_standardized_json():
    """
    Fixture providing a JSON string of IQM device properties with simple connectivity.
    """
    return json.dumps(reduced_standardized_gate_model_qpu_device_properties_dict)


@pytest.fixture
def reduced_standardized_json_3():
    """
    Fixture providing a JSON string of IQM device properties with directed connectivity.
    """
    return json.dumps(
        reduced_standardized_gate_model_qpu_device_properties_dict_non_fully_connected_directed
    )


#################################################
# Rigetti device property fixtures
#################################################

# Rigetti device properties with undirected connectivity
reduced_standardized_gate_model_qpu_device_properties_dict_non_fully_connected_undirected = {
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "supportedOperations": [],
            "supportedResultTypes": valid_supportedResultTypes,
            "version": ["1"],
        }
    },
    "braketSchemaHeader": {
        "name": "braket.device_schema.rigetti.rigetti_device_capabilities",
        "version": "1",
    },
    "deviceParameters": {},
    "paradigm": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.gate_model_qpu_paradigm_properties",
            "version": "1",
        },
        "connectivity": {
            "connectivityGraph": {"0": ["1"], "1": ["0", "2"], "2": ["1"]},
            "fullyConnected": False,
        },
        "nativeGateSet": ["rx", "rz", "iswap"],
        "qubitCount": 3,
    },
    "service": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.device_service_properties",
            "version": "1",
        },
        "executionWindows": [],
        "shotsRange": [1, 20000],
    },
    "standardized": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
            "version": "1",
        },
        "oneQubitProperties": {
            "0": valid_oneQubitProperties,
            "1": valid_oneQubitProperties,
            "2": valid_oneQubitProperties,
        },
        "twoQubitProperties": {"0-1": valid_twoQubitProperties, "1-2": valid_twoQubitProperties},
    },
}


@pytest.fixture
def reduced_standardized_json_2():
    """
    Fixture providing a JSON string of Rigetti device properties with undirected connectivity.
    """
    return json.dumps(
        reduced_standardized_gate_model_qpu_device_properties_dict_non_fully_connected_undirected
    )


#################################################
# IonQ device property fixtures
#################################################

# IonQ device properties with fully connected topology
reduced_ionq_device_capabilities_dict = {
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "supportedOperations": [],
            "supportedResultTypes": valid_supportedResultTypes,
            "version": ["1"],
        }
    },
    "braketSchemaHeader": {
        "name": "braket.device_schema.ionq.ionq_device_capabilities",
        "version": "1",
    },
    "deviceParameters": {},
    "paradigm": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.gate_model_qpu_paradigm_properties",
            "version": "1",
        },
        "connectivity": {"connectivityGraph": {}, "fullyConnected": True},
        "nativeGateSet": ["GPI", "GPI2", "MS"],
        "qubitCount": 25,
    },
    "provider": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.ionq.ionq_provider_properties",
            "version": "1",
        },
        "errorMitigation": {
            "braket.device_schema.error_mitigation.debias.Debias": {"minimumShots": 2500}
        },
        "fidelity": {"1Q": {"mean": 0.9998}, "2Q": {"mean": 0.99}, "spam": {"mean": 0.9937}},
        "timing": {
            "1Q": 0.000135,
            "2Q": 0.0006,
            "T1": 123.45678,
            "T2": 1.0,
            "readout": 0.0003,
            "reset": 2e-05,
        },
    },
    "service": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.device_service_properties",
            "version": "1",
        },
        "executionWindows": [],
        "shotsRange": [1, 20000],
    },
}


@pytest.fixture
def reduced_ionq_device_capabilities_json():
    """
    Fixture providing a JSON string of IonQ device properties.
    """
    return json.dumps(reduced_ionq_device_capabilities_dict)


@pytest.fixture
def reduced_ionq_device_capabilities(reduced_ionq_device_capabilities_json):
    """
    Fixture providing an IonqDeviceCapabilities object.
    """
    return IonqDeviceCapabilities.parse_raw(reduced_ionq_device_capabilities_json)


#################################################
# AQT device property fixtures
#################################################

# AQT device properties with fully connected topology
reduced_aqt_device_capabilities_dict = {
    "action": {
        "braket.ir.openqasm.program": {
            "actionType": "braket.ir.openqasm.program",
            "supportedOperations": [],
            "supportedResultTypes": valid_supportedResultTypes,
            "version": ["1"],
        }
    },
    "braketSchemaHeader": {
        "name": "braket.device_schema.aqt.aqt_device_capabilities",
        "version": "1",
    },
    "deviceParameters": {},
    "paradigm": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.gate_model_qpu_paradigm_properties",
            "version": "1",
        },
        "connectivity": {"connectivityGraph": {}, "fullyConnected": True},
        "nativeGateSet": ["prx", "cz", "xx"],
        "qubitCount": 3,
    },
    "provider": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.aqt.aqt_provider_properties",
            "version": "1",
        },
        "properties": {
            "mean_two_qubit_gate_fidelity": {"uncertainty": 0.0048, "value": 97.6907},
            "readout_time_micros": 1500.0,
            "single_qubit_gate_duration_micros": 30.0,
            "single_qubit_gate_fidelity": {
                "0": {"uncertainty": 4e-05, "value": 99.99973},
                "1": {"uncertainty": 3e-05, "value": 99.99966},
                "2": {"uncertainty": 6e-05, "value": 99.99971},
            },
            "spam_fidelity_lower_bound": 99.74,
            "t1_s": {"uncertainty": 0.007, "value": 1.168},
            "t2_coherence_time_s": {"uncertainty": 0.0442, "value": 0.1632},
            "two_qubit_gate_duration_micros": 290.0,
            "updated_at": "2000-09-19 12:00:00",
        },
    },
    "service": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.device_service_properties",
            "version": "1",
        },
        "executionWindows": [],
        "shotsRange": [1, 2000],
    },
    "standardized": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.standardized_gate_model_qpu_device_properties",
            "version": "3",
        },
        "T1": {"standardError": 0.007, "unit": "s", "value": 1.168},
        "T2": {"standardError": 0.0442, "unit": "s", "value": 0.1632},
        "oneQubitProperties": {
            "0": {
                "oneQubitFidelity": [
                    {
                        "fidelity": 0.9999973,
                        "fidelityType": {"description": None, "name": "RANDOMIZED_BENCHMARKING"},
                        "median": None,
                        "standardError": 4e-05,
                        "unit": "fraction",
                    }
                ]
            },
            "1": {
                "oneQubitFidelity": [
                    {
                        "fidelity": 0.9899973,
                        "fidelityType": {"description": None, "name": "RANDOMIZED_BENCHMARKING"},
                        "median": None,
                        "standardError": 3e-05,
                        "unit": "fraction",
                    }
                ]
            },
            "2": {
                "oneQubitFidelity": [
                    {
                        "fidelity": 0.9989973,
                        "fidelityType": {"description": None, "name": "RANDOMIZED_BENCHMARKING"},
                        "median": None,
                        "standardError": 2e-05,
                        "unit": "fraction",
                    }
                ]
            },
        },
        "readoutFidelity": [
            {
                "fidelity": 0.9974,
                "fidelityType": None,
                "median": None,
                "standardError": None,
                "unit": "fraction",
            }
        ],
        "twoQubitGateFidelity": [
            {
                "fidelity": 0.9769070000000001,
                "fidelityType": {"description": None, "name": "RANDOMIZED_BENCHMARKING"},
                "median": None,
                "standardError": 0.0048,
                "unit": "fraction",
            }
        ],
    },
}


@pytest.fixture
def reduced_aqt_device_capabilities_json():
    """
    Fixture providing a JSON string of AQT device properties.
    """
    return json.dumps(reduced_aqt_device_capabilities_dict)


@pytest.fixture
def reduced_aqt_device_capabilities(reduced_aqt_device_capabilities_json):
    """
    Fixture providing an AqtDeviceCapabilities object.
    """
    return AqtDeviceCapabilities.parse_raw(reduced_aqt_device_capabilities_json)


#################################################
# Circuit fixtures
#################################################


@pytest.fixture
def valid_verbatim_circ_garnet():
    """
    Fixture providing a valid verbatim circuit for Garnet device.
    """
    return Circuit().add_verbatim_box(Circuit().prx(1, 0, 0).cz(1, 2).prx(2, np.pi, 0).cz(0, 1))


@pytest.fixture
def valid_verbatim_circ_ankaa3():
    """
    Fixture providing a valid verbatim circuit for Ankaa-3 device.
    """
    return Circuit().add_verbatim_box(
        Circuit().rx(0, np.pi).rz(1, np.pi).iswap(0, 1).iswap(1, 2).rx(2, np.pi)
    )


@pytest.fixture
def valid_verbatim_circ_aria1():
    """
    Fixture providing a valid verbatim circuit for Aria-1 device.
    """
    return Circuit().add_verbatim_box(
        Circuit()
        .gpi(0, 3.14)
        .gpi2(1, 3.14)
        .ms(0, 1, 3.1, 3.2, 3.3)
        .ms(1, 2, 3.1, 3.3, 4.3)
        .gpi(2, 3.14)
    )
