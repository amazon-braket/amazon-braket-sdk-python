import importlib
import tempfile
from logging import getLogger
from pathlib import Path
from ssl import SSLContext
from unittest.mock import MagicMock, patch

import job_module
import pytest

from braket.aws import AwsQuantumJob
from braket.devices import Devices
from braket.jobs import hybrid_job
from braket.jobs.config import CheckpointConfig, InstanceConfig, OutputDataConfig, StoppingCondition
from braket.jobs.local import LocalQuantumJob


@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_decorator_defaults(mock_create, mock_tempdir, _mock_open, mock_time):
    @hybrid_job(device=None)
    def my_entry(c=0, d: float = 1.0, **extras):
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name

    source_module = mock_tempdir_name
    entry_point = f"{mock_tempdir_name}.entry_point:my_entry"
    wait_until_complete = False

    device = "local:none/none"

    my_entry()

    mock_create.assert_called_with(
        device=device,
        source_module=source_module,
        entry_point=entry_point,
        wait_until_complete=wait_until_complete,
        job_name="my-entry-123000",
        hyperparameters={"c": 0, "d": 1.0},
        logger=getLogger("braket.jobs.hybrid_job"),
    )
    assert mock_tempdir.return_value.__exit__.called


@pytest.mark.parametrize("include_modules", (job_module, ["job_module"]))
@patch("sys.stdout")
@patch("time.time", return_value=123.0)
@patch("cloudpickle.register_pickle_by_value")
@patch("cloudpickle.unregister_pickle_by_value")
@patch("shutil.copy")
@patch("builtins.open")
@patch.object(AwsQuantumJob, "create")
def test_decorator_non_defaults(
    mock_create,
    _mock_open,
    mock_copy,
    mock_register,
    mock_unregister,
    mock_time,
    mock_stdout,
    include_modules,
):
    dependencies = "my_requirements.txt"
    image_uri = "my_image.uri"
    default_instance = InstanceConfig()
    distribution = "data_parallel"
    copy_checkpoints_from_job = "arn/other-job"
    checkpoint_config = CheckpointConfig(localPath="local", s3Uri="s3")
    role_arn = "role_arn"
    stopping_condition = StoppingCondition(maxRuntimeInSeconds=10)
    output_data_config = OutputDataConfig(s3Path="s3")
    aws_session = MagicMock()
    tags = {"my_tag": "my_value"}
    logger = getLogger(__name__)

    with tempfile.TemporaryDirectory() as tempdir:
        Path(tempdir, "temp_dir").mkdir()
        Path(tempdir, "temp_file").touch()

        input_data = {
            "my_prefix": "my_input_data",
            "my_dir": Path(tempdir, "temp_dir"),
            "my_file": Path(tempdir, "temp_file"),
            "my_s3_prefix": "s3://bucket/path/to/prefix",
        }

        @hybrid_job(
            device=Devices.Amazon.SV1,
            include_modules=include_modules,
            dependencies=dependencies,
            image_uri=image_uri,
            input_data=input_data,
            wait_until_complete=True,
            instance_config=default_instance,
            distribution=distribution,
            checkpoint_config=checkpoint_config,
            copy_checkpoints_from_job=copy_checkpoints_from_job,
            role_arn=role_arn,
            stopping_condition=stopping_condition,
            output_data_config=output_data_config,
            aws_session=aws_session,
            tags=tags,
            logger=logger,
        )
        def my_entry(a, b: int, c=0, d: float = 1.0, **extras) -> str:
            return "my entry return value"

        mock_tempdir = MagicMock(spec=tempfile.TemporaryDirectory)
        mock_tempdir_name = "job_temp_dir_00000"
        mock_tempdir.__enter__.return_value = mock_tempdir_name

        device = Devices.Amazon.SV1
        source_module = mock_tempdir_name
        entry_point = f"{mock_tempdir_name}.entry_point:my_entry"
        wait_until_complete = True

        s3_not_linked = (
            "Input data channels mapped to an S3 source will not be available in the working "
            'directory. Use `get_input_data_dir(channel="my_s3_prefix")` to read input data '
            "from S3 source inside the job container."
        )

        with patch("tempfile.TemporaryDirectory", return_value=mock_tempdir):
            my_entry("a", 2, 3, 4, extra_param="value", another=6)

    mock_create.assert_called_with(
        device=device,
        source_module=source_module,
        entry_point=entry_point,
        image_uri=image_uri,
        input_data=input_data,
        wait_until_complete=wait_until_complete,
        job_name="my-entry-123000",
        instance_config=default_instance,
        distribution=distribution,
        hyperparameters={"a": "a", "b": 2, "c": 3, "d": 4, "extra_param": "value", "another": 6},
        checkpoint_config=checkpoint_config,
        copy_checkpoints_from_job=copy_checkpoints_from_job,
        role_arn=role_arn,
        stopping_condition=stopping_condition,
        output_data_config=output_data_config,
        aws_session=aws_session,
        tags=tags,
        logger=logger,
    )
    included_module = importlib.import_module("job_module")
    mock_register.assert_called_with(included_module)
    mock_unregister.assert_called_with(included_module)
    mock_copy.assert_called_with(
        Path("my_requirements.txt").resolve(), Path(mock_tempdir_name, "requirements.txt")
    )
    assert mock_tempdir.__exit__.called
    mock_stdout.write.assert_any_call(s3_not_linked)


