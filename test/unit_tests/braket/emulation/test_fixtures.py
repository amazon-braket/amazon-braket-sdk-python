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

minimal_valid_device_properties_dict = {'action': {'braket.ir.openqasm.program': {'actionType': 'braket.ir.openqasm.program',
                                           'supportedOperations': [],
                                           'supportedResultTypes': [{'maxShots': 20000,
                                                                     'minShots': 1,
                                                                     'name': 'Probability',
                                                                     'observables': None}],
                                           'version': ['1.0']}},
 'paradigm': {'connectivity': {'connectivityGraph': {'1': ['2'],'2': ['1']},
                               'fullyConnected': False},
              'nativeGateSet': ['cz', 'prx'],
              'qubitCount': 2},
 'standardized': {'oneQubitProperties': {'1': {'T1': {'standardError': None,
                                                      'unit': 'S',
                                                      'value': 3.70332092508592e-05},
                                               'T2': {'standardError': None,
                                                      'unit': 'S',
                                                      'value': 6.886545811001897e-06},
                                               'oneQubitFidelity': [{'fidelity': 0.9982390384135782,
                                                                     'fidelityType': {'description': None,
                                                                                      'name': 'RANDOMIZED_BENCHMARKING'},
                                                                     'standardError': None},
                                                                    {'fidelity': 0.98225,
                                                                     'fidelityType': {'description': None,
                                                                                      'name': 'READOUT'},
                                                                     'standardError': None}]},
                                         '2': {'T1': {'standardError': None,
                                                      'unit': 'S',
                                                      'value': 3.70332092508592e-05},
                                               'T2': {'standardError': None,
                                                      'unit': 'S',
                                                      'value': 6.886545811001897e-06},
                                               'oneQubitFidelity': [{'fidelity': 0.9982390384135782,
                                                                     'fidelityType': {'description': None,
                                                                                      'name': 'RANDOMIZED_BENCHMARKING'},
                                                                     'standardError': None},
                                                                    {'fidelity': 0.98225,
                                                                     'fidelityType': {'description': None,
                                                                                      'name': 'READOUT'},
                                                                     'standardError': None}]},
                                         },
                  'twoQubitProperties': {'1-2': {'twoQubitGateFidelity': [{'direction': None,
                                                                           'fidelity': 0.9954869842247106,
                                                                           'fidelityType': {'description': None,
                                                                                            'name': 'RANDOMIZED_BENCHMARKING'},
                                                                           'gateName': 'CZ',
                                                                           'standardError': None}]},
                                         }}}

dict_errorMitigation = {"provider": {"errorMitigation": {"braket.device_schema.error_mitigation.debias.Debias": {"minimumShots": 2500}}}}
minimal_valid_device_properties_dict_with_errorMitigation = {**minimal_valid_device_properties_dict, **dict_errorMitigation}