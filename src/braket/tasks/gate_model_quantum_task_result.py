# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Counter, Dict, List, Optional

import numpy as np
from braket.circuits import Observable, ResultType, StandardObservable
from braket.circuits.observables import observable_from_ir


@dataclass
class GateModelQuantumTaskResult:
    """
    Result of a gate model quantum task execution. This class is intended
    to be initialized by a QuantumTask class.

    Args:
        task_metadata (Dict[str, Any]): Dictionary of task metadata. task_metadata must have
            keys 'Id', 'Shots', 'Ir', and 'IrType'.
        result_types (List[Dict[str, Any]]): List of dictionaries where each dictionary
            has two keys: 'Type' (the result type in IR JSON form) and
            'Value' (the result value for this result type).
            This can be an empty list if no result types are specified in the IR.
            This is calculated from `measurements` and
            the IR of the circuit program when `shots>0`.
        values (List[Any]): The values for result types requested in the circuit.
            This can be an empty list if no result types are specified in the IR.
            This is calculated from `measurements` and
            the IR of the circuit program when `shots>0`.
        measurements (numpy.ndarray, optional): 2d array - row is shot, column is qubit.
            Default is None. Only available when shots > 0. The qubits in `measurements`
            are the ones in `GateModelQuantumTaskResult.measured_qubits`.
        measured_qubits (List[int], optional): The indices of the measured qubits. Default
            is None. Only available when shots > 0. Indicates which qubits are in
            `measurements`.
        measurement_counts (Counter, optional): A Counter of measurements. Key is the measurements
            in a big endian binary string. Value is the number of times that measurement occurred.
            Default is None. Only available when shots > 0.
        measurement_probabilities (Dict[str, float], optional):
            A dictionary of probabilistic results.
            Key is the measurements in a big endian binary string.
            Value is the probability the measurement occurred.
            Default is None. Only available when shots > 0.
        measurements_copied_from_device (bool, optional): flag whether `measurements`
            were copied from device. If false, `measurements` are calculated from device data.
            Default is None. Only available when shots > 0.
        measurement_counts_copied_from_device (bool, optional): flag whether `measurement_counts`
            were copied from device. If False, `measurement_counts` are calculated from device data.
            Default is None. Only available when shots > 0.
        measurement_probabilities_copied_from_device (bool, optional): flag whether
            `measurement_probabilities` were copied from device. If false,
            `measurement_probabilities` are calculated from device data. Default is None.
            Only available when shots > 0.
    """

    task_metadata: Dict[str, Any]
    result_types: List[Dict[str, str]]
    values: List[Any]
    measurements: np.ndarray = None
    measured_qubits: List[int] = None
    measurement_counts: Counter = None
    measurement_probabilities: Dict[str, float] = None
    measurements_copied_from_device: bool = None
    measurement_counts_copied_from_device: bool = None
    measurement_probabilities_copied_from_device: bool = None

    def get_value_by_result_type(self, result_type: ResultType) -> Any:
        """
        Get value by result type. The result type must have already been
        requested in the circuit sent to the device for this task result.

        Args:
            result_type (ResultType): result type requested

        Returns:
            Any: value of the result corresponding to the result type

        Raises:
            ValueError: If result type not found in result.
                Result types must be added to circuit before circuit is run on device.
        """
        rt_json = result_type.to_ir().json()
        for rt in self.result_types:
            if rt_json == json.dumps(rt["Type"]):
                return rt["Value"]
        raise ValueError(
            "Result type not found in result. "
            + "Result types must be added to circuit before circuit is run on device."
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, GateModelQuantumTaskResult) and self.task_metadata.get("Id"):
            return self.task_metadata["Id"] == other.task_metadata["Id"]
        return NotImplemented

    @staticmethod
    def measurement_counts_from_measurements(measurements: np.ndarray) -> Counter:
        """
        Creates measurement counts from measurements

        Args:
            measurements (numpy.ndarray): 2d array - row is shot, column is qubit.

        Returns:
            Counter: A Counter of measurements. Key is the measurements in a big endian binary
                string. Value is the number of times that measurement occurred.
        """
        bitstrings = []
        for j in range(len(measurements)):
            bitstrings.append("".join([str(element) for element in measurements[j]]))
        return Counter(bitstrings)

    @staticmethod
    def measurement_probabilities_from_measurement_counts(
        measurement_counts: Counter,
    ) -> Dict[str, float]:
        """
        Creates measurement probabilities from measurement counts

        Args:
            measurement_counts (Counter): A Counter of measurements. Key is the measurements
                in a big endian binary string. Value is the number of times that measurement
                occurred.

        Returns:
            Dict[str, float]: A dictionary of probabilistic results. Key is the measurements
                in a big endian binary string. Value is the probability the measurement occurred.
        """
        measurement_probabilities = {}
        shots = sum(measurement_counts.values())

        for key, count in measurement_counts.items():
            measurement_probabilities[key] = count / shots
        return measurement_probabilities

    @staticmethod
    def measurements_from_measurement_probabilities(
        measurement_probabilities: Dict[str, float], shots: int
    ) -> np.ndarray:
        """
        Creates measurements from measurement probabilities

        Args:
            measurement_probabilities (Dict[str, float]): A dictionary of probabilistic results.
                Key is the measurements in a big endian binary string.
                Value is the probability the measurement occurred.
            shots (int): number of iterations on device

        Returns:
            Dict[str, float]: A dictionary of probabilistic results.
                Key is the measurements in a big endian binary string.
                Value is the probability the measurement occurred.
        """
        measurements_list = []
        for bitstring in measurement_probabilities:
            measurement = list(bitstring)
            individual_measurement_list = [measurement] * int(
                round(measurement_probabilities[bitstring] * shots)
            )
            measurements_list.extend(individual_measurement_list)
        return np.asarray(measurements_list, dtype=int)

    @staticmethod
    def from_dict(result: Dict[str, Any]):
        """
        Create GateModelQuantumTaskResult from dict.

        Args:
            result (Dict[str, Any]): Results dict with GateModelQuantumTaskResult attributes as keys

        Returns:
            GateModelQuantumTaskResult: A GateModelQuantumTaskResult based on the given dict

        Raises:
            ValueError: If neither "Measurements" nor "MeasurementProbabilities" is a key
                in the result dict
        """
        return GateModelQuantumTaskResult._from_dict_internal(result)

    @staticmethod
    def from_string(result: str) -> GateModelQuantumTaskResult:
        """
        Create GateModelQuantumTaskResult from string.

        Args:
            result (str): JSON object string, with GateModelQuantumTaskResult attributes as keys.

        Returns:
            GateModelQuantumTaskResult: A GateModelQuantumTaskResult based on the given string

        Raises:
            ValueError: If neither "Measurements" nor "MeasurementProbabilities" is a key
                in the result dict
        """
        json_obj = json.loads(result)
        for result_type in json_obj.get("ResultTypes", []):
            type = result_type["Type"]["type"]
            if type == "probability":
                result_type["Value"] = np.array(result_type["Value"])
            elif type == "statevector":
                result_type["Value"] = np.array([complex(*value) for value in result_type["Value"]])
            elif type == "amplitude":
                for state in result_type["Value"]:
                    result_type["Value"][state] = complex(*result_type["Value"][state])
        return GateModelQuantumTaskResult._from_dict_internal(json_obj)

    @classmethod
    def _from_dict_internal(cls, result: Dict[str, Any]):
        if result["TaskMetadata"]["Shots"] > 0:
            return GateModelQuantumTaskResult._from_dict_internal_computational_basis_sampling(
                result
            )
        else:
            return GateModelQuantumTaskResult._from_dict_internal_simulator_only(result)

    @classmethod
    def _from_dict_internal_computational_basis_sampling(cls, result: Dict[str, Any]):
        task_metadata = result["TaskMetadata"]
        if "Measurements" in result:
            measurements = np.asarray(result["Measurements"], dtype=int)
            m_counts = GateModelQuantumTaskResult.measurement_counts_from_measurements(measurements)
            m_probs = GateModelQuantumTaskResult.measurement_probabilities_from_measurement_counts(
                m_counts
            )
            measurements_copied_from_device = True
            m_counts_copied_from_device = False
            m_probabilities_copied_from_device = False
        elif "MeasurementProbabilities" in result:
            shots = task_metadata["Shots"]
            m_probs = result["MeasurementProbabilities"]
            measurements = GateModelQuantumTaskResult.measurements_from_measurement_probabilities(
                m_probs, shots
            )
            m_counts = GateModelQuantumTaskResult.measurement_counts_from_measurements(measurements)
            measurements_copied_from_device = False
            m_counts_copied_from_device = False
            m_probabilities_copied_from_device = True
        else:
            raise ValueError(
                'One of "Measurements" or "MeasurementProbabilities" must be in the result dict'
            )
        measured_qubits = result["MeasuredQubits"]
        if len(measured_qubits) != measurements.shape[1]:
            raise ValueError(
                f"Measured qubits {measured_qubits} is not equivalent to number of qubits "
                + f"{measurements.shape[1]} in measurements"
            )
        result_types = GateModelQuantumTaskResult._calculate_result_types(
            result["TaskMetadata"]["Ir"], measurements, measured_qubits
        )
        values = [rt["Value"] for rt in result_types]
        return cls(
            task_metadata=task_metadata,
            result_types=result_types,
            values=values,
            measurements=measurements,
            measured_qubits=measured_qubits,
            measurement_counts=m_counts,
            measurement_probabilities=m_probs,
            measurements_copied_from_device=measurements_copied_from_device,
            measurement_counts_copied_from_device=m_counts_copied_from_device,
            measurement_probabilities_copied_from_device=m_probabilities_copied_from_device,
        )

    @classmethod
    def _from_dict_internal_simulator_only(cls, result: Dict[str, Any]):
        task_metadata = result["TaskMetadata"]
        result_types = result["ResultTypes"]
        values = [rt["Value"] for rt in result_types]
        return cls(task_metadata=task_metadata, result_types=result_types, values=values)

    @staticmethod
    def _calculate_result_types(
        ir_string: str, measurements: np.ndarray, measured_qubits: List[int]
    ) -> List[Dict[str, Any]]:
        ir = json.loads(ir_string)
        result_types = []
        if not ir.get("results"):
            return result_types
        for result_type in ir["results"]:
            ir_observable = result_type.get("observable")
            observable = observable_from_ir(ir_observable) if ir_observable else None
            targets = result_type.get("targets")
            rt_type = result_type["type"]
            if rt_type == "probability":
                value = GateModelQuantumTaskResult._probability_from_measurements(
                    measurements, measured_qubits, targets
                )
            elif rt_type == "sample":
                if targets:
                    value = GateModelQuantumTaskResult._samples_from_measurements(
                        measurements, measured_qubits, observable, targets
                    )
                else:
                    value = [
                        GateModelQuantumTaskResult._samples_from_measurements(
                            measurements, measured_qubits, observable, [i]
                        )
                        for i in measured_qubits
                    ]
            elif rt_type == "variance":
                if targets:
                    value = GateModelQuantumTaskResult._variance_from_measurements(
                        measurements, measured_qubits, observable, targets
                    )
                else:
                    value = [
                        GateModelQuantumTaskResult._variance_from_measurements(
                            measurements, measured_qubits, observable, [i]
                        )
                        for i in measured_qubits
                    ]
            elif rt_type == "expectation":
                if targets:
                    value = GateModelQuantumTaskResult._expectation_from_measurements(
                        measurements, measured_qubits, observable, targets
                    )
                else:
                    value = [
                        GateModelQuantumTaskResult._expectation_from_measurements(
                            measurements, measured_qubits, observable, [i]
                        )
                        for i in measured_qubits
                    ]
            else:
                raise ValueError(f"Unknown result type {rt_type}")
            result_types.append({"Type": result_type, "Value": value})
        return result_types

    @staticmethod
    def _selected_measurements(
        measurements: np.ndarray, measured_qubits: List[int], targets: Optional[List[int]]
    ) -> np.ndarray:
        if not (targets is None or targets == measured_qubits):
            # Only some qubits targeted
            columns = [measured_qubits.index(t) for t in targets]
            measurements = measurements[:, columns]
        return measurements

    @staticmethod
    def _probability_from_measurements(
        measurements: np.ndarray, measured_qubits: List[int], targets: Optional[List[int]]
    ) -> np.ndarray:
        measurements = GateModelQuantumTaskResult._selected_measurements(
            measurements, measured_qubits, targets
        )
        shots, num_measured_qubits = measurements.shape
        # convert samples from a list of 0, 1 integers, to base 10 representation
        unraveled_indices = [2] * num_measured_qubits
        indices = np.ravel_multi_index(measurements.T, unraveled_indices)

        # count the basis state occurrences, and construct the probability vector
        basis_states, counts = np.unique(indices, return_counts=True)
        probabilities = np.zeros([2 ** num_measured_qubits], dtype=np.float64)
        probabilities[basis_states] = counts / shots
        return probabilities

    @staticmethod
    def _variance_from_measurements(
        measurements: np.ndarray,
        measured_qubits: List[int],
        observable: Observable,
        targets: List[int],
    ) -> float:
        samples = GateModelQuantumTaskResult._samples_from_measurements(
            measurements, measured_qubits, observable, targets
        )
        return np.var(samples)

    @staticmethod
    def _expectation_from_measurements(
        measurements: np.ndarray,
        measured_qubits: List[int],
        observable: Observable,
        targets: List[int],
    ) -> float:
        samples = GateModelQuantumTaskResult._samples_from_measurements(
            measurements, measured_qubits, observable, targets
        )
        return np.mean(samples)

    @staticmethod
    def _samples_from_measurements(
        measurements: np.ndarray,
        measured_qubits: List[int],
        observable: Observable,
        targets: List[int],
    ) -> np.ndarray:
        measurements = GateModelQuantumTaskResult._selected_measurements(
            measurements, measured_qubits, targets
        )
        shots, num_measured_qubits = measurements.shape
        if isinstance(observable, StandardObservable):
            # Process samples for observables with eigenvalues {1, -1}
            return 1 - 2 * measurements.flatten()
        # Replace the basis state in the computational basis with the correct eigenvalue.
        # Extract only the columns of the basis samples required based on ``wires``.
        unraveled_indices = [2] * num_measured_qubits
        indices = np.ravel_multi_index(measurements.T, unraveled_indices)
        return observable.eigenvalues[indices]
