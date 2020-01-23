**This prerelease documentation is confidential and is provided under the terms of your nondisclosure agreement with Amazon Web Services (AWS) or other agreement governing your receipt of AWS confidential information.**

The Amazon Braket Python SDK is an open source library that provides a framework that you can use to interact with quantum computing hardware devices through Amazon Braket.

## Prerequisites
Before you begin working with the Amazon Braket SDK, make sure that you've installed or configured the following prerequisites.

### Python 3.7.2+
Install Python version 3.7.2 or later. [Python Downloads](https://www.python.org/downloads/). 

### Access to Amazon Braket (Private Beta)
You can configure your environment for the Amazon Braket Python SDK, but you need to be granted permission to access Amazon Braket (Private Beta). 

### AWS CLI

#### Install and configure the AWS Command Line Interface (CLI)
Install the [AWS CLI](https://github.com/aws/aws-cli#installation) so that you can interact with AWS via the command line. This is required to perform some steps in this document.

#### Use the following command to install the AWS CLI
```bash
pip install awscli
```

#### Configure a profile for the AWS CLI
Configure a CLI profile to use your account to interact with AWS. To learn more, see [Configure AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html). 

After you create a profile, use the following command to set the `AWS_PROFILE` so that all future commands can access your AWS account and resources.

```bash
export AWS_PROFILE=YOUR_PROFILE_NAME
```

### Configure your AWS account with the resources necessary for Amazon Braket
Use the following link to an AWS CloudFormation template to automatically create the resources that Amazon Braket uses or interacts with in your account. The template creates the following resources:
- An S3 bucket to store job output. The bucket is named `braket-output-AWSaccountId` where AWSAccountId is your account ID. For example, if your AWS account ID is 123456789012, the bucket is named `braket-output-123456789012`.
- IAM roles named 
- An IAM policy, AmazonBraketFullAccess, that includes permission to use Amazon Braket actions and the permissions necessary to access the S3 bucket created. 
Follow the link below to create the resources using CloudFormation. This will create the required IAM resources and a default S3 bucket, `braket-output-${AWS::AccountId}`, for storing Amazon Braket outputs.

[Amazon Braket CloudFormation STack Creation template](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL=https://braket-external-assets-prod-us-west-2.s3-us-west-2.amazonaws.com/templates/braket-resources.yaml&stackName=BraketResources)


## Setting up the Braket Python SDK
Use the steps in this section to install and configure the Braket Python SDK for your environment. You should perform the steps in the order in which they are included in this document.
 
### Install the braket-python-sdk package
Use the following commands to install the Braket Python SDK package

```bash
git clone https://github.com/aws/braket-python-sdk.git --branch stable/latest
```
```bash
pip install -e braket-python-sdk
```

### Install latest Amazon Braket model in AWS CLI
Run the following commands to install the 
```bash
aws s3 cp s3://braket-external-assets-prod-us-west-2/models/braket-2019-09-01.normal.json braket-model.json
```
```bash
aws configure add-model --service-model "file://braket-model.json" --service-name braket
```
## Validate the Installation
Your environment should now be configured to successfully use the Braket Python SDK to interact with Amazon Braket. You can use the following example to confirm that your settings are correct.
**Important**
You must replace the value for the s3_folder to the value for the bucket created when you ran the CloudFormation template. Replace the AWS_ACCOUINT_ID with your 12-digit AWS account number. You can find your account number by logging into the AWS console.
	
```python
from braket.circuits import Circuit
from braket.aws import AwsQuantumSimulator
   
device = AwsQuantumSimulator("arn:aws:aqx:::quantum-simulator:aqx:qs1")
s3_folder = ("braket-output-AWS_ACCOUNT_ID", "folder-name")

bell = Circuit().h(0).cnot(0, 1)
print(device.run(bell, s3_folder).result().measurement_counts)
```
	
When you execute this code, you should get a response similar to the following:

```
Counter({'11': 50, '00': 50})
```

### Install Jupyter and Create a Braket Kernel
Use the following command to install [Jupyter](https://jupyter.org/install).

```bash
pip install jupyter ipykernel
```

Then use this command to create a Braket kernel

```bash
python -m ipykernel install --user --name braket
```

Then use this command to open a Jupyter notebook so you can use the SDK within the notebook

```bash
jupyter notebook
```

## Updating to the latest release
We will periodically make updates and changes the the SDK or the model. When you are notified of a change that requires action on your part, use the following steps to update your environment to the lastest version.

### To get the lastest updated
Position your cursor in the folder where you cloned the GitHub repo for the Braket Python SDK, then run the following command to get the latest version.
```bash
git pull
```

## Sample Notebooks
Coming soon 

## Documentation
You can generate the documentation for the SDK. Run the following command

First change directories (`cd`) to position the cursor in the (`doc`) directory.
Then run the following command to generate the HTML documentation files:

```bash
make html
```

To view the generated documentation, open the following file in a browser:
`BRAKET_SDK_ROOT/build/documentation/html/index.html`

## Testing
Make sure to install test dependencies first:

```bash
pip install -e "braket-python-sdk[test]"
```

### Unit Tests
```bash
tox -e unit-tests
```

To run an individual test
```
tox -e unit-tests -- -k 'your_test'
```

To run linters and doc generators and unit tests
```bash
tox
```

### Integration Tests

Set the `AWS_PROFILE`
```bash
export AWS_PROFILE=Your_Profile_Name
```

Create an S3 bucket in the same account as the `AWS_PROFILE` with the following naming convention `braket-sdk-integ-tests-{account_id}`.

Run the tests
```bash
tox -e integ-tests
```

To run an individual test
```bash
tox -e integ-tests -- -k 'your_test'
```

## License

This project is licensed under the Apache-2.0 License.
