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

from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from braket.ir.annealing import Problem
from braket.ir.jaqcd import Program


class BraketSimulator(ABC):
    """ An abstract simulator that locally runs a quantum task.

    The task can be either a circuit-based program or an annealing task,
    specified by the given IR.

    For users creating their own simulator: to register a simulator so the
    Braket SDK recognizes its name, the name and class must added as an
    entry point for "braket.simulators". This is done by adding an entry to
    entry_points in the simulator package's setup.py:

    >>> entry_points = {
    >>>     "braket.simulators": [
    >>>         "backend_name = <backend_class>"
    >>>     ]
    >>> }
    """

    # TODO: Move this class to the local simulator repo and take a dependency on it
    # As such, this will not depend on any SDK classes.

    # TODO: Update to use new simulate() method

    @abstractmethod
    def run(self, ir: Union[Program, Problem], *args, **kwargs) -> Dict[str, Any]:
        """ Run the task specified by the given IR.

        Extra arguments will contain any additional information necessary to run the task,
        such as number of qubits.

        Args:
            ir (Union[Program, Problem]): The IR representation of the program

        Returns:
            Dict[str, Any]: A dict containing the results of the simulation.
            In order to work with braket-python-sdk, the format of the JSON dict should
            match that needed by GateModelQuantumTaskResult or AnnealingQuantumTaskResult
            from the SDK, depending on the type of task.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def properties(self) -> Dict[str, Any]:
        """ Dict[str, Any]: Properties of the BraketSimulator device. """
        raise NotImplementedError()
