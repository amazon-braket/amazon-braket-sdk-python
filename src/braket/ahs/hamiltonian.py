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

from typing import List, Optional


class Hamiltonian:
    def __init__(self, terms: Optional[List[Hamiltonian]] = None):
        self._terms = terms or []

    @property
    def terms(self) -> List[Hamiltonian]:
        return self._terms

    def __iadd__(self, other: Hamiltonian) -> Hamiltonian:
        if type(self) is not Hamiltonian:
            raise ValueError(f"Unable to modify Hamiltonian of type {type(self)}")
        self._terms.extend(other.terms)
        return self

    def __add__(self, other: Hamiltonian) -> Hamiltonian:
        terms = []
        terms.extend(self.terms)
        terms.extend(other.terms)
        return Hamiltonian(terms)
