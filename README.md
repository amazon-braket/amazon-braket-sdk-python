**DO NOT SHARE OR TALK ABOUT THE CONTENTS OF THIS LIBRARY per the Amazon Beta NDA you signed.**

Amazon Braket Python SDK is an open source library for interacting with quantum devices on Amazon Braket.

TODO describe the different feature sets / abstractions.

## Installation

### Prerequisites
- Python 3.7.2+
- TODO: Describe how to get access to the service and what IAM roles need to be created.

### Steps

1. (Optional) Recommended to work inside a virtual environment. You can skip this step if you don't care about mucking with your global python dependencies. See [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) if you don't have it already installed.
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
 
3. [Configure AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) settings to have a profile that can assume the Amazon Braket IAM role in your AWS account. TODO: Add more specifics once the IAM role steps are defined in prerequisites.
 
4. Install `braket-python-sdk` package.
 ```bash
 git clone https://github.com/aws/braket-python-sdk.git
 pip install -e braket-python-sdk
 ```

 To install test dependencies for running tests locally run:
 ```bash
 pip install -e "braket-python-sdk[test]"
 ```
   
5. Install latest Amazon Braket model in AWS CLI.
 ```bash
 aws s3 cp s3://aqx-preview-assets-beta/models/aqx-2019-09-01.normal.json aqx-model.json --profile PROFILE_FROM_STEP_3
 aws configure add-model --service-model "file://aqx-model.json" --service-name aqx
 ```

6. You can now call AWS from the `braket-python-sdk`. Confirm by running the following in a python interpreter.
 ```python
 import boto3
 import json
 from braket.circuits import Circuit
 from braket.aws import AwsQuantumSimulator, AwsSession
	
 aws_session = AwsSession(
     boto_session=boto3.session.Session(
         profile_name="PROFILE_FROM_STEP_3"
     )
 )
 device = AwsQuantumSimulator("arn:aws:aqx:::quantum-simulator:aqx:qs1", aws_session)
 s3_folder = ("INSERT_BUCKET", "INSERT_KEY")
	
 bell = Circuit().h(0).cnot(0, 1)
 print(device.run(bell, s3_folder).result().measurement_counts())
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

## Sample Notebooks
TODO 

## Documentation
TODO

## Testing

Make sure to install test dependencies first:
```
pip install -e "braket-python-sdk[test]"
```

To run the unit tests only:
```
tox -e unit-tests
```

To run the integ tests only, first set the AWS_PROFILE you'd like to use for testing:
```bash
export AWS_PROFILE=PROFILE_FROM_STEP_3
```

Run the following tox command
```bash
tox -e integ-tests
```

To run an individual test (unit or integration)
```bash
tox -e unit-tests -- -k 'your_test'
```

```bash
tox -e integ-tests -- -k 'your_test'
```

To run everything (linters, docs, and unit tests)
```bash
tox
```

## Building Sphinx docs
`cd` into the `doc` directory and run:
```bash
make html
```

You can edit the templates for any of the pages in the docs by editing the .rst files in the ``doc`` directory and then running ``make html`` again.

## License

This project is licensed under the Apache-2.0 License.
