import boto3
import pytest
from botocore.config import Config

from braket.ahs.analog_hamiltonian_simulation import (
    AnalogHamiltonianSimulation,
    AtomArrangement,
    DrivingField,
    ShiftingField,
    SiteType,
)
from braket.ahs.field import Field
from braket.ahs.pattern import Pattern
from braket.ahs.time_series import TimeSeries
from braket.aws import AwsDevice, AwsSession


@pytest.fixture
def register():
    return (
        AtomArrangement()
        .add((0.0, 0.0))
        .add((0.0, 4.0e-6))
        .add((5.0e-6, 0.0))
        .add((5.0e-6, 4.0e-6))
    )


@pytest.fixture
def driving_field():
    return DrivingField(
        amplitude=TimeSeries()
        .put(0.0, 0.0)
        .put(1.0e-7, 12566400.0)
        .put(3.9e-6, 12566400.0)
        .put(4.0e-6, 0.0),
        phase=TimeSeries()
        .put(0.0, 0.0)
        .put(1.0e-7, 0.0)
        .put(3.9e-6, -16.0832)
        .put(4.0e-6, -16.0832),
        detuning=TimeSeries()
        .put(0.0, -125000000)
        .put(1.0e-7, -125000000)
        .put(3.9e-6, 125000000)
        .put(4.0e-6, 125000000),
    )


@pytest.fixture
def shifting_field():
    return ShiftingField(
        Field(
            TimeSeries().put(0.0, 0).put(4.0e-6, 125000000),
            Pattern([0.0, 1.0, 0.5, 0.0]),
        )
    )


def test_ahs(register, driving_field, shifting_field):
    endpoint = "https://braket-gamma.us-east-1.amazonaws.com"
    braket_client = boto3.client(
        "braket", endpoint_url=endpoint, config=Config(region_name="us-east-1")
    )
    boto_session = boto3.Session(region_name="us-east-1")
    aws_session = AwsSession(braket_client=braket_client, boto_session=boto_session)

    info = aws_session.get_device("arn:aws:braket:us-east-1::device/qpu/quera/Aquila")
    print(info)

    device = AwsDevice("arn:aws:braket:us-east-1::device/qpu/quera/Aquila", aws_session)
    hamiltonian = driving_field + shifting_field
    ahs = AnalogHamiltonianSimulation(register=register, hamiltonian=hamiltonian)
    run_result = device.run(ahs)
    print(run_result)
