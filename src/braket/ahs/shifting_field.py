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

from braket.ahs.local_detuning import LocalDetuning

# The class `ShiftingField` is deprecated. Please use `LocalDetuning` instead.
# This file and class will be removed in a future version.
# We are retaining this now to avoid breaking backwards compatibility for users already
# utilizing this nomenclature.
ShiftingField = LocalDetuning
