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

from decimal import Decimal
from typing import Annotated, Optional

from pydantic.v1 import BaseModel, Field

from braket.schema_common import BraketSchemaBase, BraketSchemaHeader


class Area(BaseModel):
    """
    The area of the FOV
    Attributes:
        width (Decimal): Largest allowed difference between x
            coordinates of any two sites (measured in meters)
        height (Decimal): Largest allowed difference between y
            coordinates of any two sites (measured in meters)
    """

    width: Decimal
    height: Decimal


class Geometry(BaseModel):
    """
    Spacing or number of sites or rows
    Attributes:
        spacingRadialMin (Decimal): Minimum radial spacing between any
            two sites in the lattice (measured in meters)
        spacingVerticalMin (Decimal): Minimum spacing between any two
            rows in the lattice (measured in meters)
        positionResolution (Decimal): Resolution with which site positions
            can be specified (measured in meters)
        numberSitesMax (int): Maximum number of sites that can be placed
            in the lattice
    """

    spacingRadialMin: Decimal
    spacingVerticalMin: Decimal
    positionResolution: Decimal
    numberSitesMax: int


class Lattice(BaseModel):
    """
    Spacing or number of sites or rows
    Attributes:
        area : The rectangular area available for arranging atomic sites
        geometry : Limitations of atomic site arrangements
    """

    area: Area
    geometry: Geometry


class RydbergGlobal(BaseModel):
    """
    Constraints for the parameters of the driving field that drives the
        ground-to-Rydberg transition uniformly on all atoms
    Attributes:
        rabiFrequencyRange (tuple[Decimal,Decimal]): Achievable Rabi frequency range for the global
            Rydberg drive waveform (measured in rad/s)
        rabiFrequencyResolution (Decimal): Resolution with which global Rabi frequency amplitude
            can be specified (measured in rad/s)
        rabiFrequencySlewRateMax (Decimal): Maximum slew rate for changing the global Rabi
            frequency (measured in (rad/s)/s)
        detuningRange(tuple[Decimal,Decimal]): Achievable detuning range for the global Rydberg
            pulse (measured in rad/s)
        detuningResolution(Decimal): Resolution with which global detuning can be specified
            (measured in rad/s)
        detuningSlewRateMax (Decimal): Maximum slew rate for detuning (measured in (rad/s)/s)
        phaseRange(tuple[Decimal,Decimal]): Achievable phase range for the global Rydberg pulse
            (measured in rad)
        phaseResolution(Decimal): Resolution with which global Rabi frequency phase can be
            specified (measured in rad)
        timeResolution(Decimal): Resolution with which times for global Rydberg drive parameters
            can be specified (measured in s)
        timeDeltaMin(Decimal): Minimum time step with which times for global Rydberg drive
            parameters can be specified (measured in s)
        timeMin (Decimal): Minimum duration of Rydberg drive (measured in s)
        timeMax (Decimal): Maximum duration of Rydberg drive (measured in s) Note: This may be
            longer than the T2 coherence time.
    """

    rabiFrequencyRange: tuple[Decimal, Decimal]
    rabiFrequencyResolution: Decimal
    rabiFrequencySlewRateMax: Decimal
    detuningRange: tuple[Decimal, Decimal]
    detuningResolution: Decimal
    detuningSlewRateMax: Decimal
    phaseRange: tuple[Decimal, Decimal]
    phaseResolution: Decimal
    timeResolution: Decimal
    timeDeltaMin: Decimal
    timeMin: Decimal
    timeMax: Decimal


class RydbergLocal(BaseModel):
    """
    Constraints for the parameters of the local detuning
    Attributes:
        detuningRange(tuple[Decimal,Decimal]):
            Achievable detuning range for the local detuning pattern (measured in rad/s)
        detuningSlewRateMax(Decimal):
            Maximum slew rate for changing the local detuning (measured in (rad/s)/s)
        siteCoefficientRange(tuple[Decimal,Decimal]):
            Achievable site coefficient range for the local detuning pattern (unitless)
        numberLocalDetuningSitesMax(Decimal):
            Maximum number of sites available for the local detuning pattern
        spacingRadialMin(Decimal):
            Minimum radial spacing between any two sites with non-zero local detuning
            (measured in meter)
        timeResolution(Decimal):
            Resolution with which times for local detuning time series can be specified
            (measured in s)
        timeDeltaMin(Decimal):
            Minimum step between times for local detuning time series (measured in s)
    """

    detuningRange: tuple[Decimal, Decimal]
    detuningSlewRateMax: Decimal
    siteCoefficientRange: tuple[Decimal, Decimal]
    numberLocalDetuningSitesMax: Decimal
    spacingRadialMin: Decimal
    timeResolution: Decimal
    timeDeltaMin: Decimal


