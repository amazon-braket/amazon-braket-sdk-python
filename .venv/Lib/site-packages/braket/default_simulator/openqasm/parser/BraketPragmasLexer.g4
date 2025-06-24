lexer grammar BraketPragmasLexer;

import qasm3Lexer;

BRAKET: 'braket';
UNITARY: 'unitary';
RESULT: 'result';
NOISE: 'noise';
VERBATIM: 'verbatim';

STATE_VECTOR: 'state_vector';
PROBABILITY: 'probability';
DENSITY_MATRIX: 'density_matrix';
AMPLITUDE: 'amplitude';
EXPECTATION: 'expectation';
VARIANCE: 'variance';
SAMPLE: 'sample';

X: 'x';
Y: 'y';
Z: 'z';
I: 'i';
H: 'h';
HERMITIAN: 'hermitian';

ALL: 'all';

AT: '@';

BIT_FLIP: 'bit_flip';
PHASE_FLIP: 'phase_flip';
PAULI_CHANNEL: 'pauli_channel';
DEPOLARIZING: 'depolarizing';
TWO_QUBIT_DEPOLARIZING: 'two_qubit_depolarizing';
TWO_QUBIT_DEPHASING: 'two_qubit_dephasing';
AMPLITUDE_DAMPING: 'amplitude_damping';
GENERALIZED_AMPLITUDE_DAMPING: 'generalized_amplitude_damping';
PHASE_DAMPING: 'phase_damping';
KRAUS: 'kraus';
