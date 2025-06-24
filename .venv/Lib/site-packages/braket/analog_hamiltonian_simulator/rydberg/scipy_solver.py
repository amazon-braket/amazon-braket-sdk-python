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

import time

import numpy as np
import scipy.integrate
import scipy.sparse

from braket.analog_hamiltonian_simulator.rydberg.rydberg_simulator_helpers import (
    _apply_hamiltonian,
    _get_ops_coefs,
    _print_progress_bar,
)
from braket.ir.ahs.program_v1 import Program


def scipy_integrate_ode_run(
    program: Program,
    configurations: list[str],
    simulation_times: list[float],
    rydberg_interaction_coef: float,
    progress_bar: bool = False,
    atol: float = 1e-8,
    rtol: float = 1e-6,
    solver_method: str = "adams",
    order: int = 12,
    nsteps: int = 1000,
    first_step: int = 0,
    max_step: int = 0,
    min_step: int = 0,
) -> np.ndarray:
    """
    Solves the Schrödinger equation with `scipy.integrate.ode`

    Args:
        program (Program): An analog simulation Hamiltonian for the Rydberg system simulated
        configurations (list[str]): The list of configurations that comply with the
            blockade approximation.
        simulation_times (list[float]): The list of time points
        rydberg_interaction_coef (float): The interaction coefficient
        progress_bar (bool): If true, a progress bar will be printed during the simulation.
            Default: False
        atol (float): Absolute tolerance for solution. Default: 1e-8
        rtol (float): Relative tolerance for solution. Default: 1e-6
        solver_method (str): Which solver to use, `adams` for non-stiff problems or `bdf`
            for stiff problems. Default: "adams"
        order (int): Maximum order used by the integrator, order <= 12 for Adams, <= 5 for BDF.
            Default: 12
        nsteps (int): Maximum number of (internally defined) steps allowed during one call to
            the solver. Default: 1000
        first_step (int): Default: 0
        max_step (int): Limits for the step sizes used by the integrator. Default: 0
        min_step (int): Default: 0

    Returns:
        ndarray: The list of all the intermediate states in the simulation.

    For more information, please refer to the documentation for `scipy.integrate.ode`
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.ode.html

    """

    operators_coefficients = _get_ops_coefs(
        program, configurations, rydberg_interaction_coef, simulation_times
    )

    # Define the initial state for the simulation
    size_hilbert_space = len(configurations)
    state = np.zeros(size_hilbert_space)
    state[0] = 1

    states = [state]  # The history of all intermediate states

    if len(simulation_times) == 1:
        return states

    dt = simulation_times[1] - simulation_times[0]  # The time step for the simulation

    # Define the function to be integrated, e.g. dy/dt = f(t, y).
    # Note that we we will use the index of the time point,
    # instead of time, for f(t, y).
    def f(index_time: int, y: np.ndarray) -> scipy.sparse.csr_matrix:
        return -1j * dt * _apply_hamiltonian(index_time, operators_coefficients, y)

    integrator = scipy.integrate.ode(f)
    integrator.set_integrator(
        "zvode",
        atol=atol,
        rtol=rtol,
        method=solver_method,
        order=order,
        nsteps=nsteps,
        first_step=first_step,
        max_step=max_step,
        min_step=min_step,
    )

    if progress_bar:  # print a lightweight progress bar
        start_time = time.time()

    for index_time in range(len(simulation_times) - 1):
        if progress_bar:  # print a lightweight progress bar
            _print_progress_bar(len(simulation_times), index_time, start_time)

        if not integrator.successful():
            raise Exception(
                "ODE integration error: Try to increase "
                "the allowed number of substeps by increasing "
                "the parameter `nsteps`."
            )

        integrator.set_initial_value(state, index_time)
        integrator.integrate(index_time + 1)

        # get the current state, and normalize it
        state = integrator.y
        state /= np.linalg.norm(state)  # normalize the state
        states.append(state)

    return states
