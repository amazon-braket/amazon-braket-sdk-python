import os
import random

import numpy as np

from braket.circuits import Circuit, Noise, Observable
from braket.devices import LocalSimulator

test_dir = "./test/unit_tests/braket/circuits/from"

check_dir = f"{test_dir}/check.cache"
if not os.path.isdir(check_dir):
    os.mkdir(check_dir, 0o755)
output_dir = f"{test_dir}/output.cache"
if not os.path.isdir(output_dir):
    os.mkdir(output_dir, 0o755)
result_dir = f"{test_dir}/result.cache"
if not os.path.isdir(result_dir):
    os.mkdir(result_dir, 0o755)

device = LocalSimulator("braket_dm")
shots = 1000


def sort_key(d):
    return {x: d[x] for x in sorted(d)} if d else None


def write_file(file_name, file_text):
    f = open(file_name, "w")
    f.write(file_text)
    f.close()
    return file_text


def dump_prog(circ):
    return f"{circ.to_ir()}"


def u3(alpha, theta, phi):
    # One-bit unitary
    u11 = np.cos(alpha / 2) - 1j * np.sin(alpha / 2) * np.cos(theta)
    u12 = -1j * (np.exp(-1j * phi)) * np.sin(theta) * np.sin(alpha / 2)
    u21 = -1j * (np.exp(1j * phi)) * np.sin(theta) * np.sin(alpha / 2)
    u22 = np.cos(alpha / 2) + 1j * np.sin(alpha / 2) * np.cos(theta)

    return np.array([[u11, u12], [u21, u22]])


def u_cnot():
    # Two-bit unitary
    return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])


def hermitian_xyz():
    # Hermitian equivalent to X@Y@Z
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, -1j, 0],
            [0, 0, 0, 0, 0, 0, 0, 1j],
            [0, 0, 0, 0, 1j, 0, 0, 0],
            [0, 0, 0, 0, 0, -1j, 0, 0],
            [0, 0, -1j, 0, 0, 0, 0, 0],
            [0, 0, 0, 1j, 0, 0, 0, 0],
            [1j, 0, 0, 0, 0, 0, 0, 0],
            [0, -1j, 0, 0, 0, 0, 0, 0],
        ]
    )


def kaus_2():
    E0 = u3(
        np.pi * random.random(), np.pi / 3 * random.random(), np.pi / 4 * random.random()
    ) * np.sqrt(0.2)
    E1 = u3(
        np.pi * random.random(), np.pi / 3 * random.random(), np.pi / 4 * random.random()
    ) * np.sqrt(0.8)
    K = [E0, E1]
    return K


def do_test(circ, test_case="matrix"):
    print(f"  {test_case}")
    check_path = f"{check_dir}/{test_case}"
    output_path = f"{output_dir}/{test_case}"
    result_path = f"{result_dir}/{test_case}"

    write_file(f"{check_path}.diag", f"{circ}")

    try:
        task = device.run(circ, shots=shots)
        result = task.result()
        counts = result.measurement_counts
        write_file(f"{result_path}.result_circ", f"{sort_key(counts)}")
    except Exception:
        assert False, f"Failed {test_case}: result_from_ir"

    prog_chk = dump_prog(circ)
    write_file(f"{check_path}.prog", prog_chk)

    ir_inp = circ.to_ir()
    circ_from_ir = Circuit().from_ir(ir_inp)
    write_file(f"{output_path}.diag_from_ir", f"{circ_from_ir}")

    prog_from_ir = dump_prog(circ_from_ir)
    write_file(f"{output_path}.prog_from_ir", prog_from_ir)
    assert prog_from_ir == prog_chk, f"Failed {test_case}: {test_case}.prog_from_ir != prog_chk"

    try:
        task = device.run(circ_from_ir, shots=shots)
        result = task.result()
        counts = result.measurement_counts
        write_file(f"{result_path}.result_from_ir", f"{sort_key(counts)}")
    except Exception:
        assert False, f"Failed {test_case}: result_from_ir"


def test_from_matrices():
    print("Testing with circuits with matrices")

    circ_base = Circuit()
    circ_base.h(0)
    circ_base.unitary(matrix=u3(np.pi / 2, np.pi / 3, np.pi / 4), targets=[0])
    circ_base.cnot(0, 1)
    circ_base.cnot(1, 2)
    circ_base.apply_gate_noise(Noise.Kraus(kaus_2()))
    circ_base.unitary(matrix=u_cnot(), targets=[0, 1])

    circ = circ_base + Circuit().expectation(
        Observable.Hermitian(matrix=hermitian_xyz()), [0, 1, 2]
    )
    do_test(circ, "matrix-hermitian")

    circ = circ_base + Circuit().expectation(Observable.X(), 0)
    do_test(circ, "matrix-obsx")

    circ = circ_base + Circuit().expectation(Observable.X() @ Observable.Y(), [0, 1])
    do_test(circ, "matrix-obsxy")
