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

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CheckpointConfig:
    """Configuration that specifies the location where checkpoint data is stored."""

    localPath: str = "/opt/jobs/checkpoints"
    s3Uri: str | None = None


@dataclass
class InstanceConfig:
    """Configuration of the instance(s) used to run the hybrid job."""

    instanceType: str = "ml.m5.large"
    volumeSizeInGb: int = 30
    instanceCount: int = 1


@dataclass
class OutputDataConfig:
    """Configuration that specifies the location for the output of the hybrid job."""

    s3Path: str | None = None
    kmsKeyId: str | None = None


@dataclass
class StoppingCondition:
    """Conditions that specify when the hybrid job should be forcefully stopped."""

    maxRuntimeInSeconds: int = 5 * 24 * 60 * 60


@dataclass
class DeviceConfig:
    device: str


class S3DataSourceConfig:
    """
    Data source for data that lives on S3
    Attributes:
        config (dict[str, dict]): config passed to the Braket API
    """

    def __init__(
        self,
        s3_data: str,
        content_type: str = None,
    ):
        """Create a definition for input data used by a Braket Hybrid job.

        Args:
            s3_data (str): Defines the location of s3 data to train on.
            content_type (str): MIME type of the input data (default: None).
        """
        self.config = {
            "dataSource": {
                "s3DataSource": {
                    "s3Uri": s3_data,
                }
            }
        }

        if content_type is not None:
            self.config["contentType"] = content_type
