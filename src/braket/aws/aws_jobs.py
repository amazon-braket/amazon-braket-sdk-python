import os
from functools import singledispatch
from test.integ_tests.conftest import aws_session
from typing import Any, Dict, List, Optional, Union

import boto3

from braket.annealing.problem import Problem
from braket.aws.aws_quantum_task import _create_annealing_device_params
from braket.aws.aws_session import AwsSession
from braket.circuits.circuit import Circuit
from braket.circuits.circuit_helpers import validate_circuit_and_shots
from braket.device_schema import GateModelParameters
from braket.device_schema.dwave import (
    Dwave2000QDeviceParameters,
    DwaveAdvantageDeviceParameters,
    DwaveDeviceParameters,
)
from braket.device_schema.dwave.dwave_2000Q_device_level_parameters_v1 import (
    Dwave2000QDeviceLevelParameters,
)
from braket.device_schema.dwave.dwave_advantage_device_level_parameters_v1 import (
    DwaveAdvantageDeviceLevelParameters,
)
from braket.device_schema.ionq import IonqDeviceParameters
from braket.device_schema.rigetti import RigettiDeviceParameters
from braket.device_schema.simulators import GateModelSimulatorDeviceParameters
from braket.schema_common import BraketSchemaBase
from braket.task_result import AnnealingTaskResult, GateModelTaskResult
from braket.tasks.quantum_job import QuantumJob
from braket.utils.checkpoint_config import CheckpointConfig
from braket.utils.instance_config import InstanceConfig
from braket.utils.metric_definition import MetricDefinition
from braket.utils.metric_period import MetricPeriod
from braket.utils.metric_statistic import MetricStatistic
from braket.utils.output_data_config import OutputDataConfig
from braket.utils.stopping_condition import StoppingCondition
from braket.utils.vpc_config import VpcConfig

########################################## MAIN CLASS ##################################################


class AwsQuantumJob(QuantumJob):
    @classmethod
    def create(
        cls,
        aws_session: AwsSession,
        entry_point: str,
        image_uri: str = "Base Image URI",
        code_location: str = "s3://braket-{region}-{account}/jobs/{jobname}/source",
        priority_access_device_arn: str = None,
        source_dir: str = None,
        job_name: str = None,
        role_arn: str = None,
        wait: bool = False,
        hyperParameters: Dict[str, Any] = None,
        metric_definitions: List[MetricDefinition] = None,
        input_data_config: Union[Any] = None,
        instance_config: InstanceConfig = InstanceConfig(),
        stopping_condition: StoppingCondition = StoppingCondition(),
        output_data_config: OutputDataConfig = OutputDataConfig(),
        copy_checkpoints_from_job: str = None,
        checkpoint_config: CheckpointConfig = CheckpointConfig(),
        vpc_config: VpcConfig = None,
        tags: Dict[str, str] = None,
        *args,
        **kwargs,
    ) -> AwsQuantumJob:

        # @classmethod
        # def _is_source_dir(cls, source_dir):
        #     return isinstance(source_dir, str) and source_dir.startswith("s3://")

        # if entrypoint is None:
        #     raise ValueError("Please enter the module for entry point")

        return _create_internal(
            aws_session,
            entry_point,
            image_uri,
            code_location,
            *args,
            **kwargs,
        )

    def __init__(
        self,
        arn: str,
        aws_session: AwsSession = None,
    ):
        self._arn: str = arn
        self._aws_session: AwsSession = aws_session or AwsQuantumJob._aws_session_for_job_arn(
            task_arn=arn
        )
        self._status = "client.get_status"

    @staticmethod
    def _aws_session_for_job_arn(job_arn: str) -> AwsSession:
        """
        Get an AwsSession for the Job ARN. The AWS session should be in the region of the task.

        Returns:
            AwsSession: `AwsSession` object with default `boto_session` in job's region.
        """
        job_region = job_arn.split(":")[3]
        boto_session = boto3.Session(region_name=job_region)
        return AwsSession(boto_session=boto_session)

    @property
    def arn(self) -> str:
        return self._arn

    @property
    def state(self) -> str:
        return self._aws_session.get_job(self.arn)

    def logs(self) -> None:
        """Prints the logs from cloudwatch to stdout"""
        pass

    def metadata(self) -> Dict[str, Any]:
        """Returns the job metadata defined in Amazon Braket (uses the GetJob API call)"""
        pass

    def metrics(
        self,
        metric_names: List[str] = None,
        period: MetricPeriod = MetricPeriod.ONE_MINUTE,
        statistic: MetricStatistic = MetricStatistic.AVG,
    ) -> Dict[str, Any]:
        pass

    def cancel(self) -> str:
        pass

    def result(self) -> str:
        pass

    def download_results(self, extract_to=None) -> None:
        pass


