import os
from functools import singledispatch
from typing import Any, Dict, List, Optional, Union

import boto3

from braket.aws.aws_session import AwsSession
from braket.jobs.quantum_job import QuantumJob
from braket.job_services.instance_config import InstanceConfig
from braket.job_services.checkpoint_config import CheckpointConfig
from braket.job_services.metric_definition import MetricDefinition
from braket.job_services.metric_period import MetricPeriod
from braket.job_services.metric_statistic import MetricStatistic
from braket.job_services.output_data_config import OutputDataConfig
from braket.job_services.stopping_condition import StoppingCondition
from braket.job_services.vpc_config import VpcConfig


class AwsQuantumJob(QuantumJob):
    @classmethod
    def create(
        cls,
        aws_session: AwsSession,
        entry_point: str,
        image_uri: str = "Base Image URI",
        code_location: str = None,
        priority_access_device_arn: str = None,
        source_dir: str = None,
        job_name: str = None,
        role_arn: str = None,
        wait: bool = False,
        hyper_parameters: Dict[str, Any] = None,
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
    ):

        """
        Creates a job by invoking the Braket CreateJob API.

        Args:
        entry_point(str): str specifying the 'module' or 'module:method' to be executed as
        an entry point for the job.

        image_uri(str): str specifying the ECR image to use for executing the job.
        `image_uris.retrieve()` function may be used for retrieving the ECR image uris
        for the containers supported by Braket (default: <Braket base image uri>).

        code_location(str): The S3 prefix URI where custom code will be uploaded.
        (default: 's3://braket-{region}-{account}/jobs/{jobname}/source')


        source_dir(str): Path (absolute, relative or an S3 URI) to a directory with any
        other source code dependencies aside from the entry point file. If `source_dir`
        is an S3 URI, it must point to a tar.gz file. Structure within this directory are
        preserved when executing on Amazon Braket.
        (default: None).


        job_name(str): str representing the name with which the job will be created.
        (default: {image_type<base/tensorflow/pytorch/jax>}:{timestamp})

        metric_definitions(List[MetricDefinition]): A list of MetricDefinitions that
        defines the metric(s) used to evaluate the training jobs.
        (default: None)

        role_arn(str): str representing the IAM role arn to be used for executing the
        script. (default: IAM role returned by get_execution_role())

        wait(bool): bool representing whether we should wait until the job completes.
        This would tail the job logs as it waits (default: False)

        priority_access_device_arn(str): ARN for the AWS device which should have priority
        access for the execution of this job. (default: None)

        hyperparameters(Dict[str, Any]): Hyperparameters that will be made accessible to
        the job. The hyperparameters are made accessible as a Dict[str, str] to the
        job. For convenience, this accepts other types for keys and values, but
        `str()` will be called to convert them before being passed on. (default: None)

        input_data_config(Union[str, Dict[str, str], JobInputData]): Information
        about the training data. Similar to SageMaker's Estimator.fit() inputs
        parameter. See https://tiny.amazon.com/41g8elq8/githawssageblobmastsrcsage
        for details. (default: None)

        instance_config(InstanceConfig): Configuration of the instances to be used for
        executing the job.
        (default: InstanceConfig(instanceType='ml.m5.large', instanceCount=1,
        volumeSizeInGB=30, volumeKmsKey=None))

        stopping_condition(StoppingCondition): Conditions denoting when the job should be
        forcefully stopped.
        (default: StoppingCondition(maxRuntimeInSeconds=5 * 24 * 60 * 60,
        maxTaskLimit=100,000))

        output_data_config(OutputDataConfig): Configuration specifying the location for
        the output of the job.
        (default:
        OutputDataConfig(s3Path=s3://braket-{region}-{account}/jobs/{jobname}/output,
        kmsKeyId=None))

        copy_checkpoints_from_job(str): str specifying the job name whose checkpoint you wish
        to use in the current job. Specifying this value will copy over the checkpoint
        data from `use_checkpoints_from_job`'s checkpoint_config s3Uri to the current job's
        checkpoint_config s3Uri, making it available at checkpoint_config.localPath during the
        job execution.

        checkpoint_config(CheckPointConfig): Configuration specifying the location where
        checkpoint data would be stored.
        (default:
        CheckpointConfig(localPath='/opt/jobs/checkpoints',
        s3Uri='s3://braket-{region}-{account}/jobs/{jobname}/checkpoints'))

        vpc_config(VpcConfig): Configuration specifying the security groups and subnets
        to use for running the job.
        (default: None)

        tags(Dict[str, str]): Dict specifying the Key-Value pairs to tag the quantum job with.
        (default: None)

        Returns:
        Job: Job tracking the execution on Amazon Braket."""

        """
        [IMPLEMENT]
        
        if entry_point file is provided, then we raise the error. 
        
        if code_location is not provided by the customer, 
        then we default it with the bucket_name with we get from the AwsSession object.

        default => code_location:str = "s3://braket-{region}-{account}/jobs/{jobname}/source"
        """

        pass

    def __init__(
        self,
        arn: str,
        aws_session: AwsSession = None,
    ):
        self._arn: str = arn
        self._aws_session: AwsSession = aws_session or AwsQuantumJob._aws_session_for_job_arn(
            job_arn=arn
        )

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
        """Returns the job arn corresponding to the job"""
        return self._arn

    @property
    def state(self) -> str:
        """Returns the status for the job"""
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
        """
        Note: The function definition here is subject to change depending on our metric
        strategy for the console.

        Queries cloudwatch to retrieve the metric values for the specified metric_names
        for the job.

        Args:
          metric_names(List[str]): Metric names to retrieve for the job.
             (default: All custom metrics + host metrics)
          period(MetricPeriod): Period over which the cloudwatch metric is aggregated.
             (default: MetricPeriod.ONE_MINUTE)
          statistic(MetricStatistic): Metric data aggregation to use over the specified
             period. (default: MetricStatistic.AVG)

        Returns:
           Dict[str, Any]: Dict containing the metric information represented with the keys
           "timestamp", "metric_name" and "value" """
        pass

    def cancel(self) -> str:
        """Cancels the job

        Returns:
            str: Representing the status of the job."""
        pass

    def result(self) -> str:
        """
        Retrieves the job result persisted using save_job_result() function.

        Returns:
            Dict[str, Any]: Dict specifying the job results."""

        pass

    def download_results(self, extract_to=None) -> None:
        """Downloads the results from the job output S3 bucket and extracts the tar.gz
        bundle to the location specified by 'extract_to'. If no location is specified,
        the results are extracted to the current directory."""

        pass


# Calling the create method with the AwsQuantumJob class
"""
job = AwsQuantumJob.create(
    entry_point="vqe",
    metricDefinitions=[
        MetricDefinition(name="energy", regex="energyHa=(.*?);"),
        MetricDefinition("convergence", "convergence_parameter=(.*?);"),
    ],
    copy_checkpoints_from_job="my_last_job",
    src_dir=os.getcwd(),
    image_uri=image_uris.retrieve(framework="pytorch", framework_version="1.8", py_version="3.7"),
    hyper_parameters={"basis_set": "sto-3g", "charge": 0, "multiplicity": 1},
    priority_access_device_arn="arn:aws:braket:::device/qpu/rigetti/Aspen-9",
)
"""
