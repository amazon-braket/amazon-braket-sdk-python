# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
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

import re

import braket.ir.jaqcd as ir
from braket.circuits import circuit
from braket.circuits.free_parameter import FreeParameter
from braket.circuits.observable import Observable
from braket.circuits.result_type import (
    ObservableParameterResultType,
    ObservableResultType,
    ResultType,
)
from braket.circuits.serialization import IRType, OpenQASMSerializationProperties
from braket.registers.qubit_set import QubitSet, QubitSetInput

"""
To add a new result type:
    1. Implement the class and extend `ResultType`
    2. Add a method with the `@circuit.subroutine(register=True)` decorator. Method name
       is added into the `Circuit` class. This method is the default way
       clients add this result type to a circuit.
    3. Register the class with the `ResultType` class via `ResultType.register_result_type()`.
"""


class StateVector(ResultType):
    """The full state vector as a requested result type.
    This is available on simulators only when `shots=0`.
    """

    def __init__(self):
        super().__init__(ascii_symbols=["StateVector"])

    def _to_jaqcd(self) -> ir.StateVector:
        return ir.StateVector.construct()

    def _to_openqasm(self, serialization_properties: OpenQASMSerializationProperties) -> str:
        return "#pragma braket result state_vector"

    @staticmethod
    @circuit.subroutine(register=True)
    def state_vector() -> ResultType:
        """Registers this function into the circuit class.

        Returns:
            ResultType: state vector as a requested result type

        Examples:
            >>> circ = Circuit().state_vector()
        """
        return ResultType.StateVector()

    def __eq__(self, other: StateVector) -> bool:
        return isinstance(other, StateVector)

    def __copy__(self) -> StateVector:
        return type(self)()

    # must redefine __hash__ since __eq__ is overwritten
    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    def __hash__(self) -> int:
        return super().__hash__()


ResultType.register_result_type(StateVector)


