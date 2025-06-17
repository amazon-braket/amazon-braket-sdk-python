import ast
import importlib
import inspect
import re
import sys
import tempfile
from logging import getLogger
from pathlib import Path
from ssl import PROTOCOL_TLS_CLIENT, SSLContext
from unittest.mock import MagicMock, mock_open, patch

import job_module
import pytest
from cloudpickle import cloudpickle

from braket.aws import AwsQuantumJob
from braket.devices import Devices
from braket.jobs import hybrid_job
from braket.jobs.config import (
    CheckpointConfig,
    InstanceConfig,
    OutputDataConfig,
    S3DataSourceConfig,
    StoppingCondition,
)
from braket.jobs.hybrid_job import _sanitize, _serialize_entry_point
from braket.jobs.local import LocalQuantumJob


@pytest.fixture
def aws_session():
    aws_session = MagicMock()
    python_version_str = f"py{sys.version_info.major}{sys.version_info.minor}"
    aws_session.get_full_image_tag.return_value = f"1.0-cpu-{python_version_str}-ubuntu22.04"
    aws_session.region = "us-west-2"
    return aws_session


@patch.object(sys.modules["braket.jobs.hybrid_job"], "persist_inner_function_source")
@patch.object(sys.modules["braket.jobs.hybrid_job"], "retrieve_image")
@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_decorator_defaults(
    mock_create,
    mock_tempdir,
    _mock_open,
    mock_time,
    mock_retrieve,
    mock_persist_source,
    aws_session,
):
    mock_retrieve.return_value = "00000000.dkr.ecr.us-west-2.amazonaws.com/latest"

    @hybrid_job(device=None, aws_session=aws_session)
    def my_entry(c=0, d: float = 1.0, **extras):
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name
    mock_persist_source.return_value.__enter__.return_value = {}

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
        hyperparameters={"c": "0", "d": "1.0"},
        logger=getLogger("braket.jobs.hybrid_job"),
        aws_session=aws_session,
        input_data={},
    )
    assert mock_tempdir.return_value.__exit__.called


@pytest.mark.parametrize("include_modules", (job_module, ["job_module"]))
@patch.object(sys.modules["braket.jobs.hybrid_job"], "persist_inner_function_source")
@patch("braket.jobs.image_uris.retrieve_image")
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
    mock_retrieve,
    mock_persist_source,
    include_modules,
):
    mock_retrieve.return_value = "should-not-be-used"
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
    reservation_arn = (
        "arn:aws:braket:us-west-2:123456789123:reservation/a1b123cd-45e6-789f-gh01-i234567jk8l9"
    )
    logger = getLogger(__name__)

    with tempfile.TemporaryDirectory() as tempdir:
        Path(tempdir, "temp_dir").mkdir()
        Path(tempdir, "temp_file").touch()

        input_data = {
            "my_prefix": "my_input_data",
            "my_dir": Path(tempdir, "temp_dir"),
            "my_file": Path(tempdir, "temp_file"),
            "my_s3_prefix": "s3://bucket/path/to/prefix",
            "my_s3_config": S3DataSourceConfig(s3_data="s3://bucket/path/to/prefix"),
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
            reservation_arn=reservation_arn,
            logger=logger,
        )
        def my_entry(a, b: int, c=0, d: float = 1.0, **extras) -> str:
            return "my entry return value"

        mock_tempdir = MagicMock(spec=tempfile.TemporaryDirectory)
        mock_tempdir_name = "job_temp_dir_00000"
        mock_tempdir.__enter__.return_value = mock_tempdir_name
        mock_persist_source.return_value.__enter__.return_value = {}

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
        hyperparameters={
            "a": "a",
            "b": "2",
            "c": "3",
            "d": "4",
            "extra_param": "value",
            "another": "6",
        },
        checkpoint_config=checkpoint_config,
        copy_checkpoints_from_job=copy_checkpoints_from_job,
        role_arn=role_arn,
        stopping_condition=stopping_condition,
        output_data_config=output_data_config,
        aws_session=aws_session,
        tags=tags,
        logger=logger,
        reservation_arn=reservation_arn,
    )
    included_module = importlib.import_module("job_module")
    mock_register.assert_called_with(included_module)
    mock_unregister.assert_called_with(included_module)
    mock_copy.assert_called_with(
        Path("my_requirements.txt").resolve(), Path(mock_tempdir_name, "requirements.txt")
    )
    assert mock_tempdir.__exit__.called
    mock_stdout.write.assert_any_call(s3_not_linked)


