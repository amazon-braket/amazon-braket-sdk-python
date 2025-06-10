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

from braket.device_schema.result_type import ResultType


DEFAULT_SUPPORTED_RESULT_TYPES = [
    ResultType(name='Sample', observables=['x', 'y', 'z', 'h', 'i'], minShots=1, maxShots=20000),
    ResultType(name='Expectation', observables=['x', 'y', 'z', 'h', 'i'], minShots=1, maxShots=20000),
    ResultType(name='Variance', observables=['x', 'y', 'z', 'h', 'i'], minShots=1, maxShots=20000),
    ResultType(name='Probability', observables=None, minShots=1, maxShots=20000)
]