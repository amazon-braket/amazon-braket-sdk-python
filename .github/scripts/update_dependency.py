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

import fileinput
from pathlib import Path

# Here we replace the `amazon-braket-sdk` dependency to point to the file system; otherwise
# pip will install them separately, allowing it to override the version of
# any mutual dependencies with the sdk. By pointing to the file system, pip will be
# forced to reconcile the dependencies in pyproject.toml with the dependencies of the sdk,
# and raise an error if there are conflicts. While we can't do this for every upstream
# dependency, we can do this for the ones we own to make sure that when the sdk updates
# its dependencies, these upstream github repos will not be impacted.

package = "amazon-braket-sdk"
path = Path.cwd().parent.resolve()

with fileinput.input("pyproject.toml", inplace=True) as f:
    for line in f:
        # Update the amazon-braket-sdk dependency in pyproject.toml to use the local path. This
        # would help catch conflicts during the installation process.
        replaced_line = (
            line if package not in line else f'    "{package} @ file://{path}/{package}-python",\n'
        )
        print(replaced_line, end="")
