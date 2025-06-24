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

from braket.analog_hamiltonian_simulator.rydberg.constants import FIELD_UNIT, SPACE_UNIT, TIME_UNIT
from braket.ir.ahs.physical_field import PhysicalField
from braket.ir.ahs.program_v1 import Program


def convert_unit(program: Program) -> Program:
    """
    For a given program, convert the SI units to units that are more
    suitable for local simulator

    Args:
        program (Program): An analog simulation program for Rydberg system

    Returns:
        Program: A new Program object with units converted for simulation
    """

    setup = program.setup
    sites = setup.ahs_register.sites
    new_sites = [[float(site[0]) / SPACE_UNIT, float(site[1]) / SPACE_UNIT] for site in sites]
    new_setup = {"ahs_register": {"sites": new_sites, "filling": setup.ahs_register.filling}}

    hamiltonian = program.hamiltonian
    driving_fields = hamiltonian.drivingFields
    local_detunings = hamiltonian.localDetuning

    new_driving_fields, new_local_detunings = [], []
    for driving_field in driving_fields:
        new_amplitude = _convert_unit_for_field(driving_field.amplitude)
        new_phase = _convert_unit_for_field(driving_field.phase, False)
        new_detuning = _convert_unit_for_field(driving_field.detuning)
        new_driving_field = {
            "amplitude": new_amplitude,
            "phase": new_phase,
            "detuning": new_detuning,
        }
        new_driving_fields.append(new_driving_field)

    for local_detuning in local_detunings:
        new_magnitude = _convert_unit_for_field(local_detuning.magnitude)
        new_local_detuning = {"magnitude": new_magnitude}
        new_local_detunings.append(new_local_detuning)

    new_hamiltonian = {"drivingFields": new_driving_fields, "localDetuning": new_local_detunings}

    new_program = Program(
        setup=new_setup,
        hamiltonian=new_hamiltonian,
    )
    return new_program


def _convert_unit_for_field(field: PhysicalField, convertvalues: bool = True) -> dict:
    """
    For a given field, convert the unit of time from second to microsecond,
    and convert the unit of values from Hz to MHz if `convertvalues` =True

    Args:
        field (PhysicalField): The physical field for converting unit
        convertvalues (bool): If true then convert the unit of values from Hz to MHz,
            otherwise convert the unit of time from second to microsecond. Default: True.

    Returns:
        dict: The field with units converted

    """
    times = [float(time) / TIME_UNIT for time in field.time_series.times]

    if convertvalues:
        values = [float(value) / FIELD_UNIT for value in field.time_series.values]
    else:
        values = [float(value) for value in field.time_series.values]

    new_field = {"pattern": field.pattern, "time_series": {"times": times, "values": values}}

    return new_field
