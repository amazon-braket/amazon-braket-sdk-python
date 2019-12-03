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

import boto3

# TODO: remove this once we have prod stages
PDX_BETA_URL = "https://4tetbmwz5k.execute-api.us-west-2.amazonaws.com/Prod"


class AwsSession(object):
    S3DestinationFolder = NamedTuple("S3DestinationFolder", [("bucket", str), ("key", int)])

    """
    Manage interactions with AWS services

    Args:
        boto_session: boto3 session object
        braket_client: boto3 braket client
    """

    # similar to sagemaker sdk:
    # https://github.com/aws/sagemaker-python-sdk/blob/master/src/sagemaker/session.py
    def __init__(self, boto_session=None, braket_client=None):
        self.boto_session = boto_session or boto3.Session()
        self.braket_client = braket_client or self.boto_session.client(
            "aqx", endpoint_url=PDX_BETA_URL
        )

    #
    # Quantum Tasks
    #
    def cancel_quantum_task(self, arn: str) -> None:
        """
        Cancel the quantum task.

        Args:
            arn (str): ARN of the quantum task to cancel.
        """
        self.braket_client.cancel_quantum_task(quantumTaskArn=arn)

    def create_quantum_task(self, **boto3_kwargs) -> str:
        """
        Create a quantum task.

        Args:
            **boto3_kwargs: Keyword arguments for the Braket CreateQuantumTask API.

        Returns:
            str: Quantum task ARN.
        """
        response = self.braket_client.create_quantum_task(**boto3_kwargs)
        return response["quantumTaskArn"]

    def get_quantum_task(self, arn: str) -> Dict[str, Any]:
        """
        Get the quantum task.

        Args:
            arn (str): ARN of the quantum task to cancel.

        Returns:
            Dict[str, Any]: Braket GetQuantumTask API result.
        """
        return self.braket_client.get_quantum_task(quantumTaskArn=arn)

    def retrieve_s3_object_body(self, s3_bucket: str, s3_object_key: str) -> str:
        """
        Retrieve S3 object body

        Args:
            s3_bucket (str): S3 bucket name
            s3_object_key (str): S3 object key within `s3_bucket`

        Returns:
            str: Body of S3 object
        """
        s3 = self.boto_session.resource("s3")
        obj = s3.Object(s3_bucket, s3_object_key)
        return obj.get()["Body"].read().decode("utf-8")

    # TODO: add in boto3 exception handling once we have exception types in API
    def get_qpu_metadata(self, arn: str) -> Dict[str, Any]:
        """
        Call AWS API describe_qpus to return metadata about QPU

        Args:
            arn (str): QPU ARN

        Returns:
            Dict[str, Any]: QPU metadata
        """
        try:
            response = self.braket_client.describe_qpus(qpuArns=[arn])
            qpu_metadata = response.get("qpus")[0]
            return qpu_metadata
        except Exception as e:
            raise e

    # TODO: add in boto3 exception handling once we have exception types in API
    def get_simulator_metadata(self, arn: str) -> Dict[str, Any]:
        """
        Call AWS API describe_quantum_simulators to return metadata about simulator

        Args:
            arn (str): simulator ARN

        Returns:
            Dict[str, Any]: simulator metadata
        """
        try:
            response = self.braket_client.describe_quantum_simulators(quantumSimulatorArns=[arn])
            simulator_metadata = response.get("quantumSimulators")[0]
            return simulator_metadata
        except Exception as e:
            raise e
