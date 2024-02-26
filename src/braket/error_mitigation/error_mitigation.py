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

from braket.device_schema import error_mitigation


class ErrorMitigation:
    def serialize(self) -> list[error_mitigation.ErrorMitigationScheme]:
        """This returns a list of service-readable error mitigation
        scheme descriptions.

        Returns:
            list[ErrorMitigationScheme]: A list of service-readable error
            mitigation scheme descriptions.

        Raises:
            NotImplementedError: Not implemented in the base class.
        """
        raise NotImplementedError("serialize is not implemented.")