class Rydberg(BaseModel):
    """
    Parameters determining the limitations of the Rydberg Hamiltonian
    Attributes:
        c6Coefficient (Decimal): Rydberg-Rydberg C6 interaction coefficient (measured in
            (rad/s)*m^6)
        rydbergGlobal (RydbergGlobal): Rydberg Global
        rydbergLocal (Optional[RydbergLocal]): Rydberg Local. Defaults to None.
    """

    c6Coefficient: Decimal
    rydbergGlobal: RydbergGlobal
    rydbergLocal: Optional[RydbergLocal] = None


class PerformanceLattice(BaseModel):
    """
    Uncertainties of atomic site arrangements
    Attributes:
        positionErrorAbs (Decimal): Total error of the atom position during coherent evolution
            relative to the lab frame over the course of a 4-microsecond quantum program; it
            combines lattice site position and thermal atom position errors. (measured in meters)
        sitePositionError (Decimal): Systematic, pattern-dependent error between specified and
            actual lattice site positions. (measured in meters)
        atomPositionError (Decimal): Random error in the atom position during coherent evolution as
            a result of thermal motion over the course of a 4-microsecond quantum program.
            (measured in meters)
        fillingErrorTypical (Annotated[Decimal, Field(ge=0, le=1)]): Typical probability of failing
            to occupy a site specified by user as 'filled'. These probabilities are dependent on
            the pattern and site position within the pattern. Normalized to 1.
        fillingErrorWorst (Annotated[Decimal, Field(ge=0, le=1)]): Worst-case probability of
            failing to occupy a site specified by user as 'filled'. Upper bound that includes the
            pattern-dependence and site position dependence. Normalized to 1.
        vacancyErrorTypical (Annotated[Decimal, Field(ge=0, le=1)]): Typical probability of
            erroneously filling a site specified by user as 'unfilled'. These probabilities can be
            dependent on the pattern and site position within the pattern, and can change slightly
            with time. Normalized to 1.
        vacancyErrorWorst (Annotated[Decimal, Field(ge=0, le=1)]): Worst-case probability of
            erroneously filling a site specified by user as 'unfilled'. Upper bound that includes
            the pattern-dependence, site position dependence and time-variation of this
            probability. Normalized to 1.
        atomLossProbabilityTypical (Annotated[Decimal, Field(ge=0, le=1)]): Typical probability of
            atom loss from a filled site over the course of a 4-microsecond quantum program between
            the first (“pre-sequence”) and second (“post-sequence”) image. These probabilities can
            be dependent on the pattern and site position within the pattern, and can change
            slightly with time. Normalized to 1.
        atomLossProbabilityWorst (Annotated[Decimal, Field(ge=0, le=1)]): Worst-case probability of
            atom loss from a filled site over the course of a 4-microsecond quantum program between
            the first (“pre-sequence”) and second (“post-sequence”) image. Upper bound that
            includes the pattern-dependence, site position dependence and time-varition of this
            probability. Normalized to 1.
        atomCaptureProbabilityTypical (Annotated[Decimal, Field(ge=0, le=1)]): Typical probability
            of atom capture into an empty site over the course of a 4-microsecond quantum program
            between the first (“pre-sequence”) and second (“post-sequence”) image. These
            probabilities can be dependent on the pattern and site position within the pattern, and
            can change slightly with time. Normalized to 1.
        atomCaptureProbabilityWorst (Annotated[Decimal, Field(ge=0, le=1)]): Worst-case probability
            of atom capture into an empty site over the course of a 4-microsecond quantum program
            between the first (“pre-sequence”) and second (“post-sequence”) image. Upper bound that
            includes the pattern-dependence, site position dependence and time-variation of this
            probability. Normalized to 1.
        atomDetectionErrorFalsePositiveTypical (Annotated[Decimal, Field(ge=0, le=1)]): Typical
            probability of a false-positive atom detection error. These probabilities can be
            dependent on the pattern and site position within the pattern, and can change slightly
            with time. Normalized to 1.
        atomDetectionErrorFalsePositiveWorst (Annotated[Decimal, Field(ge=0, le=1)]): Worst-case
            probability of a false-positive atom detection error. Upper bound that includes the
            pattern-dependence, site position dependence and time-variation of this probability.
            Normalized to 1.
        atomDetectionErrorFalseNegativeTypical (Annotated[Decimal, Field(ge=0, le=1)]): Typical
            probability of a false-negative atom detection error. These probabilities can be
            dependent on the pattern and site position within the pattern, and can change slightly
            with time. Normalized to 1.
        atomDetectionErrorFalseNegativeWorst (Annotated[Decimal, Field(ge=0, le=1)]): Worst-case
            probability of a false-negative atom detection error. Upper bound that includes the
            pattern-dependence, site position dependence and time-variation of this probability.
            Normalized to 1.
    """

    positionErrorAbs: Decimal
    sitePositionError: Decimal
    atomPositionError: Decimal
    fillingErrorTypical: Annotated[Decimal, Field(ge=0, le=1)]
    fillingErrorWorst: Annotated[Decimal, Field(ge=0, le=1)]
    vacancyErrorTypical: Annotated[Decimal, Field(ge=0, le=1)]
    vacancyErrorWorst: Annotated[Decimal, Field(ge=0, le=1)]
    atomLossProbabilityTypical: Annotated[Decimal, Field(ge=0, le=1)]
    atomLossProbabilityWorst: Annotated[Decimal, Field(ge=0, le=1)]
    atomCaptureProbabilityTypical: Annotated[Decimal, Field(ge=0, le=1)]
    atomCaptureProbabilityWorst: Annotated[Decimal, Field(ge=0, le=1)]
    atomDetectionErrorFalsePositiveTypical: Annotated[Decimal, Field(ge=0, le=1)]
    atomDetectionErrorFalsePositiveWorst: Annotated[Decimal, Field(ge=0, le=1)]
    atomDetectionErrorFalseNegativeTypical: Annotated[Decimal, Field(ge=0, le=1)]
    atomDetectionErrorFalseNegativeWorst: Annotated[Decimal, Field(ge=0, le=1)]


