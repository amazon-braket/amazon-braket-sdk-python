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

import aqx.qdk.ipython_utils as ipython_utils

# Apply nest_asyncio if currently running within Jupyter. This ensures anything that uses
# asyncio will run in Jupyter without any issues.
#
# Inspired by https://github.com/ipython/ipython/issues/11694 and
# https://github.com/jupyter/notebook/issues/3397#issuecomment-419386811
if ipython_utils.running_in_jupyter():
    import nest_asyncio

    nest_asyncio.apply()
