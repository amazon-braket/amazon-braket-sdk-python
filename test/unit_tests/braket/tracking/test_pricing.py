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


import io
from unittest.mock import patch

from braket.tracking.pricing import Pricing


@patch("urllib.request.urlopen")
@patch("io.TextIOWrapper")
def test_search_prices(mock_text, mock_url):
    mock_text.return_value = io.StringIO(
        """line1
line2
line3
line4
line5
A,B
1,1
1,2
"""
    )
    pricer = Pricing()
    assert pricer.price_search(A="0") == []
    assert pricer.price_search(A="1", B="1") == [{"A": "1", "B": "1"}]
    assert pricer.price_search(A="1") == [{"A": "1", "B": "1"}, {"A": "1", "B": "2"}]