class RabiCorrection(BaseModel):
    """
    Correction factors for calculating the fraction of the expected Rabi oscillation frequency as a
        function of ramp time, in the absence of any local detuning pattern.
    Attributes:
        rampTime (Decimal): The ramp time. (measured in s)
        rabiCorrection (Annotated[Decimal, Field(ge=0.0, le=1.0)]): The fraction of the expected
            rabi oscillation frequency. Normalized to the range [0.0, 1.0].
    """

    rampTime: Decimal
    rabiCorrection: Annotated[Decimal, Field(ge=0.0, le=1.0)]


class PerformanceRydbergGlobal(BaseModel):
    """
    Performance metrics for the global driving field
    Attributes:
        rabiFrequencyErrorRel (Decimal): Total error in the Rabi frequency due to inhomogeneity and
            variations in time, relative to the specified value. (unitless)
        rabiFrequencyGlobalErrorRel (Decimal): RMS Rabi frequency variation in time as a relative
            value. (unitless)
        rabiFrequencyInhomogeneityRel (Decimal): RMS Rabi frequency inhomogeneity over the user
            region, relative to the specified value. (unitless)
        groundDetectionError (Annotated[Decimal, Field(ge=0, le=1)]): Probability of mis-detecting
            a ground-state atom as a Rydberg-state atom. (unitless)
        rydbergDetectionError (Annotated[Decimal, Field(ge=0, le=1)]): Probability of mis-detecting
            a Rydberg-state atom as a ground-state atom. (unitless)
        groundPrepError (Annotated[Decimal, Field(ge=0, le=1)]): Probability of failing to
            initialize an atom in the ground state prior to user-programmed coherent evolution, in
            the absence of any local detuning pattern. Normalized to 1.
        rydbergPrepErrorBest (Annotated[Decimal, Field(ge=0, le=1)]): Probability of failing to
            initialize an atom in the Rydberg state by an optimal (for that site) user specified
            pi-pulse from the ground state at maximum Rabi frequency, in the absence of any local
            detuning pattern. Normalized to 1.
        rydbergPrepErrorWorst (Annotated[Decimal, Field(ge=0, le=1)]): Worst-case probability of
            failing to initialize an atom in the Rydberg state by a user specified pi-pulse from
            the ground state at maximum Rabi frequency, optimized for a different site, in the
            absence of any local detuning pattern. Normalized to 1.
        T1Single (Decimal): Typical lifetime of the Rydberg state for a single non-interacting
            qubit in the absence of drive, as measured by a pi-wait-pi protocol. (measured in s)
        T1Ensemble (Decimal): Lifetime of the Rydberg state for an ensemble of non-interacting
            qubits distributed over the user region, in the absence of drive, as measured by a
            pi-wait-pi protocol. (measured in s)
        T2StarSingle (Decimal): Typical dephasing time of a single non-interacting qubit in the
            absence of drive, as measured by a Ramsey protocol. Includes coherent and incoherent
            processes. (measured in s)
        T2StarEnsemble (Decimal): Dephasing time of an ensemble of non-interacting qubits
            distributed over the user region, in the absence of drive, as measured by a Ramsey
            protocol. Includes coherent and incoherent processes. (measured in s)
        T2EchoSingle (Decimal): Typical dephasing time of a single non-interacting qubit in the
            absence of drive, as measured by a spin-echo dynamical decoupling protocol. This
            measurement isolates the effects of incoherent processes. (measured in s)
        T2EchoEnsemble (Decimal): Dephasing time of an ensemble of non-interacting qubits
            distributed over the user region, in the absence of drive, as measured by a spin-echo
            dynamical decoupling protocol. This measurement isolates the effects of incoherent
            processes. (measured in s)
        T2RabiSingle (Decimal): Typical decoherence time of a single driven qubit, as measured by a
            Rabi oscillation protocol with variable pulse duration a maximum Rabi frequency.
            Includes coherent and incoherent processes. (measured in s)
        T2RabiEnsemble (Decimal): Decoherence time of an ensemble of non-interacting driven qubits
            distributed over the user region, as measured by a Rabi oscillation protocol with
            variable pulse duration at maximum Rabi frequency. Includes coherent and incoherent
            processes. (measured in s)
        T2BlockadedRabiSingle (Decimal): Typical decoherence time of a single pair of driven
            blockaded qubits, as measured by a Rabi oscillation protocol with variable pulse
            duration a maximum Rabi frequency. Includes coherent and incoherent processes.
            (measured in s)
        T2BlockadedRabiEnsemble (Decimal): Decoherence time of an ensemble of pairs of driven
            blockaded qubits distributed over the user region (different pairs do not interact with
            each other), as measured by a Rabi oscillation protocol with variable pulse duration at
            maximum Rabi frequency. Includes coherent and incoherent processes. (measured in s)
        detuningError (Decimal): Systematic error from specified value of the global detuning
            averaged over the user region. (measured in rad/s)
        detuningInhomogeneity (Decimal): RMS inhomogeneity of the detuning over the user region.
            (measured in rad/s)
        rabiAmplitudeRampCorrection (list[RabiCorrection]): dynamic correction curve of effective
            single-qubit on-resonant Rabi oscillation frequency driven by a triangular amplitude
            waveform, relative to the specified value.
    """

    rabiFrequencyErrorRel: Decimal
    rabiFrequencyGlobalErrorRel: Decimal
    rabiFrequencyInhomogeneityRel: Decimal
    groundDetectionError: Annotated[Decimal, Field(ge=0, le=1)]
    rydbergDetectionError: Annotated[Decimal, Field(ge=0, le=1)]
    groundPrepError: Annotated[Decimal, Field(ge=0, le=1)]
    rydbergPrepErrorBest: Annotated[Decimal, Field(ge=0, le=1)]
    rydbergPrepErrorWorst: Annotated[Decimal, Field(ge=0, le=1)]
    T1Single: Decimal
    T1Ensemble: Decimal
    T2StarSingle: Decimal
    T2StarEnsemble: Decimal
    T2EchoSingle: Decimal
    T2EchoEnsemble: Decimal
    T2RabiSingle: Decimal
    T2RabiEnsemble: Decimal
    T2BlockadedRabiSingle: Decimal
    T2BlockadedRabiEnsemble: Decimal
    detuningError: Decimal
    detuningInhomogeneity: Decimal
    rabiAmplitudeRampCorrection: list[RabiCorrection]


