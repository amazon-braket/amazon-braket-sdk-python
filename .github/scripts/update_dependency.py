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

package = "amazon-braket-sdk"
path = Path.cwd().parent.resolve()

for line in fileinput.input("setup.py", inplace=True):
    # Update the `package` dependency to use the local path. This would help catch conflicts during
    # the installation process
    replaced_line = (
        line if package not in line else f'"{package} @ file://{path}/{package}-python",\n'
    )
    print(replaced_line, end="")
