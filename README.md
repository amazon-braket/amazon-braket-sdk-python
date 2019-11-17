**DO NOT SHARE OR TALK ABOUT THE CONTENTS OF THIS LIBRARY per the Amazon Beta NDA you signed.**

Amazon Qx Python SDK is an open source library for interacting with quantum devices on Amazon Qx.

TODO describe the different feature sets / abstractions.

## Installation

### Prerequisites
- Python 3.7.2+
- TODO: Describe how to get access to the service

### Steps

1. (Optional) Recommended to work inside a virtual environment. You can skip this step if you don't care about mucking with your global python dependencies. See [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) if you don't have it already installed.
 ```bash
 mkdir aqx
 cd aqx

 virtualenv venv
 source venv/bin/activate
 ```
  
2. Install [AWS CLI](https://github.com/aws/aws-cli#installation)
 ```bash
 pip install awscli
 ```
 
3. Install `aqx-python-sdk` package.
 ```bash
 git clone https://github.com/aws/aqx-python-sdk.git
 pip install -e aqx-python-sdk
 ```

 To install test dependencies for running tests locally run:
 ```bash
 pip install -e "aqx-python-sdk[test]"
 ```
   
4. TODO: Add AQx Service model to the AWS CLI

5. [Configure AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) settings to have a profile that the `aqx-python-sdk` can assume.

6. You can now call AWS from the `aqx-python-sdk`. Confirm by running the following in a python interpreter.
 ```python
 import boto3
 import json
 from aqx.qdk.circuits import Circuit
 from aqx.qdk.aws import AwsQuantumSimulator, AwsSession
	
 aws_session = AwsSession(
     boto_session=boto3.session.Session(
         profile_name="INSERT_AWS_PROFILE_NAME"
     )
 )
 device = AwsQuantumSimulator("quest_arn", aws_session)
 s3_folder = ("INSERT_BUCKET", "INSERT_KEY")
	
 bell = Circuit().h(0).cnot(0, 1)
 print(device.run(bell, s3_folder).result().measurement_counts())
 ```
	
You should get output similar to...
```
Counter({'11': 50, '00': 50})
```

7. Install [Jupyter](https://jupyter.org/install) and create an aqx kernel.
 ```
 pip install jupyter ipykernel
 python -m ipykernel install --user --name aqx
 ```
	
8. You can now launch Jupyter and use the QDK within it.
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
pip install -e "aqx-python-sdk[test]"
```

To run the unit tests only:
```
tox
```

To run the integ tests only, first set the AWS_PROFILE you'd like to use for testing:
```bash
export AWS_PROFILE=INSERT_PROFILE_NAME
```

Run the following tox command
```bash
tox test/integ_tests
```

To run an individual test:
```bash
tox -- -k 'your_test'
```

## Building Sphinx docs
`cd` into the `doc` directory and run:
```bash
make html
```

You can edit the templates for any of the pages in the docs by editing the .rst files in the ``doc`` directory and then running ``make html`` again.

## License

This project is licensed under the Apache-2.0 License.
