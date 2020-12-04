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

from typing import Any, Dict, List, NamedTuple, Optional

import backoff
import boto3
from botocore.exceptions import ClientError


class AwsSession(object):
    """Manage interactions with AWS services."""

    S3DestinationFolder = NamedTuple("S3DestinationFolder", [("bucket", str), ("key", int)])

    def __init__(self, boto_session=None, braket_client=None, config=None):
        """
        Args:
            boto_session: A boto3 session object.
            braket_client: A boto3 Braket client.
            config: A botocore Config object.
        """

        self.boto_session = boto_session or boto3.Session()
        self._config = config

        if braket_client:
            self.braket_client = braket_client
        else:
            self.braket_client = self.boto_session.client("braket", config=self._config)

    #
    # Quantum Tasks
    #
    def cancel_quantum_task(self, arn: str) -> None:
        """
        Cancel the quantum task.

        Args:
            arn (str): The ARN of the quantum task to cancel.
        """
        self.braket_client.cancel_quantum_task(quantumTaskArn=arn)

    def create_quantum_task(self, **boto3_kwargs) -> str:
        """
        Create a quantum task.

        Args:
            **boto3_kwargs: Keyword arguments for the Amazon Braket `CreateQuantumTask` operation.

        Returns:
            str: The ARN of the quantum task.
        """
        response = self.braket_client.create_quantum_task(**boto3_kwargs)
        return response["quantumTaskArn"]

    @staticmethod
    def _should_giveup(err):
        return not (
            isinstance(err, ClientError)
            and err.response["Error"]["Code"]
            in [
                "ResourceNotFoundException",
                "ThrottlingException",
            ]
        )

    @backoff.on_exception(
        backoff.expo,
        ClientError,
        max_tries=3,
        jitter=backoff.full_jitter,
        giveup=_should_giveup.__func__,
    )
    def get_quantum_task(self, arn: str) -> Dict[str, Any]:
        """
        Gets the quantum task.

        Args:
            arn (str): The ARN of the quantum task to get.

        Returns:
            Dict[str, Any]: The response from the Amazon Braket `GetQuantumTask` operation.
        """
        return self.braket_client.get_quantum_task(quantumTaskArn=arn)

    def retrieve_s3_object_body(self, s3_bucket: str, s3_object_key: str) -> str:
        """
        Retrieve the S3 object body.

        Args:
            s3_bucket (str): The S3 bucket name.
            s3_object_key (str): The S3 object key within the `s3_bucket`.

        Returns:
            str: The body of the S3 object.
        """
        s3 = self.boto_session.resource("s3", config=self._config)
        obj = s3.Object(s3_bucket, s3_object_key)
        return obj.get()["Body"].read().decode("utf-8")

    def get_device(self, arn: str) -> Dict[str, Any]:
        """
        Calls the Amazon Braket `get_device` API to
        retrieve device metadata.

        Args:
            arn (str): The ARN of the device.

        Returns:
            Dict[str, Any]: The response from the Amazon Braket `GetDevice` operation.
        """
        return self.braket_client.get_device(deviceArn=arn)

    def search_devices(
        self,
        arns: Optional[List[str]] = None,
        names: Optional[List[str]] = None,
        types: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        provider_names: Optional[List[str]] = None,
    ):
        """
        Get devices based on filters. The result is the AND of
        all the filters `arns`, `names`, `types`, `statuses`, `provider_names`.

        Args:
            arns (List[str], optional): device ARN list, default is `None`.
            names (List[str], optional): device name list, default is `None`.
            types (List[str], optional): device type list, default is `None`.
            statuses (List[str], optional): device status list, default is `None`.
            provider_names (List[str], optional): provider name list, default is `None`.

        Returns:
            List[Dict[str, Any]: The response from the Amazon Braket `SearchDevices` operation.
        """
        filters = []
        if arns:
            filters.append({"name": "deviceArn", "values": arns})
        paginator = self.braket_client.get_paginator("search_devices")
        page_iterator = paginator.paginate(filters=filters, PaginationConfig={"MaxItems": 100})
        results = []
        for page in page_iterator:
            for result in page["devices"]:
                if names and result["deviceName"] not in names:
                    continue
                if types and result["deviceType"] not in types:
                    continue
                if statuses and result["deviceStatus"] not in statuses:
                    continue
                if provider_names and result["providerName"] not in provider_names:
                    continue
                results.append(result)
        return results
