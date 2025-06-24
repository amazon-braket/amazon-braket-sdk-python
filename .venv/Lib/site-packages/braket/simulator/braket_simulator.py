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

from abc import ABC, abstractmethod
from collections.abc import Sequence
from multiprocessing import Pool
from os import cpu_count
from typing import Optional, Union

from braket.device_schema import DeviceCapabilities
from braket.ir.ahs import Program as AHSProgram
from braket.ir.jaqcd import Program as JaqcdProgram
from braket.ir.openqasm import Program as OQ3Program
from braket.task_result import AnalogHamiltonianSimulationTaskResult, GateModelTaskResult


class BraketSimulator(ABC):
    """An abstract simulator that locally runs a quantum task.

    The task can be either a quantum circuit defined in an OpenQASM or JAQCD program,
    or an analog Hamiltonian simulation (AHS) program.

    For users creating their own simulator: to register a simulator so the
    Braket SDK recognizes its name, the name and class must be added as an
    entry point for "braket.simulators". This is done by adding an entry to
    entry_points in the simulator package's setup.py:

    >>> entry_points = {
    >>>     "braket.simulators": [
    >>>         "backend_name = <backend_class>"
    >>>     ]
    >>> }
    """

    DEVICE_ID = None

    @abstractmethod
    def run(
        self, ir: Union[OQ3Program, AHSProgram, JaqcdProgram], *args, **kwargs
    ) -> Union[GateModelTaskResult, AnalogHamiltonianSimulationTaskResult]:
        """
        Run the task specified by the given IR.

        Extra arguments will contain any additional information necessary to run the task,
        such as the extra parameters for AHS simulations.

        Args:
            ir (Union[OQ3Program, AHSProgram, JaqcdProgram]): The IR representation of the program

        Returns:
            Union[GateModelTaskResult, AnalogHamiltonianSimulationTaskResult]: An object
            representing the results of the simulation.
        """

    def run_multiple(
        self,
        programs: Sequence[Union[OQ3Program, AHSProgram, JaqcdProgram]],
        max_parallel: Optional[int] = None,
        *args,
        **kwargs,
    ) -> list[Union[GateModelTaskResult, AnalogHamiltonianSimulationTaskResult]]:
        """
        Run the tasks specified by the given IR programs.

        Extra arguments will contain any additional information necessary to run the tasks,
        such as the extra parameters for AHS simulations.

        Args:
            programs (Sequence[Union[OQ3Program, AHSProgram, JaqcdProgram]]): The IR representations
                of the programs
            max_parallel (Optional[int]): The maximum number of programs to run in parallel.
                Default is the number of logical CPUs.

        Returns:
            list[Union[GateModelTaskResult, AnalogHamiltonianSimulationTaskResult]]: A list of
            result objects, with the ith object being the result of the ith program.
        """
        max_parallel = max_parallel or cpu_count()
        with Pool(min(max_parallel, len(programs))) as pool:
            param_list = [(program, args, kwargs) for program in programs]
            results = pool.starmap(self._run_wrapped, param_list)
        return results

    def _run_wrapped(
        self, ir: Union[OQ3Program, AHSProgram, JaqcdProgram], args, kwargs
    ):  # pragma: no cover
        return self.run(ir, *args, **kwargs)

    @property
    @abstractmethod
    def properties(self) -> DeviceCapabilities:
        """DeviceCapabilities: Properties of the device."""
