**DO NOT SHARE OR TALK ABOUT THE CONTENTS OF THIS LIBRARY per the Amazon Beta NDA you signed.**

Amazon Braket Python SDK is an open source library for interacting with quantum devices on Amazon Braket.

## Installation

### Prerequisites
- Python 3.7.2+

### Steps

1. Get a confirmation email from Amazon Braket confirming you have access to the service.

2. (Optional) Recommended to work inside a virtual environment. You can skip this step if you don't care about mucking with your global python dependencies. See [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) if you don't have it already installed.

```bash
mkdir braket
cd braket

virtualenv venv
source venv/bin/activate
```
  
2. Install [AWS CLI](https://github.com/aws/aws-cli#installation)

```bash
pip install awscli
```
 
3. [Configure AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) settings to have a profile that can access your AWS account. Once a profile has been created set the `AWS_PROFILE` such that all future steps can connect to your AWS account.

```bash
export AWS_PROFILE=YOUR_PROFILE_NAME
```
 
4. Install `braket-python-sdk` package.

```bash
git clone https://github.com/aws/braket-python-sdk.git --branch stable/latest
pip install -e braket-python-sdk
```

If you want to run tests and / or do any development on the framework run:
```bash
pip install -e "braket-python-sdk[test]"
```
   
5. Install latest Amazon Braket model in AWS CLI.

```bash
aws s3 cp s3://braket-external-assets-prod-us-west-2/models/braket-2019-09-01.normal.json braket-model.json
aws configure add-model --service-model "file://braket-model.json" --service-name braket
```

6. Create the necessary Amazon Braket resources in your AWS account.

Follow the link below to create the resources using CloudFormation. This will create the required IAM resources and a default S3 bucket, `braket-output-${AWS::AccountId}`, for storing Amazon Braket outputs.

[Quick-Create in AWS CloudFormation](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL=https://braket-external-assets-prod-us-west-2.s3-us-west-2.amazonaws.com/templates/braket-resources.yaml&stackName=BraketResources)


7. You can now call Amazon Braket from the `braket-python-sdk`.

```python
from braket.circuits import Circuit
from braket.aws import AwsQuantumSimulator
   
device = AwsQuantumSimulator("arn:aws:aqx:::quantum-simulator:aqx:qs1")
s3_folder = ("braket-output-AWS_ACCOUNT_ID", "folder-name")
   
bell = Circuit().h(0).cnot(0, 1)
print(device.run(bell, s3_folder).result().measurement_counts)
```
	
You should get output similar to...
```
Counter({'11': 50, '00': 50})
```

7. Install [Jupyter](https://jupyter.org/install) and create an braket kernel.
```
pip install jupyter ipykernel
python -m ipykernel install --user --name braket
```
	
8. You can now launch Jupyter and use the SDK within it.
```
jupyter notebook
```

## Update to latest changes

1. `cd` into the GitHub repository directory
2. run `git pull`

## Sample Notebooks
TODO 

## Documentation

First `cd` into the `doc` directory and run:
```bash
make html
```

Then open `BRAKET_SDK_ROOT/build/documentation/html/index.html` in a browser to view the docs.

## Testing

Make sure to install test dependencies first:
```
pip install -e "braket-python-sdk[test]"
```

### Unit Tests
```
tox -e unit-tests
```

To run an individual test
```bash
tox -e unit-tests -- -k 'your_test'
```

To run linters and doc generators and unit tests
```bash
tox
```

### Integration Tests

Set the `AWS_PROFILE`
```bash
export AWS_PROFILE=PROFILE_FROM_STEP_3
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
