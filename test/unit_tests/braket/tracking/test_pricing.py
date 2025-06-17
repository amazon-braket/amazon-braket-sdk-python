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

import pytest

from braket.tracking.pricing import Pricing


@pytest.fixture
def mock_http():
    with patch("urllib3.PoolManager") as http_mock:
        http_mock().request.return_value = io.BytesIO(
            b"""line1
line2
line3
line4
line5
A,B
1,1
1,2
"""
        )
        yield http_mock()


def test_search_prices(mock_http):
    pricer = Pricing()
    assert pricer.price_search(A="0") == []
    assert pricer.price_search(A="1", B="1") == [{"A": "1", "B": "1"}]
    assert pricer.price_search(A="1") == [{"A": "1", "B": "1"}, {"A": "1", "B": "2"}]


@patch.dict("os.environ", {"BRAKET_PRICE_OFFERS_URL": "https://myurl"})
def test_price_offer_env_var(mock_http):
    pricer = Pricing()
    pricer.get_prices()

    mock_http.request.assert_called_with("GET", "https://myurl", preload_content=False)
