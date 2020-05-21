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

from typing import Counter, Dict, Tuple


def assert_measurement_probabilities(
    probabilities: Dict[str, float], tolerances: Dict[str, Tuple[float, float]]
):
    for bitstring in probabilities:
        tolerance = tolerances[bitstring]
        assert tolerance[0] < probabilities[bitstring] < tolerance[1]


def assert_measurement_counts_most_common(measurement_counts: Counter, bitstring: str):
    assert measurement_counts.most_common(1)[0][0] == bitstring