@patch.object(sys.modules["braket.jobs.hybrid_job"], "persist_inner_function_source")
@patch.object(sys.modules["braket.jobs.hybrid_job"], "retrieve_image")
@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_decorator_non_dict_input(
    mock_create,
    mock_tempdir,
    _mock_open,
    mock_time,
    mock_retrieve,
    mock_persist_source,
    aws_session,
):
    mock_retrieve.return_value = "00000000.dkr.ecr.us-west-2.amazonaws.com/latest"
    input_prefix = "my_input"

    @hybrid_job(device=None, input_data=input_prefix, aws_session=aws_session)
    def my_entry():
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name
    mock_persist_source.return_value.__enter__.return_value = {}

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
        hyperparameters={},
        logger=getLogger("braket.jobs.hybrid_job"),
        input_data={"input": input_prefix},
        aws_session=aws_session,
    )
    assert mock_tempdir.return_value.__exit__.called


@patch.object(sys.modules["braket.jobs.hybrid_job"], "persist_inner_function_source")
@patch.object(sys.modules["braket.jobs.hybrid_job"], "retrieve_image")
@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_decorator_list_dependencies(
    mock_create,
    mock_tempdir,
    _mock_open,
    mock_time,
    mock_retrieve,
    mock_persist_source,
    aws_session,
):
    mock_retrieve.return_value = "00000000.dkr.ecr.us-west-2.amazonaws.com/latest"
    dependency_list = ["dep_1", "dep_2", "dep_3"]

    @hybrid_job(
        device=None,
        aws_session=aws_session,
        dependencies=dependency_list,
    )
    def my_entry(c=0, d: float = 1.0, **extras):
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name
    mock_persist_source.return_value.__enter__.return_value = {}

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
        hyperparameters={"c": "0", "d": "1.0"},
        logger=getLogger("braket.jobs.hybrid_job"),
        input_data={},
        aws_session=aws_session,
    )
    assert mock_tempdir.return_value.__exit__.called
    _mock_open.assert_called_with(
        Path(mock_tempdir_name) / "requirements.txt", "w", encoding="utf-8"
    )
    _mock_open.return_value.__enter__.return_value.write.assert_called_with(
        "\n".join(dependency_list)
    )


@patch.object(sys.modules["braket.jobs.hybrid_job"], "persist_inner_function_source")
@patch.object(sys.modules["braket.jobs.hybrid_job"], "retrieve_image")
@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(LocalQuantumJob, "create")
def test_decorator_local(
    mock_create,
    mock_tempdir,
    _mock_open,
    mock_time,
    mock_retrieve,
    mock_persist_source,
    aws_session,
):
    mock_retrieve.return_value = "00000000.dkr.ecr.us-west-2.amazonaws.com/latest"

    @hybrid_job(device=Devices.Amazon.SV1, local=True, aws_session=aws_session)
    def my_entry():
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name
    mock_persist_source.return_value.__enter__.return_value = {}

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
        input_data={},
        aws_session=aws_session,
    )
    assert mock_tempdir.return_value.__exit__.called


@patch.object(sys.modules["braket.jobs.hybrid_job"], "persist_inner_function_source")
@patch.object(sys.modules["braket.jobs.hybrid_job"], "retrieve_image")
@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(LocalQuantumJob, "create")
def test_decorator_local_unsupported_args(
    mock_create,
    mock_tempdir,
    _mock_open,
    mock_time,
    mock_retrieve,
    mock_persist_source,
    aws_session,
):
    mock_retrieve.return_value = "00000000.dkr.ecr.us-west-2.amazonaws.com/latest"

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
        aws_session=aws_session,
    )
    def my_entry():
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name
    mock_persist_source.return_value.__enter__.return_value = {}

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
        input_data={},
        aws_session=aws_session,
    )
    assert mock_tempdir.return_value.__exit__.called


