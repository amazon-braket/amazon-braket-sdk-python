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

# TODO: This function is defined based on the defintiion in the design doc,
# and is subject to change.


def retrieve(framework="base", framework_version="1.8", py_version="3.7"):
    """Retrieves the ECR URI for the Docker image matching the given arguments.

    Args:
        framework (str): The name of the framework or algorithm.
        framework_version (str): The framework or algorithm version. This is required if there is
            more than one supported version for the given framework or algorithm.
        py_version (str, optional): [description]. The Python version. This is required if there is
            more than one supported Python version for the given framework version.

    Returns:
        str: the ECR URI for the corresponding SageMaker Docker image.

    Raises:
        ValueError: If the combination of arguments specified is not supported.
    """
