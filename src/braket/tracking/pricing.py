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

from __future__ import annotations

import csv
import io
import os
from functools import lru_cache

import urllib3


class Pricing:
    def __init__(self):
        self._price_list = []

    def get_prices(self) -> None:
        """Retrieves the price list."""
        # Using AWS Pricing Bulk API. Format for the response is described at
        # https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/reading-an-offer.html

        http = urllib3.PoolManager()
        price_url = os.environ.get(
            "BRAKET_PRICE_OFFERS_URL",
            "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBraket/current/index.csv",
        )
        response = http.request(
            "GET",
            price_url,
            preload_content=False,
        )
        response.auto_close = False

        text_response = io.TextIOWrapper(response, encoding="utf-8")

        # Data starts on line 6
        #
        # > The first five rows of the CSV are the metadata for the offer file. The sixth row has
        # > all the column names for the products and their attributes...
        # https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/reading-an-offer.html#csv
        for _ in range(5):
            text_response.readline()
        self._price_list = list(csv.DictReader(text_response))

    @lru_cache  # noqa: B019
    def price_search(self, **kwargs: str) -> list[dict[str, str]]:
        """Searches the price list for a given set of parameters.

        Args:
            **kwargs (str): Arbitrary keyword arguments.

        Returns:
            list[dict[str, str]]: The price list.
        """
        if not self._price_list:
            self.get_prices()
        return [
            entry for entry in self._price_list if all(entry[k] == v for k, v in kwargs.items())
        ]


_pricing = Pricing()
price_search = _pricing.price_search
