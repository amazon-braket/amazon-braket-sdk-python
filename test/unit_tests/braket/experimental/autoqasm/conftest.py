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

"""Test fixtures shared among the tests."""

from collections.abc import Callable

import pytest

import braket.experimental.autoqasm as aq
from braket.experimental.autoqasm.instructions import cnot, h


@pytest.fixture
def empty_subroutine() -> Callable:
    """Empty subroutine fixture.

    Returns:
        Callable: the aq program.
    """

    @aq.subroutine
    def empty_function() -> None:
        """A function that does nothing."""
        pass

    return empty_function


@pytest.fixture
def empty_program() -> Callable:
    """Empty program fixture.

    Returns:
        Callable: the aq program.
    """

    @aq.main
    def empty_function() -> None:
        """A function that does nothing."""
        pass

    return empty_function


@pytest.fixture
def bell_state_subroutine() -> Callable:
    """Bell state preparation subroutine fixture.

    Returns:
        Callable: the aq program.
    """

    @aq.subroutine
    def bell_state() -> None:
        """A function that generates a two-qubit Bell state."""
        h(0)
        cnot(0, 1)

    return bell_state


@pytest.fixture
def bell_state_program() -> Callable:
    """Bell state preparation program fixture.

    Returns:
        Callable: the aq program.
    """

    @aq.main
    def bell_state() -> None:
        """A function that generates a two-qubit Bell state."""
        h(0)
        cnot(0, 1)

    return bell_state


@pytest.fixture
def physical_bell_subroutine() -> Callable:
    """Physical bell state preparation program fixture.

    Returns:
        Callable: the aq program.
    """

    @aq.subroutine
    def physical_bell() -> None:
        """A function that generates a two-qubit Bell state on particular qubits."""
        h("$0")
        cnot("$0", "$5")

    return physical_bell


@pytest.fixture
def physical_bell_program() -> Callable:
    """Physical bell state preparation program fixture.

    Returns:
        Callable: the aq program.
    """

    @aq.main
    def physical_bell() -> None:
        """A function that generates a two-qubit Bell state on particular qubits."""
        h("$0")
        cnot("$0", "$5")

    return physical_bell
