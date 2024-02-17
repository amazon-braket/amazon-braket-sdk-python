import importlib
import multiprocessing
import os
import pathlib

import pytest


def test_for_import_cycles():
    # Note, because of all the multiprocessing in this test, when running 'tox', the process
    # threads may be made to wait as other tests are running in parallel, making it seems like
    # this test is much slower than it actually is. However, splitting the test into a
    # parameterized version wasn't able to correctly detect some circular imports when running tox.
    modules = get_modules_to_test()
    processes = []
    multiprocessing.set_start_method("spawn", force=True)
    for module in modules:
        # We create a separate process to make sure the imports do not interfere with each-other.
        process = multiprocessing.Process(target=import_module, args=(module,))
        processes.append(process)
        process.start()

    for index, process in enumerate(processes):
        process.join()
        if process.exitcode != 0:
            pytest.fail(
                f"Unable to import '{modules[index]}'."
                " If all other tests are passing, check for cyclical dependencies."
            )


def get_modules_to_test():
    curr_path = pathlib.Path(__file__).resolve()
    while "test" in str(curr_path):
        curr_path = curr_path.parent
    curr_path = curr_path.joinpath("src")
    curr_path_len = len(str(curr_path)) + len(os.sep)
    modules = []
    for dir_, temp, files in os.walk(curr_path):
        # Rather than testing every single python file we just test modules, for now.
        if "__init__.py" in files:
            braket_module = dir_[curr_path_len:].replace(os.sep, ".")
            modules.append(braket_module)
    return modules


def import_module(module):
    importlib.import_module(module)