@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(LocalQuantumJob, "create")
def test_decorator_local(mock_create, mock_tempdir, _mock_open, mock_time):
    @hybrid_job(device=Devices.Amazon.SV1, local=True)
    def my_entry():
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name

    device = Devices.Amazon.SV1
    source_module = mock_tempdir_name
    entry_point = f"{mock_tempdir_name}.entry_point:my_entry"

    my_entry()

    mock_create.assert_called_with(
        device=device,
        source_module=source_module,
        entry_point=entry_point,
        job_name="my-entry-123000",
        hyperparameters={},
    )
    assert mock_tempdir.return_value.__exit__.called


@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(LocalQuantumJob, "create")
def test_decorator_local_unsupported_args(mock_create, mock_tempdir, _mock_open, mock_time):
    @hybrid_job(
        device=Devices.Amazon.SV1,
        local=True,
        wait_until_complete=True,
        copy_checkpoints_from_job="arn/other-job",
        instance_config=InstanceConfig(),
        distribution="data_parallel",
        stopping_condition=StoppingCondition(),
        tags={"my_tag": "my_value"},
        logger=getLogger(__name__),
    )
    def my_entry():
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name

    device = Devices.Amazon.SV1
    source_module = mock_tempdir_name
    entry_point = f"{mock_tempdir_name}.entry_point:my_entry"

    my_entry()

    mock_create.assert_called_with(
        device=device,
        source_module=source_module,
        entry_point=entry_point,
        job_name="my-entry-123000",
        hyperparameters={},
    )
    assert mock_tempdir.return_value.__exit__.called


@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_job_name_too_long(mock_create, mock_tempdir, _mock_open, mock_time):
    @hybrid_job(device="local:braket/default")
    def this_is_a_50_character_func_name_for_testing_names():
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name

    device = "local:braket/default"
    source_module = mock_tempdir_name
    entry_point = (
        f"{mock_tempdir_name}.entry_point:this_is_a_50_character_func_name_for_testing_names"
    )
    wait_until_complete = False

    with pytest.warns(UserWarning):
        this_is_a_50_character_func_name_for_testing_names()

        expected_job_name = "this-is-a-50-character-func-name-for-testin-123000"

        mock_create.assert_called_with(
            device=device,
            source_module=source_module,
            entry_point=entry_point,
            wait_until_complete=wait_until_complete,
            job_name=expected_job_name,
            hyperparameters={},
            logger=getLogger("braket.jobs.hybrid_job"),
        )
        assert len(expected_job_name) == 50
        assert mock_tempdir.return_value.__exit__.called


@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_decorator_pos_only_slash(mock_create, mock_tempdir, _mock_open, mock_time):
    @hybrid_job(device="local:braket/default")
    def my_entry(pos_only, /):
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name

    device = "local:braket/default"
    source_module = mock_tempdir_name
    entry_point = f"{mock_tempdir_name}.entry_point:my_entry"
    wait_until_complete = False

    pos_only_warning = "Positional only arguments will not be logged to the hyperparameters file."
    with pytest.warns(match=pos_only_warning):
        my_entry("pos_only")

    mock_create.assert_called_with(
        device=device,
        source_module=source_module,
        entry_point=entry_point,
        wait_until_complete=wait_until_complete,
        job_name="my-entry-123000",
        hyperparameters={},
        logger=getLogger("braket.jobs.hybrid_job"),
    )
    assert mock_tempdir.return_value.__exit__.called


@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_decorator_pos_only_args(mock_create, mock_tempdir, _mock_open, mock_time):
    @hybrid_job(device="local:braket/default")
    def my_entry(*args):
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name

    device = "local:braket/default"
    source_module = mock_tempdir_name
    entry_point = f"{mock_tempdir_name}.entry_point:my_entry"
    wait_until_complete = False

    pos_only_warning = "Positional only arguments will not be logged to the hyperparameters file."
    with pytest.warns(match=pos_only_warning):
        my_entry("pos_only")

    mock_create.assert_called_with(
        device=device,
        source_module=source_module,
        entry_point=entry_point,
        wait_until_complete=wait_until_complete,
        job_name="my-entry-123000",
        hyperparameters={},
        logger=getLogger("braket.jobs.hybrid_job"),
    )
    assert mock_tempdir.return_value.__exit__.called


def test_serialization_error():
    ssl_context = SSLContext()

    @hybrid_job(device=None)
    def fails_serialization():
        print(ssl_context)

    serialization_failed = (
        "Serialization failed for decorator hybrid job. For troubleshooting, "
        "see the developer guide: #todo: link to docs with info as below"
    )
    with pytest.raises(RuntimeError, match=serialization_failed):
        fails_serialization()
