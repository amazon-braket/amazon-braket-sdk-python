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

from abc import abstractmethod

from braket.circuits.noise_model.criteria import Criteria
from braket.circuits.result_type import ResultType


class ResultTypeCriteria(Criteria):
    """Criteria that implement these methods may be used to determine readout noise."""

    @abstractmethod
    def result_type_matches(self, result_type: ResultType) -> bool:
        """Returns true if a result type matches the criteria.

        Args:
            result_type (ResultType): A result type or list of result types to match.
        Returns:
            bool: True if the result type matches the criteria.
        """
        raise NotImplementedError
