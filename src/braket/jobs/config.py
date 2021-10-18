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
    """Configuration that specifies the location where checkpoint data is stored."""

    localPath: str = "/opt/jobs/checkpoints"
    s3Uri: Optional[str] = None


@dataclass
class InstanceConfig:
    """Configuration of the instances used to execute the job."""

    instanceType: str = "ml.m5.large"
    instanceCount: int = 1
    volumeSizeInGb: int = 30
    volumeKmsKeyId = None


@dataclass
class OutputDataConfig:
    """Configuration that specifies the location for the output of the job."""

    s3Path: Optional[str] = None
    kmsKeyId = None


@dataclass
class StoppingCondition:
    """Conditions that specify when the job should be forcefully stopped."""

    maxRuntimeInSeconds: int = 5 * 24 * 60 * 60


@dataclass
class VpcConfig:
    # TODO: Add securityGroupIds and subnets default values here.
    # TODO: Ensure that length of the list for securityGroupIds is between 1 and 5
    # and for subnets between 1 and 16.
    """Configuration that specifies the security groups and subnets to use for running the job."""

    securityGroupIds: List[str]
    subnets: List[str]


@dataclass
class DeviceConfig:
    devices: List[str] = field(default_factory=list)


class S3DataSourceConfig:
    """
    Data source for data that lives on S3
    Attributes:
        config (dict[str, dict]): config passed to the Braket API
    """

    class DistributionType:
        FULLY_REPLICATED = "FULLY_REPLICATED"
        SHARDED_BY_S3_KEY = "SHARDED_BY_S3_KEY"

    class S3DataType:
        S3_PREFIX = "S3_PREFIX"
        MANIFEST_FILE = "MANIFEST_FILE"

    def __init__(
        self,
        s3_data,
        distribution=DistributionType.FULLY_REPLICATED,
        content_type=None,
        s3_data_type=S3DataType.S3_PREFIX,
    ):
        """Create a definition for input data used by a Braket job.

        Args:
            s3_data (str): Defines the location of s3 data to train on.
            distribution (str): Valid values: 'FullyReplicated', 'ShardedByS3Key'
                (default: 'FullyReplicated').
            content_type (str): MIME type of the input data (default: None).
            s3_data_type (str): Valid values: 'S3Prefix', 'ManifestFile'.
                If 'S3Prefix', ``s3_data`` defines a prefix of s3 objects to train on.
                All objects with s3 keys beginning with ``s3_data`` will be used to train.
                If 'ManifestFile', then ``s3_data`` defines a single S3 manifest file,
                listing the S3 data to train on.
        """
        self.config = {
            "dataSource": {
                "s3DataSource": {
                    "s3DataType": s3_data_type,
                    "s3Uri": s3_data,
                    "s3DataDistributionType": distribution,
                }
            }
        }

        if content_type is not None:
            self.config["contentType"] = content_type