@singledispatch
def _create_internal(
    task_specification: Union[Circuit, Problem],
    aws_session: AwsSession,
    create_task_kwargs: Dict[str, Any],
    priority_access_device_arn: str,
    device_parameters: Union[dict, BraketSchemaBase],
    disable_qubit_rewiring,
    *args,
    **kwargs,
) -> AwsQuantumJob:
    raise TypeError("Invalid job specification type")


@_create_internal.register
def _(
    circuit: Circuit,
    aws_session: AwsSession,
    create_task_kwargs: Dict[str, Any],
    priority_access_device_arn: str,
    device_parameters: Union[dict, BraketSchemaBase],  # Not currently used for circuits
    disable_qubit_rewiring,
    *args,
    **kwargs,
) -> AwsQuantumJob:
    validate_circuit_and_shots(circuit, create_task_kwargs["shots"])

    # TODO: Update this to use `deviceCapabilities` from Amazon Braket's GetDevice operation
    # in order to decide what parameters to build.
    paradigm_parameters = GateModelParameters(
        qubitCount=circuit.qubit_count, disableQubitRewiring=disable_qubit_rewiring
    )
    if "ionq" in priority_access_device_arn:
        device_parameters = IonqDeviceParameters(paradigmParameters=paradigm_parameters)
    elif "rigetti" in priority_access_device_arn:
        device_parameters = RigettiDeviceParameters(paradigmParameters=paradigm_parameters)
    else:  # default to use simulator
        device_parameters = GateModelSimulatorDeviceParameters(
            paradigmParameters=paradigm_parameters
        )

    create_task_kwargs.update(
        {"action": circuit.to_ir().json(), "deviceParameters": device_parameters.json()}
    )
    task_arn = aws_session.create_job(**create_task_kwargs)
    return AwsQuantumJob(task_arn, aws_session, *args, **kwargs)


@_create_internal.register
def _(
    problem: Problem,
    aws_session: AwsSession,
    create_task_kwargs: Dict[str, Any],
    priority_access_device_arn: str,
    device_parameters: Union[
        dict,
        DwaveDeviceParameters,
        DwaveAdvantageDeviceParameters,
        Dwave2000QDeviceParameters,
    ],
    disable_qubit_rewiring,
    *args,
    **kwargs,
) -> AwsQuantumJob:
    device_params = _create_annealing_device_params(device_parameters, priority_access_device_arn)
    create_task_kwargs.update(
        {
            "action": problem.to_ir().json(),
            "deviceParameters": device_params.json(exclude_none=True),
        }
    )

    task_arn = aws_session.create_job(**create_task_kwargs)
    return AwsQuantumJob(task_arn, aws_session, *args, **kwargs)


def _create_annealing_device_params(device_params, priority_access_device_arn):
    if type(device_params) is not dict:
        device_params = device_params.dict()

    # check for device level or provider level parameters
    device_level_parameters = device_params.get("deviceLevelParameters", None) or device_params.get(
        "providerLevelParameters", {}
    )

    # deleting since it may be the old version
    if "braketSchemaHeader" in device_level_parameters:
        del device_level_parameters["braketSchemaHeader"]

    if "Advantage" in priority_access_device_arn:
        device_level_parameters = DwaveAdvantageDeviceLevelParameters.parse_obj(
            device_level_parameters
        )
        return DwaveAdvantageDeviceParameters(deviceLevelParameters=device_level_parameters)
    elif "2000Q" in priority_access_device_arn:
        device_level_parameters = Dwave2000QDeviceLevelParameters.parse_obj(device_level_parameters)
        return Dwave2000QDeviceParameters(deviceLevelParameters=device_level_parameters)
    else:
        raise Exception(
            f"Amazon Braket could not find a device with ARN: {priority_access_device_arn}. "
            "To continue, make sure that the value of the priority_access_device_arn parameter "
            "corresponds to a valid QPU."
        )


# Calling the class method directly with the AwsQuantumJob class
# job = AwsQuantumJob.create(
#     "vqe",
#     metric_definitions=[
#         MetricDefinition(name="energy", regex="energyHa=(.*?);"),
#         MetricDefinition("convergence", "convergence_parameter=(.*?);"),
#     ],
#     copy_checkpoints_from_job="my_last_job",
#     source_dir=os.getcwd(),
#     # image_uri=image_uris.retrieve(framework="pytorch", framework_version="1.8", py_version="3.7"),
#     hyperParameters={"basis_set": "sto-3g", "charge": 0, "multiplicity": 1},
#     priority_access_device_arn="arn:aws:braket:::device/qpu/rigetti/Aspen-9",
# )
