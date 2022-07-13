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
import urllib.request
from functools import lru_cache


class Pricing:
    def __init__(self):
        self._price_list = []

    def get_prices(self):
        # Using AWS Pricing Bulk API. Format for the response is described at
        # https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/reading-an-offer.html
        response = urllib.request.urlopen(
            "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBraket/current/index.csv"
        )
        text_response = io.TextIOWrapper(response)
        # Data starts on line 6
        for _ in range(5):
            text_response.readline()
        self._price_list = list(csv.DictReader(text_response))

    @lru_cache()
    def price_search(self, **kwargs):
        if not self._price_list:
            self.get_prices()
        return [
            entry for entry in self._price_list if all(entry[k] == v for k, v in kwargs.items())
        ]


_pricing = Pricing()
price_search = _pricing.price_search
