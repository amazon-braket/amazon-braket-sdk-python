# Amazon Braket Python SDK

[![Latest Version](https://img.shields.io/pypi/v/amazon-braket-sdk.svg)](https://pypi.python.org/pypi/amazon-braket-sdk)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/amazon-braket-sdk.svg)](https://pypi.python.org/pypi/amazon-braket-sdk)
[![Code Style: Black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/amazon-braket-sdk-python/badge/?version=latest)](https://amazon-braket-sdk-python.readthedocs.io/en/latest/?badge=latest)

The Amazon Braket Python SDK is an open source library that provides a framework that you can use to interact with quantum computing hardware devices through Amazon Braket.

## Prerequisites
Before you begin working with the Amazon Braket SDK, make sure that you've installed or configured the following prerequisites.

### Python 3.7.2 or greater
Download and install Python 3.7.2 or greater from [Python.org](https://www.python.org/downloads/).

### Git
Install Git from https://git-scm.com/downloads. Installation instructions are provided on the download page.

### IAM user or role with required permissions
As a managed service, Amazon Braket performs operations on your behalf on the AWS hardware that is managed by Amazon Braket. Amazon Braket can perform only operations that the user permits. You can read more about which permissions are necessary in the AWS Documentation.

The Braket Python SDK should not require any additional permissions aside from what is required for using Braket. However, if you are using an IAM role with a path in it, you should grant permission for iam:GetRole.

To learn more about IAM user, roles, and policies, see [Adding and Removing IAM Identity Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_manage-attach-detach.html).

### Boto3 and setting up AWS credentials

Follow the installation [instructions](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html) for Boto3 and setting up AWS credentials.

### Configure your AWS account with the resources necessary for Amazon Braket
If you are new to Amazon Braket, onboard to the service and create the resources necessary to use Amazon Braket using the [AWS console](https://console.aws.amazon.com/braket/home ).

## Installing the Amazon Braket Python SDK

The Amazon Braket Python SDK can be installed with pip as follows:

```bash
pip install amazon-braket-sdk
```

You can also install from source by cloning this repository and running a pip install command in the root directory of the repository:

```bash
git clone https://github.com/aws/amazon-braket-sdk-python.git
cd amazon-braket-sdk-python
pip install .
```

### Check the version you have installed
You can view the version of the amazon-braket-sdk you have installed by using the following command:
```bash
pip show amazon-braket-sdk
```

You can also check your version of `amazon-braket-sdk` from within Python:

```
>>> import braket._sdk as braket_sdk
>>> braket_sdk.__version__
```

## Usage

### Running a circuit on an AWS simulator

```python
import boto3
from braket.aws import AwsDevice
from braket.circuits import Circuit

aws_account_id = boto3.client("sts").get_caller_identity()["Account"]

device = AwsDevice("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
s3_folder = (f"amazon-braket-output-{aws_account_id}", "folder-name")

bell = Circuit().h(0).cnot(0, 1)
task = device.run(bell, s3_folder, shots=100)
print(task.result().measurement_counts)
```

The code sample imports the Amazon Braket framework, then defines the device to use (the SV1 AWS simulator). The `s3_folder` statement defines the Amazon S3 bucket for the task result and the folder in the bucket to store the task result. This folder is created when you run the task. It then creates a Bell Pair circuit, executes the circuit on the simulator and prints the results of the job. This example can be found in `../examples/bell.py`.

### Available Simulators
Amazon Braket provides access to two simulators: a fully managed statevector simulator, SV1, and a local simulator that is part of the Amazon Braket SDK.

- `arn:aws:braket:::device/quantum-simulator/amazon/sv1` - SV1 is a fully managed, high-performance, state vector simulator. It can simulate circuits of up to 34 qubits and has a maximum runtime of 12h. You should expect a 34-qubit, dense, and square (circuit depth = 34) circuit to take approximately 1-2 hours to complete, depending on the type of gates used and other factors.

- `LocalSimulator()` - The Amazon Braket Python SDK comes bundled with an implementation of a quantum simulator that you can run locally. The local simulator is well suited for rapid prototyping on small circuits up to 25 qubits, depending on the hardware specifications of your Braket notebook instance or your local environment. An example of how to execute the task locally is included in the repo `../examples/local_bell.py`.

### Debugging logs

Tasks sent to QPUs don't always run right away. To view task status, you can enable debugging logs. An example of how to enable these logs is included in repo: `../examples/debug_bell.py`. This example enables task logging so that status updates are continuously printed to the terminal after a quantum task is executed. The logs can also be configured to save to a file or output to another stream. You can use the debugging example to get information on the tasks you submit, such as the current status, so that you know when your task completes.

### Running a Quantum Algorithm on a Quantum Computer
With Amazon Braket, you can run your quantum circuit on a physical quantum computer.

The following example executes the same Bell Pair example described to validate your configuration on a Rigetti quantum computer.

```python
import boto3
from braket.circuits import Circuit
from braket.aws import AwsDevice

aws_account_id = boto3.client("sts").get_caller_identity()["Account"]

device = AwsDevice("arn:aws:braket:::device/qpu/rigetti/Aspen-8")
s3_folder = (f"amazon-braket-output-{aws_account_id}", "RIGETTI")

bell = Circuit().h(0).cnot(0, 1)
task = device.run(bell, s3_folder) 
print(task.result().measurement_counts)
```

When you execute your task, Amazon Braket polls for a result. By default, Braket polls for 5 days; however, it is possible to change this by modifying the `poll_timeout_seconds` parameter in `AwsDevice.run`, as in the example below. Keep in mind that if your polling timeout is too short, results may not be returned within the polling time, such as when a QPU is unavailable, and a local timeout error is returned. You can always restart the polling by using `task.result()`.

```python
task = device.run(bell, s3_folder, poll_timeout_seconds=86400)  # 1 day 
print(task.result().measurement_counts)
```

Specify which quantum computer hardware to use by changing the value of the `device_arn` to the value for quantum computer to use:
- **IonQ** "arn:aws:braket:::device/qpu/ionq/ionQdevice"
- **Rigetti** "arn:aws:braket:::device/qpu/rigetti/Aspen-8"
- **D-Wave** "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6" (See the next section in this document for more information about using D-Wave.)

**Important** Tasks may not run immediately on the QPU. The QPUs only execute tasks during execution windows. To find their execution windows, please refer to the [AWS console](https://console.aws.amazon.com/braket/home) in the "Devices" tab.

### Using Amazon Braket with D-Wave QPU
If you want to use [Ocean](https://docs.ocean.dwavesys.com/en/latest/) with the D-Wave QPU, you can install the [amazon-braket-ocean-plugin-python](https://github.com/aws/amazon-braket-ocean-plugin-python). Information about how to install the plugin is provided in the [README](https://github.com/aws/amazon-braket-ocean-plugin-python/blob/master/README.md) for the repo.

## Sample Notebooks
Coming soon

## Braket Python SDK API Reference Documentation

The API reference, can be found on [Read the Docs](https://amazon-braket-sdk-python.readthedocs.io/en/latest/).

**To generate the API Reference HTML in your local environment**

To generate the HTML, first change directories (`cd`) to position the cursor in the `amazon-braket-sdk-python` directory. Then, run the following command to generate the HTML documentation files:

```bash
pip install tox
tox -e docs
```

To view the generated documentation, open the following file in a browser:
`../amazon-braket-sdk-python/build/documentation/html/index.html`

## Testing

This repository has both unit and integration tests.

To run the tests, make sure to install test dependencies first:
```bash
pip install -e "amazon-braket-sdk-python[test]"
```

### Unit Tests
```bash
tox -e unit-tests
```

You can also pass in various pytest arguments `tox -e integ-tests -- your-arguments` to run selected tests. For more information, please see [pytest usage](https://docs.pytest.org/en/stable/usage.html).


To run linters and doc generators and unit tests
```bash
tox
```

### Integration Tests

First, configure a profile to use your account to interact with AWS. To learn more, see [Configure AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html).

After you create a profile, use the following command to set the `AWS_PROFILE` so that all future commands can access your AWS account and resources.

```bash
export AWS_PROFILE=YOUR_PROFILE_NAME
```

Run the tests
```bash
tox -e integ-tests
```

You can also pass in various pytest arguments `tox -e integ-tests -- your-arguments` to run selected tests. For more information, please see [pytest usage](https://docs.pytest.org/en/stable/usage.html).

## License
This project is licensed under the Apache-2.0 License.