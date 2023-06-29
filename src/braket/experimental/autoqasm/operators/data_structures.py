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


"""Operators for other data structures (e.g. list)."""

from typing import Iterable, Optional


def new_list(iterable: Optional[Iterable] = None) -> list:
    """The list constructor

    Args:
        iterable (Optional[Iterable]): Optional elements to fill the list with. Defaults to None.

    Returns:
        list: A list-like object. The exact return value depends on the initial elements.
    """
    return list(iterable) if iterable else []
