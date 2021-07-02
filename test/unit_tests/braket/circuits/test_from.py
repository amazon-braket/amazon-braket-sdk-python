import os

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


def dump_prog(circ):
    return f"{circ.to_ir()}"


def sort_key(d):
    return {x: d[x] for x in sorted(d)} if d else None


def test_from():  # noqa: C901
    print("Testing with circuits without matrices")

    test_dir = "./test/unit_tests/braket/circuits/from"
    input_dir = f"{test_dir}/input"

    check_dir = f"{test_dir}/check.cache"
    if not os.path.isdir(check_dir):
        os.mkdir(check_dir, 0o755)
    output_dir = f"{test_dir}/output.cache"
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir, 0o755)
    result_dir = f"{test_dir}/result.cache"
    if not os.path.isdir(result_dir):
        os.mkdir(result_dir, 0o755)

    test_specs = read_file(f"{test_dir}/test_cases.txt").strip("\n").split("\n")

    # Naming
    #     Prefixes:
    #         circ - Circuit object
    #         diag - ascii diagram: str - f'{circ}'
    #         repr - repr output: str - repr(circ)
    #         prog - Program dumpo: str - f'{prog}'
    #         ir - Intermediate Representation (IR): Program - circ.to_ir()
    #     Suffixes:
    #         inp - Input
    #         out - Output
    #         <test> - Generated from_diagram, from_repr, from_ir

    for test_spec in test_specs:
        print(f"Test: {test_spec}")

        test_scope_str, test_case, sim_dev, shots_str = test_spec.split()
        if test_scope_str == "*":
            test_scope = ["diag", "repr", "ir"]
        else:
            test_scope = test_scope_str.split("|")
        shots = int(shots_str)

        input_path = f"{input_dir}/{test_case}"
        check_path = f"{check_dir}/{test_case}"
        output_path = f"{output_dir}/{test_case}"
        result_path = f"{result_dir}/{test_case}"

        # Loading from input path
        diag_inp = None
        try:
            diag_inp = read_file(f"{input_path}.diag")
        except Exception:
            pass

        repr_inp = None
        try:
            repr_inp = read_file(f"{input_path}.repr")
        except Exception:
            pass

        prog_chk = None
        try:
            prog_chk = read_file(f"{check_path}.prog")
        except Exception:
            pass

        #
        # from_diagram
        #
        circ_from_diagram = None
        if "diag" in test_scope and diag_inp:
            print("  from_diagram")
            circ_from_diagram = Circuit().from_diagram(diag_inp)

            diag_from_diagram = f"{circ_from_diagram}\n"
            write_file(f"{output_path}.diag_from_diagram", diag_from_diagram)
            assert (
                diag_from_diagram == diag_inp
            ), f"Failed {test_spec}: {test_case}.diag_from_diagram != diag_inp"

            try:
                task = devices[sim_dev].run(circ_from_diagram, shots=shots)
                result = task.result()
                counts = result.measurement_counts
                write_file(f"{result_path}.result_from_diagram", f"{sort_key(counts)}")
            except Exception:
                assert False, f"Failed {test_spec}: result_from_diagram"

            # For subsequent tests
            if not repr_inp:
                repr_inp = repr(circ_from_diagram)
                write_file(f"{check_path}.repr", repr_inp)
            if not prog_chk:
                prog_chk = dump_prog(circ_from_diagram)
                write_file(f"{check_path}.prog", prog_chk)

        #
        # from_repr
        #
        circ_from_repr = None
        if "repr" in test_scope and repr_inp:
            print("  from_repr")
            circ_from_repr = Circuit().from_repr(repr_inp)

            repr_from_repr = f"{repr(circ_from_repr)}"
            write_file(f"{output_path}.repr_from_repr", repr_from_repr)
            assert (
                repr_from_repr == repr_inp
            ), f"Failed {test_spec}: {test_case}.repr_from_repr != repr_inp"

            if diag_inp:
                diag_from_repr = f"{circ_from_repr}\n"
                write_file(f"{output_path}.diag_from_repr", diag_from_repr)
                assert (
                    diag_from_repr == diag_inp
                ), f"Failed {test_spec}: {test_case}.diag_from_repr != diag_inp"

            try:
                task = devices[sim_dev].run(circ_from_repr, shots=shots)
                result = task.result()
                counts = result.measurement_counts
                write_file(f"{result_path}.result_from_repr", f"{sort_key(counts)}")
            except Exception:
                assert False, f"Failed {test_spec}: result_from_repr"

            if not prog_chk:
                prog_chk = dump_prog(circ_from_diagram)
                write_file(f"{check_path}.prog", prog_chk)

        #
        # from_ir
        #
        circ_from_ir = None
        if "ir" in test_scope and (circ_from_diagram or circ_from_repr):
            print("  from_ir")
            ir_inp = None
            if circ_from_diagram:
                ir_inp = circ_from_diagram.to_ir()
                print("    using circ_from_diagram")
            elif circ_from_repr:
                ir_inp = circ_from_repr.to_ir()
                print("    using circ_from_repr")

            if not ir_inp:
                print("    (no input circuit)")
            else:
                circ_from_ir = Circuit().from_ir(ir_inp)

                prog_from_ir = dump_prog(circ_from_ir)
                write_file(f"{output_path}.prog_from_ir", prog_from_ir)
                assert (
                    prog_from_ir == prog_chk
                ), f"Failed {test_spec}: {test_case}.prog_from_ir != prog_chk"

                try:
                    task = devices[sim_dev].run(circ_from_ir, shots=shots)
                    result = task.result()
                    counts = result.measurement_counts
                    write_file(f"{result_path}.result_from_ir", f"{sort_key(counts)}")
                except Exception:
                    assert False, f"Failed {test_spec}: result_from_ir"
