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

import os.path
from typing import Any, Dict, List, NamedTuple, Optional

import backoff
import boto3
from botocore.exceptions import ClientError

import braket._schemas as braket_schemas
import braket._sdk as braket_sdk


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
        self._update_user_agent()
        self._default_bucket = None

    def _update_user_agent(self):
        """
        Updates the `User-Agent` header forwarded by boto3 to include the braket-sdk,
        braket-schemas and the notebook instance version. The header is a string of space delimited
        values (For example: "Boto3/1.14.43 Python/3.7.9 Botocore/1.17.44"). See:
        https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config
        """

        def _notebook_instance_version():
            # TODO: Replace with lifecycle configuration version once we have a way to access those
            nbi_metadata_path = "/opt/ml/metadata/resource-metadata.json"
            return "0" if os.path.exists(nbi_metadata_path) else "None"

        additional_user_agent_fields = (
            f"BraketSdk/{braket_sdk.__version__} "
            f"BraketSchemas/{braket_schemas.__version__} "
            f"NotebookInstance/{_notebook_instance_version()}"
        )

        self.braket_client._client_config.user_agent = (
            f"{self.braket_client._client_config.user_agent} {additional_user_agent_fields}"
        )

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

    def create_job(self, **boto3_kwargs) -> str:
        """
        Create a quantum job.
        Args:
            **boto3_kwargs: Keyword arguments for the Amazon Braket `CreateJob` operation.
        Returns:
            str: The ARN of the job.
        """
        response = self.braket_client.create_job(**boto3_kwargs)
        return response["jobArn"]

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

    def get_execution_role(self) -> str:
        """Return the role ARN whose credentials are used to call the API.
           Throws an exception if role doesn't exist.

        Args:
            aws_session (AwsSession): Current braket session.

        Returns:
            (str): The execution role ARN.
        """
        iam = self.boto_session.resource("iam", region_name=self.boto_session.region_name)
        # TODO: possibly wrap this call with a more specific error message
        role = iam.Role(name="AmazonBraketInternalSLR")
        return role.arn

    # TODO: Implementation suggestions, uncomment when ready with tests.
    @backoff.on_exception(
        backoff.expo,
        ClientError,
        max_tries=3,
        jitter=backoff.full_jitter,
        giveup=_should_giveup.__func__,
    )
    def get_job(self, arn: str) -> str:
        """
        Gets the quantum job.

        Args:
            arn (str): The ARN of the quantum job to get.

        Returns:
            Dict[str, Any]: The response from the Amazon Braket `GetQuantumJob` operation.
        """
        # return self.braket_client.get_job(jobArn=arn)

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

    def upload_to_s3(self, filename: str, s3_uri: str) -> None:
        """
        Upload file to S3

        Args:
            filename (str): local file to be uploaded.
            s3_uri (str): The S3 uri where the file will be uploaded.

        Returns:
            None
        """
        bucket, key = self.parse_s3_uri(s3_uri)
        s3 = self.boto_session.client("s3", config=self._config)
        s3.upload_file(filename, bucket, key)

    def copy_s3(self, source_s3_uri: str, destination_s3_uri: str) -> None:
        """
        Copy source from another location in s3

        Args:
            'source_s3_uri': S3 uri pointing to a tar.gz file containing the source code.
            'destination_s3_uri': S3 uri where the code will be copied.
        """
        source_bucket, source_key = self.parse_s3_uri(source_s3_uri)
        destination_bucket, destination_key = self.parse_s3_uri(destination_s3_uri)

        if (source_bucket, source_key) == (destination_bucket, destination_key):
            return

        s3 = self.boto_session.client("s3")
        s3.copy(
            {
                "Bucket": source_bucket,
                "Key": source_key,
            },
            destination_bucket,
            destination_key,
        )

    def default_bucket(self):
        if self._default_bucket:
            return self._default_bucket
        aws_account_id = self.boto_session.client("sts").get_caller_identity()["Account"]
        region = self.boto_session.region_name
        default_bucket = f"amazon-braket-{region}-{aws_account_id}"

        self._create_s3_bucket_if_it_does_not_exist(bucket_name=default_bucket, region=region)

        self._default_bucket = default_bucket
        return self._default_bucket

    def _create_s3_bucket_if_it_does_not_exist(self, bucket_name, region):
        """Creates an S3 Bucket if it does not exist.
        Also swallows a few common exceptions that indicate that the bucket already exists or
        that it is being created.

        Args:
            bucket_name (str): Name of the S3 bucket to be created.
            region (str): The region in which to create the bucket.

        Raises:
            botocore.exceptions.ClientError: If S3 throws an unexpected exception during bucket
                creation.
                If the exception is due to the bucket already existing or
                already being created, no exception is raised.
        """
        s3_client = self.boto_session.client("s3", region_name=region)
        try:
            if region == "us-east-1":
                # 'us-east-1' cannot be specified because it is the default region:
                # https://github.com/boto/boto3/issues/125
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region}
                )
            s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                },
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            message = e.response["Error"]["Message"]

            if error_code == "BucketAlreadyOwnedByYou":
                pass
            elif (
                error_code == "OperationAborted"
                and "conflicting conditional operation" in message
            ):
                # If this bucket is already being concurrently created, we don't need to create
                # it again.
                pass
            else:
                raise

    def create_logs_client(self) -> "boto3.session.Session.client":
        """
        Create a CloudWatch Logs boto client.

        Returns:
            'boto3.session.Session.client': The CloudWatch Logs boto client.
        """
        return self.boto_session.client("logs", config=self._config)

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

    @staticmethod
    def parse_s3_uri(s3_uri: str) -> (str, str):
        """
        Parse S3 uri to get bucket and key

        Args:
            's3_uri': S3 uri.

        Returns:
            (str, str): Bucket and Key tuple.
        """
        try:
            assert s3_uri.startswith("s3://")
            bucket, key = s3_uri.split("/", 3)[2:]
            return bucket, key
        except (AssertionError, ValueError):
            raise ValueError("Not a valid S3 uri")

    @staticmethod
    def construct_s3_uri(bucket, *dirs):
        return f"s3://{bucket}/{'/'.join(dirs)}"
