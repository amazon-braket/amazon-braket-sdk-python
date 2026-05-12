import os
import pytest
import shutil

from braket.circuits.text_diagram_builders.text_circuit_diagram_utils import _get_display_width


def test_display_width():
    os.environ["BRAKET_DIAGRAM_WIDTH"] = "100"
    try:
        assert _get_display_width() == 100
    except AssertionError as e:
        pytest.fail(f"Incorrect display width: \n{e}")
    finally:
        del os.environ["BRAKET_DIAGRAM_WIDTH"]


@pytest.mark.parametrize(
    "invalid_input",
    [
        "TRICK",
        "echo `hello world`",
        "",
    ],
)
def test_display_width_invalid_input(invalid_input):
    os.environ["BRAKET_DIAGRAM_WIDTH"] = invalid_input
    try:
        assert _get_display_width() == shutil.get_terminal_size().columns
    except AssertionError as e:
        pytest.fail(f"Incorrect display width: \n{e}")
    finally:
        del os.environ["BRAKET_DIAGRAM_WIDTH"]


@pytest.mark.parametrize(
    "valid_input",
    ["-1", "0", "-5025", "10000000"],
)
def test_display_width_rounded_input(valid_input):
    os.environ["BRAKET_DIAGRAM_WIDTH"] = valid_input
    try:
        assert _get_display_width() in {40, 100000}
    except AssertionError as e:
        pytest.fail(f"Incorrect display width: \n{e}")
    finally:
        del os.environ["BRAKET_DIAGRAM_WIDTH"]