class PerformanceRydbergLocal(BaseModel):
    """
    Performance metrics for the local detuning
    Attributes:
        detuningErrorRms(Decimal):
            Shot-to-shot relative RMS error on the time component of the local detuning values
            (local detuning waveform)
        siteCoefficientErrorRms(Decimal):
            Site-to-site absolute RMS error on the spatial component of the local detuning values
            (site coefficients)
        errorRateIncoherentBright(Decimal):
            Incoherent error rate for locally-addressed sites at max local detuning
        errorRateIncoherentDark(Decimal):
            Incoherent error rate at a site that is not locally-addressed due to crosstalk
            from a single locally-addressed site at min distance and at max local detuning
        crosstalk(Decimal):
            Fractional local detuning induced at a site that is not locally-addressed due to
            crosstalk from a single locally-addressed site
    """

    detuningErrorRms: Decimal
    siteCoefficientErrorRms: Decimal
    errorRateIncoherentBright: Decimal
    errorRateIncoherentDark: Decimal
    crosstalk: Decimal


class PerformanceRydberg(BaseModel):
    """
    Performance metrics of the global driving field and the local detuning
    Attributes:
        rydbergGlobal (PerformanceRydbergGlobal): Performance of Rydberg Global
        rydbergLocal (Optional[PerformanceRydbergLocal]): Performance of Rydberg Local
    """

    rydbergGlobal: PerformanceRydbergGlobal
    rydbergLocal: Optional[PerformanceRydbergLocal] = None


