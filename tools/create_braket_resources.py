import argparse
import json
import os

import boto3
import yaml
from botocore.exceptions import ClientError

REQUIRED_RESOURCES_CFN_FILENAME = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "braket_required_resources.cloudformation.yaml"
)
REQUIRED_RESOURCES_STACK_NAME = "AmazonBraketResources"

DEFAULT_BUCKET_CFN_FILENAME = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "braket_default_s3_bucket.cloudformation.yaml"
)
DEFAULT_BUCKET_STACK_NAME = "AmazonBraketDefaultS3Bucket"


def main():
    parser = argparse.ArgumentParser(
        description="Create the required AWS resources for Amazon Braket."
    )
    parser.add_argument(
        "--create-default-bucket",
        dest="create_default_bucket",
        action="store_true",
        help="Creates a default S3 bucket for you to use with Amazon Braket, "
        + "e.g. 'braket-output-${AWS::AccountId}'",
    )
    args = parser.parse_args()

    boto_session = boto3.session.Session()
    region = boto_session.region_name
    cfn_client = boto_session.client("cloudformation")

    # Create required resources
    _create_cfn_stack(
        cfn_client, REQUIRED_RESOURCES_STACK_NAME, REQUIRED_RESOURCES_CFN_FILENAME, region
    )

    # Create default S3 bucket if specified
    if args.create_default_bucket:
        _create_cfn_stack(
            cfn_client, DEFAULT_BUCKET_STACK_NAME, DEFAULT_BUCKET_CFN_FILENAME, region
        )


def _read_cfn_yaml_file(filename):
    """Read the contents of a cloud formation template YAML file and return as a JSON string."""
    with open(filename, "r") as file:
        yaml_content = file.read()
        return json.dumps(yaml.load(yaml_content, Loader=yaml.BaseLoader))


def _create_cfn_stack(cfn_client, stack_name, body_filename, region):
    """
    Creates a CloudFormation stack. If stack already exists then it is deleted and then re-created
    with the supplied template body.
    """

    template_body = _read_cfn_yaml_file(body_filename)

    print(
        f"\nFollow in console: https://{region}.console.aws.amazon.com/cloudformation/home?"
        + f"region={region}#/stacks/stackinfo?stackId={stack_name}"
    )

    try:
        cfn_client.describe_stacks(StackName=stack_name)
        print(f"Stack {stack_name} already exists, deleting it...")
        cfn_client.delete_stack(StackName=stack_name)

        delete_waiter = cfn_client.get_waiter("stack_delete_complete")
        delete_waiter.wait(StackName=stack_name)
        print(f"Stack {stack_name} deleted")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ValidationError":
            # CFN stack doesn't exist, move on.
            pass
        else:
            raise e

    cfn_client.create_stack(
        StackName=stack_name, TemplateBody=template_body, Capabilities=["CAPABILITY_NAMED_IAM"]
    )

    print(f"Creating stack {stack_name}...")
    create_waiter = cfn_client.get_waiter("stack_create_complete")
    create_waiter.wait(StackName=stack_name)
    print(f"Stack {stack_name} created")


if __name__ == "__main__":
    main()
