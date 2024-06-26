import numpy as np
import pytest

from braket.circuits import Circuit
from braket.emulators.emulator_passes import QubitCountCriterion


@pytest.mark.parametrize(
    "qubit_count,circuit",
    [
        (1, Circuit()),
        (10, Circuit().add_verbatim_box(Circuit())),
        (1, Circuit().z(0)),
        (1, Circuit().z(3).x(3)),
        (2, Circuit().cnot(0, 1).swap(1, 0)),
        (2, Circuit().z(0).add_verbatim_box(Circuit().cnot(0, 4)).yy(0, 4, np.pi / 4)),
        (50, Circuit().i(range(50)).measure(range(50))),
    ],
)
def test_valid_circuits(qubit_count, circuit):
    """
    QubitCountCriterion should not raise any errors when validating these circuits.
    """
    QubitCountCriterion(qubit_count=qubit_count).validate(circuit)


@pytest.mark.parametrize("qubit_count", [0, -1])
def test_invalid_instantiation(qubit_count):
    with pytest.raises(ValueError):
        QubitCountCriterion(qubit_count)


@pytest.mark.parametrize(
    "qubit_count,circuit",
    [
        (1, Circuit().cnot(0, 1)),
        (2, Circuit().cnot(0, 1).x(2)),
        (50, Circuit().i(range(50)).measure(range(50)).measure(50)),
    ],
)
def test_invalid_circuits(qubit_count, circuit):
    with pytest.raises(
        ValueError,
        match=f"Circuit must use at most {qubit_count} qubits, \
            but uses {circuit.qubit_count} qubits.",
    ):
        QubitCountCriterion(qubit_count).validate(circuit)