class Performance(BaseModel):
    """
    Parameters determining the limitations of the QuEra device
    Attributes:
        performanceLattice (PerformanceLattice): Uncertainties of atomic site arrangements
        performanceRydberg (PerformanceRydberg): Parameters determining the limitations
            the Rydberg simulator
    """

    lattice: PerformanceLattice
    rydberg: PerformanceRydberg


class QueraAhsParadigmProperties(BraketSchemaBase):
    """
    This defines the properties common to ahs Quera devices.

    Attributes:
        area: the area of the FOV
        geometry: spacing or number of sites or rows
        qubits: the number of qubits
        rydberg: the constraint of rydberg
        performance: the performance of rydberg or atom detection
    Examples:
        >>> import json
        >>> input_json = {
        ...     "braketSchemaHeader": {
        ...         "name": "braket.device_schema.quera.quera_ahs_paradigm_properties",
        ...         "version": "1",
        ...     },
        ...     "qubitCount": 256,
        ...     "lattice":{
        ...         "area": {
        ...             "width": 100.0e-6,
        ...             "height": 100.0e-6,
        ...         },
        ...         "geometry": {
        ...             "spacingRadialMin": 4.0e-6,
        ...             "spacingVerticalMin": 2.5e-6,
        ...             "positionResolution": 1e-7,
        ...             "numberSitesMax": 256,
        ...         }
        ...     },
        ...     "rydberg": {
        ...         "c6Coefficient": 2*math.pi(3.14) *862690,
        ...         "rydbergGlobal": {
        ...             "rabiFrequencyRange": [0, 2*math.pi(3.14) *4.0e6],
        ...             "rabiFrequencyResolution": 400
        ...             "rabiFrequencySlewRateMax": 2*math.pi(3.14) *4e6/100e-9,
        ...             "detuningRange": [-2*math.pi(3.14) *20.0e6,2*math.pi(3.14) *20.0e6],
        ...             "detuningResolution": 0.2,
        ...             "detuningSlewRateMax": 2*math.pi(3.14) *40.0e6/100e-9,
        ...             "phaseRange": [-99,99],
        ...             "phaseResolution": 5e-7,
        ...             "timeResolution": 1e-9,
        ...             "timeDeltaMin": 1e-8,
        ...             "timeMin": 0,
        ...             "timeMax": 4.0e-6,
        ...         },
        ...         "rydbergLocal" : {
        ...             "detuningRange": [0, 2 * math.pi * 50.0e6],
        ...             "detuningSlewRateMax": 0.2,
        ...             "siteCoefficientRange": [0.0, 0.2],
        ...             "numberLocalDetuningSitesMax": 0.2,
        ...             "spacingRadialMin": 0.2,
        ...             "timeResolution": 0.2,
        ...             "timeDeltaMin": 0.3,
        ...         }
        ...     },
        ...     "performance": {
        ...         "lattice":{
        ...             "positionErrorAbs": 0.025e-6,
        ...             "sitePositionError": 0.025e-6,
        ...             "atomPositionError": 0.025e-6,
        ...             "fillingErrorTypical": 0.005,
        ...             "fillingErrorWorst": 0.01,
        ...             "vacancyErrorTypical": 0.005,
        ...             "vacancyErrorWorst": 0.005,
        ...             "atomLossProbabilityTypical": 0.01,
        ...             "atomLossProbabilityWorst": 0.01,
        ...             "atomCaptureProbabilityTypical": 0.01,
        ...             "atomCaptureProbabilityWorst": 0.01,
        ...             "atomDetectionErrorFalsePositiveTypical": 0.01,
        ...             "atomDetectionErrorFalsePositiveWorst": 0.01,
        ...             "atomDetectionErrorFalseNegativeTypical": 0.01,
        ...             "atomDetectionErrorFalseNegativeWorst": 0.01,
        ...         },
        ...         "rydberg":{
        ...             "rydbergGlobal":{
        ...                 "rabiFrequencyErrorRel:": 0.01,
        ...                 "rabiFrequencyGlobalErrorRel": 0.01,
        ...                 "rabiFrequencyInhomogeneityRel": 0.01,
        ...                 "groundDetectionError": 0.01,
        ...                 "rydbergDetectionError":0.1,
        ...                 "groundPrepError": 0.01,
        ...                 "rydbergPrepErrorBest": 0.05,
        ...                 "rydbergPrepErrorWorst": 0.05,
        ...                 "T1Single": 100e-6,
        ...                 "T1Ensemble": 100e-6,
        ...                 "T2StarSingle": 5e-6,
        ...                 "T2StarEnsemble": 5e-6,
        ...                 "T2EchoSingle": 5e-6,
        ...                 "T2EchoEnsemble": 5e-6,
        ...                 "T2RabiSingle": 5e-6,
        ...                 "T2RabiEnsemble": 5e-6,
        ...                 "T2BlockadedRabiSingle":5e-6,
        ...                 "T2BlockadedRabiEnsemble": 5e-6,
        ...                 "detuningError": 1e6,
        ...                 "detuningInhomogeneity": 1e6,
        ...                 "rabiAmplitudeRampCorrection":[
        ...                     {
        ...                         "rampTime":50e-9,
        ...                         "rabiCorrection": 0.92
        ...                     },
        ...                     {
        ...                         "rampTime": 75e-9,
        ...                         "rabiCorrection": 0.97
        ...                     },
        ...                     {
        ...                         "rampTime": 100e-9,
        ...                         "rabiCorrection": 1.00
        ...                     }
        ...                 ]
        ...             },
        ...             "rydbergLocal":{
        ...                 "detuningErrorRms:": 0.01,
        ...                 "siteCoefficientErrorRms:": 0.01,
        ...                 "errorRateIncoherentBright:": 0.01,
        ...                 "errorRateIncoherentDark:": 0.01,
        ...                 "crosstalk:": 0.01,
        ...             },
        ...         },
        ...     },
        ... }
        >>> QueraAhsParadigmProperties.parse_raw_schema(json.dumps(input_json))
    """

    _PROGRAM_HEADER = BraketSchemaHeader(
        name="braket.device_schema.quera.quera_ahs_paradigm_properties", version="1"
    )
    braketSchemaHeader: BraketSchemaHeader = Field(default=_PROGRAM_HEADER, const=_PROGRAM_HEADER)
    qubitCount: int
    lattice: Lattice
    rydberg: Rydberg
    performance: Performance
