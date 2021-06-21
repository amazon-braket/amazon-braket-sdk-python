# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from dataclasses import dataclass
from typing import List

# TODO: Decide on where default_bucket_name should be defined. If bucket is not present
# in the customer's account then raise ValidationException.


@dataclass
class CheckpointConfig:
    """Configuration specifying the location where checkpoint data would be stored."""

    # TODO: Might have to add the default_bucket_name and jobname as a parameter for using here.
    # TODO: job_name = image_uri_type + current_timestamp
    localPath: str = "/opt/jobs/checkpoints"
    s3Uri: str = "s3://{default_bucket_name}/jobs/{job_name}/checkpoints"


@dataclass
class InstanceConfig:
    """Configuration of the instances to be used for executing the job."""

    instanceType: str = "ml.m5.large"
    instanceCount: int = 1
    volumeSizeInGB: int = 30
    volumeKmsKey: str = None


@dataclass
class OutputDataConfig:
    """Configuration specifying the location for the output of the job."""

    # TODO: Might have to add the default_bucket_name and jobname as a parameter for using here.
    s3Path = "s3://{default_bucket_name}/jobs/{job_name}/output"
    kmsKeyId = None


@dataclass
class StoppingCondition:
    """Conditions denoting when the job should be forcefully stopped."""

    maxRuntimeInSeconds: int = 100_000
    maxTaskLimit: int = 5 * 24 * 60 * 60


@dataclass
class VpcConfig:
    # TODO: Add securityGroupIds and subnets default values here.
    # TODO: Ensure that length of the list for securityGroupIds is between 1 and 5
    # and for subnets between 1 and 16.
    """Configuration specifying the security groups and subnets to use for running the job."""
    securityGroupIds: List[str]
    subnets: List[str]
