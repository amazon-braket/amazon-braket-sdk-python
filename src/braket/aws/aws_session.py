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

from typing import Any, Dict, NamedTuple

import backoff
import boto3
from botocore.exceptions import ClientError


class AwsSession(object):
    """Manage interactions with AWS services."""

    S3DestinationFolder = NamedTuple("S3DestinationFolder", [("bucket", str), ("key", int)])

    def __init__(self, boto_session=None, braket_client=None):
        """
        Args:
            boto_session: A boto3 session object
            braket_client: A boto3 Braket client
        """

        self.boto_session = boto_session or boto3.Session()

        if braket_client:
            self.braket_client = braket_client
        else:
            self.braket_client = self.boto_session.client("braket")

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
        Retrieve the S3 object body

        Args:
            s3_bucket (str): The S3 bucket name
            s3_object_key (str): The S3 object key within the `s3_bucket`

        Returns:
            str: The body of the S3 object
        """
        s3 = self.boto_session.resource("s3")
        obj = s3.Object(s3_bucket, s3_object_key)
        return obj.get()["Body"].read().decode("utf-8")

    def get_device(self, arn: str) -> Dict[str, Any]:
        """
        Calls the Amazon Braket `get_device` API to
        retrieve device metadata

        Args:
            arn (str): The ARN of the device

        Returns:
            Dict[str, Any]: Device metadata
        """
        return self.braket_client.get_device(deviceArn=arn)
