# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from enum import StrEnum


class Devices:
    class _Amazon(StrEnum):
        SV1 = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
        TN1 = "arn:aws:braket:::device/quantum-simulator/amazon/tn1"
        DM1 = "arn:aws:braket:::device/quantum-simulator/amazon/dm1"

    class _AQT(StrEnum):
        IbexQ1 = "arn:aws:braket:eu-north-1::device/qpu/aqt/Ibex-Q1"

    class _DWave(StrEnum):
        _Advantage1 = "arn:aws:braket:::device/qpu/d-wave/Advantage_system1"
        _Advantage3 = "arn:aws:braket:::device/qpu/d-wave/Advantage_system3"
        _Advantage4 = "arn:aws:braket:::device/qpu/d-wave/Advantage_system4"
        _Advantage6 = "arn:aws:braket:us-west-2::device/qpu/d-wave/Advantage_system6"
        _DW2000Q6 = "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6"

    class _IQM(StrEnum):
        Garnet = "arn:aws:braket:eu-north-1::device/qpu/iqm/Garnet"
        Emerald = "arn:aws:braket:eu-north-1::device/qpu/iqm/Emerald"

    class _IonQ(StrEnum):
        _Harmony = "arn:aws:braket:us-east-1::device/qpu/ionq/Harmony"
        Aria1 = "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1"
        _Aria2 = "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-2"
        Forte1 = "arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1"
        ForteEnterprise1 = "arn:aws:braket:us-east-1::device/qpu/ionq/Forte-Enterprise-1"

    class _OQC(StrEnum):
        _Lucy = "arn:aws:braket:eu-west-2::device/qpu/oqc/Lucy"

    class _QuEra(StrEnum):
        Aquila = "arn:aws:braket:us-east-1::device/qpu/quera/Aquila"

    class _Rigetti(StrEnum):
        _Aspen8 = "arn:aws:braket:::device/qpu/rigetti/Aspen-8"
        _Aspen9 = "arn:aws:braket:::device/qpu/rigetti/Aspen-9"
        _Aspen10 = "arn:aws:braket:::device/qpu/rigetti/Aspen-10"
        _Aspen11 = "arn:aws:braket:::device/qpu/rigetti/Aspen-11"
        _AspenM1 = "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-1"
        _AspenM2 = "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-2"
        _AspenM3 = "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-3"
        _Ankaa2 = "arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-2"
        Ankaa3 = "arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-3"

    class _Xanadu(StrEnum):
        _Borealis = "arn:aws:braket:us-east-1::device/qpu/xanadu/Borealis"

    Amazon = _Amazon
    AQT = _AQT
    # DWave = _DWave
    IonQ = _IonQ
    IQM = _IQM
    # OQC = _OQC
    QuEra = _QuEra
    Rigetti = _Rigetti
    # Xanadu = _Xanadu
