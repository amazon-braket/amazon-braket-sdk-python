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

import pickle
from pathlib import Path

import pytest

from braket.circuits import Circuit
from braket.devices import LocalSimulator

SHOTS = 1000

DEVICE = LocalSimulator()
DEVICE_DM = LocalSimulator("braket_dm")

TEST_CASES = [
    ("all", DEVICE, SHOTS),
    ("bell", DEVICE, SHOTS),
    ("ghz", DEVICE, SHOTS),
    ("rot", DEVICE, SHOTS),
    ("pm1", DEVICE, SHOTS),
    ("pm1b", DEVICE, SHOTS),
    ("pm2", DEVICE, SHOTS),
    ("noise_1", DEVICE_DM, SHOTS),
    ("noise_2", DEVICE_DM, SHOTS),
    ("noise_3", DEVICE_DM, SHOTS),
    ("noise_4", DEVICE_DM, SHOTS),
    ("noise_5", DEVICE_DM, SHOTS),
    ("noise_6", DEVICE_DM, SHOTS),
    ("noise_7", DEVICE_DM, SHOTS),
    ("noise_8", DEVICE_DM, SHOTS),
    ("noise_9", DEVICE_DM, 0),
    ("noise_ap", DEVICE_DM, SHOTS),
    ("noise_deph_2q", DEVICE_DM, SHOTS),
    ("noise_deph_mixed", DEVICE_DM, SHOTS),
    ("noise_depo", DEVICE_DM, SHOTS),
    ("noise_depo_2q", DEVICE_DM, SHOTS),
    ("noise_gad", DEVICE_DM, SHOTS),
    ("noise_pb", DEVICE_DM, SHOTS),
    ("noise_pc", DEVICE_DM, SHOTS),
    ("noise_pc_gad", DEVICE_DM, SHOTS),
    ("rt1", DEVICE, 0),
    ("rt2", DEVICE, 0),
    ("rt3", DEVICE, SHOTS),
    ("rt_dm", DEVICE_DM, 0),
    ("matrix-hermitian", DEVICE_DM, SHOTS),
    ("matrix-obsx", DEVICE_DM, SHOTS),
    ("matrix-obsxy", DEVICE_DM, SHOTS),
]

INPUT_DIR = "./test/unit_tests/braket/circuits/from_ir_test_files"

TEST_CACHE_DIR = "./.cache/from_ir_test"
for cache_dir in ["check", "output", "result"]:
    Path(f"{TEST_CACHE_DIR}/{cache_dir}").mkdir(parents=True, exist_ok=True)


def read_file(file_name):
    f = open(file_name, "r")
    file_text = f.read()
    f.close()
    return file_text


def write_file(file_name, file_text):
    f = open(file_name, "w")
    f.write(file_text)
    f.close()
    return file_text


def read_pickle(file):
    return pickle.load(open(file, "rb"))


def sort_key(d):
    return {x: d[x] for x in sorted(d)} if d else None


@pytest.mark.parametrize("test_case, sim_dev, shots", TEST_CASES)
def test_from_ir(test_case, sim_dev, shots):
    input_path = f"{INPUT_DIR}/{test_case}"
    check_path = f"{TEST_CACHE_DIR}/check/{test_case}"
    output_path = f"{TEST_CACHE_DIR}/output/{test_case}"
    result_path = f"{TEST_CACHE_DIR}/result/{test_case}"

    # Loading the pickled IR test case
    ir_inp = read_pickle(f"{input_path}.ir")
    # Save the input IR in repr for manual checking if required
    write_file(f"{check_path}.ir_inp", f"{ir_inp}")

    # Test the from_ir() method
    circ_from_ir = Circuit().from_ir(ir_inp)
    write_file(f"{check_path}.diag", f"{circ_from_ir}")

    ir_out = circ_from_ir.to_ir()
    # Save the output IR in repr manual checking if required
    write_file(f"{output_path}.ir_out", f"{ir_out}")
    assert f"{ir_inp}" == f"{ir_out}"

    # Run the circuit created by from_ir() to make sure it is runnable
    try:
        task = sim_dev.run(circ_from_ir, shots=shots)
        result = task.result()
        counts = result.measurement_counts
        # Save the run result for manual checking if required
        write_file(f"{result_path}.result_from_ir", f"{sort_key(counts)}")
    except Exception:
        assert False, f"Failed test case {test_case}: Circuit from IR failed to run"