@patch.object(sys.modules["braket.jobs.hybrid_job"], "persist_inner_function_source")
@patch.object(sys.modules["braket.jobs.hybrid_job"], "retrieve_image")
@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_job_name_too_long(
    mock_create,
    mock_tempdir,
    _mock_open,
    mock_time,
    mock_retrieve,
    mock_persist_source,
    aws_session,
):
    mock_retrieve.return_value = "00000000.dkr.ecr.us-west-2.amazonaws.com/latest"

    @hybrid_job(device="local:braket/default", aws_session=aws_session)
    def this_is_a_50_character_func_name_for_testing_names():
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name
    mock_persist_source.return_value.__enter__.return_value = {}

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
            input_data={},
            aws_session=aws_session,
        )
        assert len(expected_job_name) == 50
        assert mock_tempdir.return_value.__exit__.called


@patch.object(sys.modules["braket.jobs.hybrid_job"], "persist_inner_function_source")
@patch.object(sys.modules["braket.jobs.hybrid_job"], "retrieve_image")
@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_decorator_pos_only_slash(
    mock_create,
    mock_tempdir,
    _mock_open,
    mock_time,
    mock_retrieve,
    mock_persist_source,
    aws_session,
):
    mock_retrieve.return_value = "00000000.dkr.ecr.us-west-2.amazonaws.com/latest"

    @hybrid_job(device="local:braket/default", aws_session=aws_session)
    def my_entry(pos_only, /):
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name
    mock_persist_source.return_value.__enter__.return_value = {}

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
        input_data={},
        aws_session=aws_session,
    )
    assert mock_tempdir.return_value.__exit__.called


@patch.object(sys.modules["braket.jobs.hybrid_job"], "persist_inner_function_source")
@patch.object(sys.modules["braket.jobs.hybrid_job"], "retrieve_image")
@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_decorator_pos_only_args(
    mock_create,
    mock_tempdir,
    _mock_open,
    mock_time,
    mock_retrieve,
    mock_persist_source,
    aws_session,
):
    mock_retrieve.return_value = "00000000.dkr.ecr.us-west-2.amazonaws.com/latest"

    @hybrid_job(device="local:braket/default", aws_session=aws_session)
    def my_entry(*args):
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name
    mock_persist_source.return_value.__enter__.return_value = {}

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
        input_data={},
        aws_session=aws_session,
    )
    assert mock_tempdir.return_value.__exit__.called


@patch("builtins.open", new_callable=mock_open)
@patch.object(sys.modules["os"], "mkdir")
@patch.object(sys.modules["braket.jobs.hybrid_job"], "retrieve_image")
@patch("time.time", return_value=123.0)
@patch("tempfile.TemporaryDirectory")
@patch.object(LocalQuantumJob, "create")
def test_decorator_persist_inner_function_source(
    mock_create, mock_tempdir, mock_time, mock_retrieve, mock_mkdir, mock_file, aws_session
):
    from braket.jobs.hybrid_job import (
        INNER_FUNCTION_SOURCE_INPUT_CHANNEL,
        INNER_FUNCTION_SOURCE_INPUT_FOLDER,
    )

    mock_retrieve.return_value = "00000000.dkr.ecr.us-west-2.amazonaws.com/latest"

    def my_entry():
        def inner_function_1():
            def inner_function_2():
                return "my inner function 2"

            return "my inner function 1"

        return inner_function_1

    inner1 = my_entry()

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name

    device = Devices.Amazon.SV1
    source_module = mock_tempdir_name
    entry_point = f"{mock_tempdir_name}.entry_point:my_entry"

    my_entry = hybrid_job(device=Devices.Amazon.SV1, local=True, aws_session=aws_session)(my_entry)
    my_entry()

    expected_source = "".join(inspect.findsource(inner1)[0])
    assert mock_file().write.call_args_list[0][0][0] == expected_source

    expect_source_path = f"{mock_tempdir_name}/{INNER_FUNCTION_SOURCE_INPUT_FOLDER}/source_0.py"
    assert mock_file.call_args_list[0][0][0] == expect_source_path

    mock_create.assert_called_with(
        device=device,
        source_module=source_module,
        entry_point=entry_point,
        job_name="my-entry-123000",
        hyperparameters={},
        aws_session=aws_session,
        input_data={
            INNER_FUNCTION_SOURCE_INPUT_CHANNEL: f"{mock_tempdir_name}/"
            f"{INNER_FUNCTION_SOURCE_INPUT_FOLDER}"
        },
    )
    assert mock_tempdir.return_value.__exit__.called


