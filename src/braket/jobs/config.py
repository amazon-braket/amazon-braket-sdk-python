# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CheckpointConfig:
    """Configuration specifying the location where checkpoint data would be stored."""

    localPath: str = "/opt/jobs/checkpoints"
    s3Uri: Optional[str] = None


@dataclass
class InstanceConfig:
    """Configuration of the instances to be used for executing the job."""

    instanceType: str = "ml.m5.large"
    instanceCount: int = 1
    volumeSizeInGb: int = 30
    volumeKmsKeyId = None


@dataclass
class S3DataSource:
    s3Uri: Optional[str] = None
    s3DataType: str = "S3_PREFIX"


@dataclass
class DataSource:
    s3DataSource: S3DataSource = S3DataSource()


@dataclass
class InputDataConfig:
    """Configuration specifying the location for the output of the job."""

    # TODO: test multiple channels with the same name in integ test
    channelName: str = "input"
    dataSource: DataSource = DataSource()
    compressionType: str = "NONE"


@dataclass
class OutputDataConfig:
    """Configuration specifying the location for the output of the job."""

    s3Path: Optional[str] = None
    kmsKeyId = None


@dataclass
class StoppingCondition:
    """Conditions denoting when the job should be forcefully stopped."""

    maxRuntimeInSeconds: int = 100_000
    # TODO: remove this when change is propagated
    maximumTaskLimit: int = 5 * 24 * 60 * 60


@dataclass
class VpcConfig:
    # TODO: Add securityGroupIds and subnets default values here.
    # TODO: Ensure that length of the list for securityGroupIds is between 1 and 5
    # and for subnets between 1 and 16.
    """Configuration specifying the security groups and subnets to use for running the job."""
    securityGroupIds: List[str]
    subnets: List[str]


@dataclass
class PriorityAccessConfig:
    devices: List[str] = field(default_factory=list)


@dataclass
class DeviceConfig:
    priorityAccess: PriorityAccessConfig = PriorityAccessConfig()


@dataclass
class PollingConfig:
    pollTimeoutSeconds: float = 864000
    pollIntervalSeconds: float = 1
