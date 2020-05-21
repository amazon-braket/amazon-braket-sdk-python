from typing import Counter, Dict, Tuple


def assert_measurement_probabilities(
    probabilities: Dict[str, float], tolerances: Dict[str, Tuple[float, float]]
):
    for bitstring in probabilities:
        tolerance = tolerances[bitstring]
        assert tolerance[0] < probabilities[bitstring] < tolerance[1]


def assert_measurement_counts_most_common(measurement_counts: Counter, bitstring: str):
    assert measurement_counts.most_common(1)[0][0] == bitstring