@patch.object(sys.modules["braket.jobs.hybrid_job"], "persist_inner_function_source")
@patch.object(sys.modules["braket.jobs.hybrid_job"], "retrieve_image")
@patch("time.time", return_value=123.0)
@patch("builtins.open")
@patch("tempfile.TemporaryDirectory")
@patch.object(AwsQuantumJob, "create")
def test_decorator_conflict_channel_name(
    mock_create,
    mock_tempdir,
    _mock_open,
    mock_time,
    mock_retrieve,
    mock_persist_source,
    aws_session,
):
    from braket.jobs.hybrid_job import INNER_FUNCTION_SOURCE_INPUT_CHANNEL

    mock_retrieve.return_value = "00000000.dkr.ecr.us-west-2.amazonaws.com/latest"

    @hybrid_job(
        device=None,
        aws_session=aws_session,
        input_data={INNER_FUNCTION_SOURCE_INPUT_CHANNEL: "foo-bar"},
    )
    def my_entry(c=0, d: float = 1.0, **extras):
        return "my entry return value"

    mock_tempdir_name = "job_temp_dir_00000"
    mock_tempdir.return_value.__enter__.return_value = mock_tempdir_name
    mock_persist_source.return_value.__enter__.return_value = {}

    expect_error_message = f"input channel cannot be {INNER_FUNCTION_SOURCE_INPUT_CHANNEL}"
    with pytest.raises(ValueError, match=expect_error_message):
        my_entry()


def test_serialization_error(aws_session):
    ssl_context = SSLContext(protocol=PROTOCOL_TLS_CLIENT)

    @hybrid_job(device=None, aws_session=aws_session)
    def fails_serialization():
        print(ssl_context)

    serialization_failed = (
        "Serialization failed for decorator hybrid job. If you are referencing "
        "an object from outside the function scope, either directly or through "
        "function parameters, try instantiating the object inside the decorated "
        "function instead."
    )
    with pytest.raises(RuntimeError, match=serialization_failed):
        fails_serialization()


def test_serialization_wrapping():
    def my_entry(*args, **kwargs):
        print("something with \" and ' and \n")
        return args, kwargs

    args, kwargs = (1, "two"), {"three": 3}
    template = _serialize_entry_point(my_entry, args, kwargs)
    pickled_str = re.search(r"(?s)cloudpickle.loads\((.*?)\)\ndef my_entry", template)[1]
    byte_str = ast.literal_eval(pickled_str)

    recovered = cloudpickle.loads(byte_str)
    assert recovered() == (args, kwargs)


def test_python_validation(aws_session):
    aws_session.get_full_image_tag.return_value = "1.0-cpu-py38-ubuntu22.04"

    bad_version = (
        "Python version must match between local environment and container. "
        f"Client is running Python {sys.version_info.major}.{sys.version_info.minor} "
        "locally, but container uses Python 3.8."
    )
    with pytest.raises(RuntimeError, match=bad_version):

        @hybrid_job(device=None, aws_session=aws_session)
        def my_job():
            pass


@pytest.mark.parametrize(
    "hyperparameter, expected",
    (
        (
            "with\nnewline",
            "with newline",
        ),
        (
            "with weird chars: (&$`)",
            "with weird chars: {+?'}",
        ),
        (
            "?" * 2600,
            f"{'?' * 2477}...{'?' * 20}",
        ),
    ),
)
def test_sanitize_hyperparameters(hyperparameter, expected):
    assert _sanitize(hyperparameter) == expected
