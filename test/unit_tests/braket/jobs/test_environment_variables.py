import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from braket.jobs import (
    get_checkpoint_dir,
    get_hyperparameters,
    get_input_data_dir,
    get_job_device_arn,
    get_job_name,
    get_results_dir,
)


def test_job_name():
    assert get_job_name() == ""
    job_name = "my_job_name"
    with patch.dict(os.environ, {"AMZN_BRAKET_JOB_NAME": job_name}):
        assert get_job_name() == job_name


def test_job_device_arn():
    assert get_job_device_arn() == "local:none/none"
    device_arn = "my_device_arn"
    with patch.dict(os.environ, {"AMZN_BRAKET_DEVICE_ARN": device_arn}):
        assert get_job_device_arn() == device_arn


def test_input_data_dir():
    assert get_input_data_dir() == "."
    input_path = "my/input/path"
    with patch.dict(os.environ, {"AMZN_BRAKET_INPUT_DIR": input_path}):
        assert get_input_data_dir() == f"{input_path}/input"
        channel_name = "my_channel"
        assert get_input_data_dir(channel_name) == f"{input_path}/{channel_name}"


def test_results_dir():
    assert get_results_dir() == "."
    results_dir = "my_results_dir"
    with patch.dict(os.environ, {"AMZN_BRAKET_JOB_RESULTS_DIR": results_dir}):
        assert get_results_dir() == results_dir


def test_checkpoint_dir():
    assert get_checkpoint_dir() == "."
    checkpoint_dir = "my_checkpoint_dir"
    with patch.dict(os.environ, {"AMZN_BRAKET_CHECKPOINT_DIR": checkpoint_dir}):
        assert get_checkpoint_dir() == checkpoint_dir


def test_hyperparameters():
    assert get_hyperparameters() == {}
    hp_file = "my_hyperparameters.json"
    hyperparameters = {
        "a": "a_val",
        "b": 2,
    }
    with (
        tempfile.TemporaryDirectory() as temp_dir,
        patch.dict(os.environ, {"AMZN_BRAKET_HP_FILE": str(Path(temp_dir) / hp_file)}),
    ):
        with open(str(Path(temp_dir) / hp_file), "w") as f:
            json.dump(hyperparameters, f)
        assert get_hyperparameters() == hyperparameters