class DensityMatrix(ResultType):
    """The full density matrix as a requested result type.
    This is available on simulators only when `shots=0`.
    """

    def __init__(self, target: QubitSetInput | None = None):
        """Inits a `DensityMatrix`.

        Args:
            target (QubitSetInput | None): The target qubits
                of the reduced density matrix. Default is `None`, and the
                full density matrix is returned.

        Examples:
            >>> result_types.DensityMatrix(target=[0, 1])
        """
        self._target = QubitSet(target)
        ascii_symbols = ["DensityMatrix"] * len(self._target) if self._target else ["DensityMatrix"]
        super().__init__(ascii_symbols=ascii_symbols)

    @property
    def target(self) -> QubitSet:
        return self._target

    @target.setter
    def target(self, target: QubitSetInput) -> None:
        """Sets the target qubit set.

        Args:
            target (QubitSetInput): The target qubit set.
        """
        self._target = QubitSet(target)

    def _to_jaqcd(self) -> ir.DensityMatrix:
        if self.target:
            # convert qubits to int as required by the ir type
            return ir.DensityMatrix.construct(targets=[int(qubit) for qubit in self.target])
        return ir.DensityMatrix.construct()

    def _to_openqasm(self, serialization_properties: OpenQASMSerializationProperties) -> str:
        if not self.target:
            return "#pragma braket result density_matrix all"
        targets = ", ".join(
            serialization_properties.format_target(int(target)) for target in self.target
        )
        return f"#pragma braket result density_matrix {targets}"

    @staticmethod
    @circuit.subroutine(register=True)
    def density_matrix(target: QubitSetInput | None = None) -> ResultType:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput | None): The target qubits
                of the reduced density matrix. Default is `None`, and the
                full density matrix is returned.

        Returns:
            ResultType: density matrix as a requested result type

        Examples:
            >>> circ = Circuit().density_matrix(target=[0, 1])
        """
        return ResultType.DensityMatrix(target=target)

    def __eq__(self, other: DensityMatrix) -> bool:
        if isinstance(other, DensityMatrix):
            return self.target == other.target
        return False

    def __repr__(self) -> str:
        return f"DensityMatrix(target={self.target})"

    def __copy__(self) -> DensityMatrix:
        return type(self)(target=self.target)

    # must redefine __hash__ since __eq__ is overwritten
    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    def __hash__(self) -> int:
        return super().__hash__()


ResultType.register_result_type(DensityMatrix)


class AdjointGradient(ObservableParameterResultType):
    """The gradient of the expectation value of the provided observable, applied to target,
    with respect to the given parameter.
    """

    def __init__(
        self,
        observable: Observable,
        target: list[QubitSetInput] | None = None,
        parameters: list[str | FreeParameter] | None = None,
    ):
        """Inits an `AdjointGradient`.

        Args:
            observable (Observable): The expectation value of this observable is the function
                against which parameters in the gradient are differentiated.
            target (list[QubitSetInput] | None): Target qubits that the result type is requested
                for. Each term in the target list should have the same number of qubits as the
                corresponding term in the observable. Default is `None`, which means the
                observable must operate only on 1 qubit and it is applied to all qubits
                in parallel.
            parameters (list[Union[str, FreeParameter]] | None): The free parameters in the circuit
                to differentiate with respect to. Default: `all`.

        Raises:
            ValueError: If the observable's qubit count does not equal the number of target
                qubits, or if `target=None` and the observable's qubit count is not 1.


        Examples:
            >>> result_types.AdjointGradient(observable=observables.Z(0),
                                        parameters=["alpha", "beta"])
            >>> result_types.AdjointGradient(observable=observables.Z(),
                                        target=0, parameters=["alpha", "beta"])

            >>> tensor_product = observables.Y(0) @ observables.Z(1)
            >>> hamiltonian = observables.Y(0) @ observables.Z(1) + observables.H(0)
            >>> result_types.AdjointGradient(
            >>>     observable=tensor_product,
            >>>     parameters=["alpha", "beta"],
            >>> )
        """
        target_qubits = QubitSet(target if target is not None else observable.targets)
        super().__init__(
            ascii_symbols=[f"AdjointGradient({observable.ascii_symbols[0]})"] * len(target_qubits),
            observable=observable,
            target=target,
            parameters=parameters,
        )

    def _to_openqasm(self, serialization_properties: OpenQASMSerializationProperties) -> str:
        observable_ir = self.observable.to_ir(
            target=self._target,
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
        )

        pragma_parameters = ", ".join(self.parameters) if self.parameters else "all"

        return (
            f"#pragma braket result adjoint_gradient "
            f"expectation({observable_ir}) {pragma_parameters}"
        )

    @staticmethod
    @circuit.subroutine(register=True)
    def adjoint_gradient(
        observable: Observable,
        target: list[QubitSetInput] | None = None,
        parameters: list[str | FreeParameter] | None = None,
    ) -> ResultType:
        """Registers this function into the circuit class.

        Args:
            observable (Observable): The expectation value of this observable is the function
                against which parameters in the gradient are differentiated.
            target (list[QubitSetInput] | None): Target qubits that the result type is requested
                for. Each term in the target list should have the same number of qubits as the
                corresponding term in the observable. Default is `None`, which means the
                observable must operate only on 1 qubit and it is applied to all qubits
                in parallel.
            parameters (list[Union[str, FreeParameter]] | None): The free parameters in the circuit
                to differentiate with respect to. Default: `all`.

        Returns:
            ResultType: gradient computed via adjoint differentiation as a requested result type

        Examples:
            >>> alpha, beta = FreeParameter("alpha"), FreeParameter("beta")
            >>> circ = Circuit().h(0).h(1).rx(0, alpha).yy(0, 1, beta).adjoint_gradient(
            >>>     observable=observables.Z(0), parameters=[alpha, beta]
            >>> )
        """
        return ResultType.AdjointGradient(
            observable=observable, target=target, parameters=parameters
        )


ResultType.register_result_type(AdjointGradient)


class Amplitude(ResultType):
    """The amplitude of the specified quantum states as a requested result type.
    This is available on simulators only when `shots=0`.
    """

    def __init__(self, state: list[str]):
        """Initializes an `Amplitude`.

        Args:
            state (list[str]): list of quantum states as strings with "0" and "1"

        Raises:
            ValueError: If state is `None` or an empty list, or
                state is not a list of strings of '0' and '1'

        Examples:
            >>> result_types.Amplitude(state=["01", "10"])
        """
        if (
            not state
            or not isinstance(state, list)
            or not all(
                isinstance(amplitude, str) and re.fullmatch(r"^[01]+$", amplitude)
                for amplitude in state
            )
        ):
            raise ValueError(
                "A non-empty list of states must be specified in binary encoding e.g. ['01', '10']"
            )
        super().__init__(ascii_symbols=[f"Amplitude({','.join(state)})"])
        self._state = state

    @property
    def state(self) -> list[str]:
        return self._state

    def _to_jaqcd(self) -> ir.Amplitude:
        return ir.Amplitude.construct(states=self.state)

    def _to_openqasm(self, serialization_properties: OpenQASMSerializationProperties) -> str:
        states = ", ".join(f'"{state}"' for state in self.state)
        return f"#pragma braket result amplitude {states}"

    @staticmethod
    @circuit.subroutine(register=True)
    def amplitude(state: list[str]) -> ResultType:
        """Registers this function into the circuit class.

        Args:
            state (list[str]): list of quantum states as strings with "0" and "1"

        Returns:
            ResultType: state vector as a requested result type

        Examples:
            >>> circ = Circuit().amplitude(state=["01", "10"])
        """
        return ResultType.Amplitude(state=state)

    def __eq__(self, other: Amplitude):
        return self.state == other.state if isinstance(other, Amplitude) else False

    def __repr__(self):
        return f"Amplitude(state={self.state})"

    def __copy__(self):
        return type(self)(state=self.state)

    def __hash__(self) -> int:
        return super().__hash__()


ResultType.register_result_type(Amplitude)


class Probability(ResultType):
    """Probability in the computational basis as the requested result type.

    It can be the probability of all states if no targets are specified, or the marginal
    probability of a restricted set of states if only a subset of all qubits are specified as
    targets.

    For `shots>0`, this is calculated by measurements. For `shots=0`, this is supported
    only on simulators and represents the exact result.
    """

    def __init__(self, target: QubitSetInput | None = None):
        """Inits a `Probability`.

        Args:
            target (QubitSetInput | None): The target qubits that the
                result type is requested for. Default is `None`, which means all qubits for the
                circuit.

        Examples:
            >>> result_types.Probability(target=[0, 1])
        """
        self._target = QubitSet(target)
        ascii_symbols = ["Probability"] * len(self._target) if self._target else ["Probability"]
        super().__init__(ascii_symbols=ascii_symbols)

    @property
    def target(self) -> QubitSet:
        return self._target

    @target.setter
    def target(self, target: QubitSetInput) -> None:
        """Sets the target qubit set.

        Args:
            target (QubitSetInput): The target qubit set.
        """
        self._target = QubitSet(target)

    def _to_jaqcd(self) -> ir.Probability:
        if self.target:
            # convert qubits to int as required by the ir type
            return ir.Probability.construct(targets=[int(qubit) for qubit in self.target])
        return ir.Probability.construct()

    def _to_openqasm(self, serialization_properties: OpenQASMSerializationProperties) -> str:
        if not self.target:
            return "#pragma braket result probability all"
        targets = ", ".join(
            serialization_properties.format_target(int(target)) for target in self.target
        )
        return f"#pragma braket result probability {targets}"

    @staticmethod
    @circuit.subroutine(register=True)
    def probability(target: QubitSetInput | None = None) -> ResultType:
        """Registers this function into the circuit class.

        Args:
            target (QubitSetInput | None): The target qubits that the
                result type is requested for. Default is `None`, which means all qubits for the
                circuit.

        Returns:
            ResultType: probability as a requested result type

        Examples:
            >>> circ = Circuit().probability(target=[0, 1])
        """
        return ResultType.Probability(target=target)

    def __eq__(self, other: Probability) -> bool:
        return self.target == other.target if isinstance(other, Probability) else False

    def __repr__(self) -> str:
        return f"Probability(target={self.target})"

    def __copy__(self) -> Probability:
        return type(self)(target=self.target)

    def __hash__(self) -> int:
        return super().__hash__()


ResultType.register_result_type(Probability)


class Expectation(ObservableResultType):
    """Expectation of the specified target qubit set and observable as the requested result type.

    If no targets are specified, the observable must operate only on 1 qubit and it
    is applied to all qubits in parallel. Otherwise, the number of specified targets
    must be equivalent to the number of qubits the observable can be applied to.

    For `shots>0`, this is calculated by measurements. For `shots=0`, this is supported
    only by simulators and represents the exact result.

    See :mod:`braket.circuits.observables` module for all of the supported observables.
    """

    def __init__(self, observable: Observable, target: QubitSetInput | None = None):
        """Inits an `Expectation`.

        Args:
            observable (Observable): the observable for the result type
            target (QubitSetInput | None): Target qubits that the result type is requested for.
                If not provided, the observable's target will be used instead. If neither exist,
                then it is applied to all qubits in parallel; in this case the observable must
                operate only on 1 qubit.
                Default: `None`.

        Examples:
            >>> result_types.Expectation(observable=observables.Z(0))
            >>> result_types.Expectation(observable=observables.Z(), target=0)

            >>> tensor_product = observables.Y(0) @ observables.Z(1)
            >>> result_types.Expectation(observable=tensor_product)
        """
        super().__init__(
            ascii_symbols=[f"Expectation({obs_ascii})" for obs_ascii in observable.ascii_symbols],
            observable=observable,
            target=target,
        )

    def _to_jaqcd(self) -> ir.Expectation:
        if self.target:
            return ir.Expectation.construct(
                observable=self.observable.to_ir(), targets=[int(qubit) for qubit in self.target]
            )
        return ir.Expectation.construct(observable=self.observable.to_ir())

    def _to_openqasm(self, serialization_properties: OpenQASMSerializationProperties) -> str:
        observable_ir = self.observable.to_ir(
            target=self._target,
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
        )
        return f"#pragma braket result expectation {observable_ir}"

    @staticmethod
    @circuit.subroutine(register=True)
    def expectation(observable: Observable, target: QubitSetInput | None = None) -> ResultType:
        """Registers this function into the circuit class.

        Args:
            observable (Observable): the observable for the result type
            target (QubitSetInput | None): Target qubits that the
                result type is requested for. Default is `None`, which means the observable must
                operate only on 1 qubit and it is applied to all qubits in parallel.

        Returns:
            ResultType: expectation as a requested result type

        Examples:
            >>> circ = Circuit().expectation(observable=observables.Z(0))
        """
        return ResultType.Expectation(observable=observable, target=target)


ResultType.register_result_type(Expectation)


class Sample(ObservableResultType):
    """Sample of specified target qubit set and observable as the requested result type.

    If no targets are specified, the observable must operate only on 1 qubit and it
    is applied to all qubits in parallel. Otherwise, the number of specified targets
    must equal the number of qubits the observable can be applied to.

    This is only available for `shots>0`.

    See :mod:`braket.circuits.observables` module for all of the supported observables.
    """

    def __init__(self, observable: Observable, target: QubitSetInput | None = None):
        """Inits a `Sample`.

        Args:
            observable (Observable): the observable for the result type
            target (QubitSetInput | None): Target qubits that the result type is requested for.
                If not provided, the observable's target will be used instead. If neither exist,
                then it is applied to all qubits in parallel; in this case the observable must
                operate only on 1 qubit.
                Default: `None`.

        Examples:
            >>> result_types.Sample(observable=observables.Z(0))
            >>> result_types.Sample(observable=observables.Z(), target=0)

            >>> tensor_product = observables.Y(0) @ observables.Z(1)
            >>> result_types.Sample(observable=tensor_product)
        """
        super().__init__(
            ascii_symbols=[f"Sample({obs_ascii})" for obs_ascii in observable.ascii_symbols],
            observable=observable,
            target=target,
        )

    def _to_jaqcd(self) -> ir.Sample:
        if self.target:
            return ir.Sample.construct(
                observable=self.observable.to_ir(), targets=[int(qubit) for qubit in self.target]
            )
        return ir.Sample.construct(observable=self.observable.to_ir())

    def _to_openqasm(self, serialization_properties: OpenQASMSerializationProperties) -> str:
        observable_ir = self.observable.to_ir(
            target=self._target,
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
        )
        return f"#pragma braket result sample {observable_ir}"

    @staticmethod
    @circuit.subroutine(register=True)
    def sample(observable: Observable, target: QubitSetInput | None = None) -> ResultType:
        """Registers this function into the circuit class.

        Args:
            observable (Observable): the observable for the result type
            target (QubitSetInput | None): Target qubits that the
                result type is requested for. Default is `None`, which means the observable must
                operate only on 1 qubit and it is applied to all qubits in parallel.

        Returns:
            ResultType: sample as a requested result type

        Examples:
            >>> circ = Circuit().sample(observable=observables.Z(0))
        """
        return ResultType.Sample(observable=observable, target=target)


ResultType.register_result_type(Sample)


class Variance(ObservableResultType):
    """Variance of specified target qubit set and observable as the requested result type.

    If no targets are specified, the observable must operate only on 1 qubit and it
    is applied to all qubits in parallel. Otherwise, the number of targets specified
    must equal the number of qubits that the observable can be applied to.

    For `shots>0`, this is calculated by measurements. For `shots=0`, this is supported
    only by simulators and represents the exact result.

    See :mod:`braket.circuits.observables` module for all of the supported observables.
    """

    def __init__(self, observable: Observable, target: QubitSetInput | None = None):
        """Inits a `Variance`.

        Args:
            observable (Observable): the observable for the result type
            target (QubitSetInput | None): Target qubits that the result type is requested for.
                If not provided, the observable's target will be used instead. If neither exist,
                then it is applied to all qubits in parallel; in this case the observable must
                operate only on 1 qubit.
                Default: `None`.

        Raises:
            ValueError: If the observable's qubit count does not equal the number of target
                qubits, or if `target=None` and the observable's qubit count is not 1.

        Examples:
            >>> result_types.Variance(observable=observables.Z(0))
            >>> result_types.Variance(observable=observables.Z(), target=0)

            >>> tensor_product = observables.Y(0) @ observables.Z(1)
            >>> result_types.Variance(observable=tensor_product)
        """
        super().__init__(
            ascii_symbols=[f"Variance({obs_ascii})" for obs_ascii in observable.ascii_symbols],
            observable=observable,
            target=target,
        )

    def _to_jaqcd(self) -> ir.Variance:
        if self.target:
            return ir.Variance.construct(
                observable=self.observable.to_ir(), targets=[int(qubit) for qubit in self.target]
            )
        return ir.Variance.construct(observable=self.observable.to_ir())

    def _to_openqasm(self, serialization_properties: OpenQASMSerializationProperties) -> str:
        observable_ir = self.observable.to_ir(
            target=self._target,
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
        )
        return f"#pragma braket result variance {observable_ir}"

    @staticmethod
    @circuit.subroutine(register=True)
    def variance(observable: Observable, target: QubitSetInput | None = None) -> ResultType:
        """Registers this function into the circuit class.

        Args:
            observable (Observable): the observable for the result type
            target (QubitSetInput | None): Target qubits that the
                result type is requested for. Default is `None`, which means the observable must
                only operate on 1 qubit and it will be applied to all qubits in parallel

        Returns:
            ResultType: variance as a requested result type

        Examples:
            >>> circ = Circuit().variance(observable=observables.Z(0))
        """
        return ResultType.Variance(observable=observable, target=target)


ResultType.register_result_type(Variance)
