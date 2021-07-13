import os
import pickle

from braket.circuits import Circuit
from braket.devices import LocalSimulator

devices = {
    "default": LocalSimulator(),
    "dm": LocalSimulator("braket_dm"),
}


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


def test_from_ir():
    print("Testing Circuit::from_ir()")

    test_dir = "./test/unit_tests/braket/circuits/from"
    input_dir = f"{test_dir}/input_ir"

    check_dir = f"{test_dir}/check_ir.cache"
    if not os.path.isdir(check_dir):
        os.mkdir(check_dir, 0o755)
    output_dir = f"{test_dir}/output_ir.cache"
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir, 0o755)
    result_dir = f"{test_dir}/result_ir.cache"
    if not os.path.isdir(result_dir):
        os.mkdir(result_dir, 0o755)

    test_specs = read_file(f"{test_dir}/test_cases_ir.txt").strip("\n").split("\n")

    for test_spec in test_specs:
        print(f"Test: {test_spec}")

        test_case, sim_dev, shots_str = test_spec.split()
        shots = int(shots_str)

        input_path = f"{input_dir}/{test_case}"
        check_path = f"{check_dir}/{test_case}"
        output_path = f"{output_dir}/{test_case}"
        result_path = f"{result_dir}/{test_case}"

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
        assert f"{ir_inp}" == f"{ir_out}", f"Failed {test_spec}: {test_case}.ir_inp != ir_out"

        # Run the circuit created by from_ir() to make sure it is runnable
        try:
            task = devices[sim_dev].run(circ_from_ir, shots=shots)
            result = task.result()
            counts = result.measurement_counts
            # Save the run result for manual checking if required
            write_file(f"{result_path}.result_from_ir", f"{sort_key(counts)}")
        except Exception:
            assert False, f"Failed {test_spec}: result_from_ir"
