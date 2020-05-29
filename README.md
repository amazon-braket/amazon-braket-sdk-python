**This prerelease documentation is confidential and is provided under the terms of your nondisclosure agreement with Amazon Web Services (AWS) or other agreement governing your receipt of AWS confidential information.**

The Amazon Braket Python SDK is an open source library that provides a framework that you can use to interact with quantum computing hardware devices through Amazon Braket. This document describes how to configure your environment to use the Amazon Braket (Private Beta) locally on your computer. It does not include information about how to use Amazon Braket (Private Beta) in the AWS console.

**Getting the latest version**

Get the latest version of the SDK. If you receive a notice that a new version of the SDK is available, you can update to the latest version. For more information, see [Updating to the latest release](https://github.com/aws/braket-python-sdk/tree/stable/latest#updating-to-the-latest-release). View the [Releases](https://github.com/aws/braket-python-sdk/releases) page for more information.

**Use the stable/latest branch**

You should always use the stable/latest branch of this repo, which includes the latest stable version of the SDK. The master branch includes in-progress features and will not work.

**Providing Feedback and Getting Help**

To provide feedback or request support, please contact the Amazon Braket team at [amazon-braket-preview-support@amazon.com](mailto:amazon-braket-preview-support@amazon.com?subject=Add%20a%20brief%20description%20of%20the%20issue).

**Important**

If you **Star**, **Watch**, or submit a pull request for this repository, other users that have access to this repository are able to see your user name in the list of watchers. If you want to remain anonymous, you should not Watch or Star this repository, nor post any comments or submit a pull request.

## Prerequisites
Before you begin working with the Amazon Braket SDK, make sure that you've installed or configured the following prerequisites.

### Python 3.7.2 or greater
Download and install Python 3.7.2 or greater from [Python.org](https://www.python.org/downloads/).
If you are using Windows, choose **Add Python to environment variables** before you begin the installation.

### Using a Virtual Environment
If you want to use a virtual environment for interacting with the Amazon Braket SDK, first install virtualenv with the following command:
```bash
pip install virtualenv
```

To learn more, see [virtualenv](https://virtualenv.pypa.io/en/stable/installation/).

On Windows, you should open a new terminal window to install `virtualenv`. If you use a terminal window that was open before you installed Python, the terminal window does not use the Python environment variables needed.

After you install `virtualenv`, use the following command to create a virtual environment. When you run this command, it creates a folder named `braketvirtenv`, and uses that folder as the root folder of the virtual environment. You should run the command from a location where you want to create the virtual environment.

**To create a virtual environment**
```bash
virtualenv braketvirtenv
```

Then use one of the following options to activate the virtual environment.

**To activate the virtual environment on Mac and Linux**:
```bash
source braketvirtenv/bin/activate
```

**To activate the virtual environment on Windows**
```bash
cd braketvirtenv\scripts
```

```bash
activate
```

Then run this command to return the cursor to the parent folder
```bash
cd ..
```

### Git
Install Git from https://git-scm.com/downloads. Installation instructions are provided on the download page.

### Access to Amazon Braket (Private Beta)
You can configure your environment for the Amazon Braket Python SDK, but you need to be granted permission to access Amazon Braket (Private Beta) before you can start making code requests to Amazon Braket. If you’ve not received notification that you have been added to the beta, please contact the Amazon Braket team for assistance using this email address: [amazon-braket-preview-support@amazon.com](mailto:amazon-braket-preview-support@amazon.com?subject=Add%20a%20brief%20description%20of%20the%20issue).

### IAM user or role with required permissions
To perform the steps in this document and to interact with Amazon Braket, use an account with administrator privileges, such as one with the AdministratorAccess policy applied. To learn more about IAM user, roles, and policies, see [Adding and Removing IAM Identity Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_manage-attach-detach.html).

### AWS CLI

#### Install and configure the AWS Command Line Interface (CLI)
Install the [AWS CLI](https://github.com/aws/aws-cli#installation) so that you can interact with AWS via the command line. This is required to perform some steps in this document. Instructions to install and configure the CLI are included on the installation page.

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
Use the following link to an AWS CloudFormation template to automatically create the resources that Amazon Braket uses or interacts with in your account.

**Important**

If you are using IAM roles for multiple users in your organization to access the Amazon Braket Private Beta from the same account, only open the template and create the stack once for the account. Each role in the account then has access to the resources Amazon Braket needs in the account.

The template creates the following resources:
- An S3 bucket to store job output. The bucket is named `braket-output-AWSaccountId` where AWSAccountId is your account ID. For example, if your AWS account ID is 123456789012, the bucket is named `braket-output-123456789012`.
- IAM roles named AmazonBraketJobExecutionRole, which is used to run jobs, and AQxFullAccess which is used to interact with the AWS resources that Amazon Braket needs.
- An IAM policy, AmazonBraketFullAccess, that includes permission to use Amazon Braket actions, as well as the permissions necessary to access the S3 bucket created. If you want to use a role that does not have admin permissions, you can apply the AmazonBraketFullAccess policy to the user or role you are using to grant the permissions required to use Amazon Braket beta.

If you are already logged in to AWS when you click the link to open the template, the resources are created in the current account. If you want to use Amazon Braket beta in a different account, first log in using that account.

[Amazon Braket CloudFormation Stack Creation template](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL=https://braket-external-assets-prod-us-west-2.s3-us-west-2.amazonaws.com/templates/braket-resources.yaml&stackName=BraketResources)

When the template loads, select the **I acknowledge that AWS CloudFormation might create IAM resources with custom names** checkbox, and then choose **Create Stack**.

Wait until the Status changes to **CREATE_COMPLETE**. You may need to refresh the page to see the current status of the stack creation.

## Setting up the Amazon Braket Python SDKs
Use the steps in this section to install and configure the Amazon Braket Python SDKs for your environment. You should perform the steps in the order in which they are included in this document.

### Download the Amazon Braket GitHub Repositories
The easiest way to get the SDKs is to download them directly from the GitHub site. Because the repositories are private during the Private Beta period, an SSH key is required to access the files remotely from a terminal session. If you download them directly from the GitHub site, you can just extract the files to your system or virtual environment without the extra steps of using an SSH key. You need to log in to GitHub using the account that was whitelisted for the Amazon Braket (Private Beta).

Use the following links to download the Amazon Braket Python SDK repos:
- [braket-python-ir](https://github.com/aws/braket-python-ir/archive/stable/latest.zip)
- [amazon-braket-default-simulator-python](https://github.com/aws/amazon-braket-default-simulator-python/archive/stable/latest.zip)
- [braket-python-sdk](https://github.com/aws/braket-python-sdk/archive/stable/latest.zip)

### Extract the SDK .zip files
Because the files were downloaded directly from GitHub, the folder in the .zip file includes the name of the branch of the GitHub repo that was downloaded, in this case the `stable/latest` branch. But to use the files in the SDK, we need to rename the folder to the original name.

Note: Make sure you are always using the branch 'stable/latest' and not 'master'. The 'master' branch may contain in-progress changes that result in errors.

**To rename the folders in the SDK .zip files**
First, extract the .zip files to a location of your choosing. Then open the location where you extracted the folders to. You can use either the GUI file system tools in your OS, or the command line. You should see 3 folders with the following names:
- braket-python-ir-stable-latest
- amazon-braket-default-simulator-python-stable-latest
- braket-python-sdk-stable-latest

Rename the folders to the following:
- braket-python-ir
- amazon-braket-default-simulator-python
- braket-python-sdk

Then copy the renamed files and paste them into the `braketvirtenv` folder where you created a virtual environment. Your folder structure should look like this:
```bash
..\YourFolder\braketvirtenv\braket-python-ir\
```

### Install the SDK packages
Use the following commands to install the SDKs in the order that they appear:

```bash
pip install -e braket-python-ir
```

```bash
pip install -e amazon-braket-default-simulator-python
```

```bash
pip install -e braket-python-sdk
```

### Install latest Amazon Braket model in AWS CLI
Run the following commands to install the Braket model. The file is downloaded to the current location. Position the cursor in the folder where you want to download the file before running the command.

```bash
aws s3 cp s3://braket-external-assets-prod-us-west-2/models/braket-2019-09-01.normal.json braket-model.json
```
```bash
aws configure add-model --service-model "file://braket-model.json" --service-name braket
```
## Validate the Configuration
Your environment should now be configured to successfully use the Braket Python SDK to interact with Amazon Braket. You can use the following example to confirm that your settings are correct.

You can confirm that your environment is correctly configured in either of the following ways:
- Create a Python file
- Use a Jupyter notebook

## Code sample for validating your configuration
Use the following code sample to validate your environment configuration.

```python
import boto3
from braket.aws import AwsQuantumSimulator, AwsQuantumSimulatorArns
from braket.circuits import Circuit

aws_account_id = boto3.client("sts").get_caller_identity()["Account"]

device = AwsQuantumSimulator(AwsQuantumSimulatorArns.QS1)
s3_folder = (f"braket-output-{aws_account_id}", "folder-name")

bell = Circuit().h(0).cnot(0, 1)
task = device.run(bell, s3_folder, shots=100)
print(task.result().measurement_counts)
```

The code sample imports the Amazon Braket framework, then defines the execution environment as the AWSQuantumSimulator and the device to use. The `s3_folder` statement defines the Amazon S3 bucket for job output and the folder in the bucket to store job output. This folder is created when you run the job. It then creates a Bell Pair circuit, executes the circuit on the simulator and prints the results of the job.

### Available Simulators
There is currently one AwsQuantumSimulator available:
- `arn:aws:aqx:::quantum-simulator:aqx:qs1` – a Schrödinger simulator. Simulates exactly running a job on a quantum computer. Limit of 25 qubits. This simulator samples only from the state vector and outputs an array of bit strings that appears as though it came from a quantum computer. Does not provide a state vector.

#### To validate your configuration using a Python file
1. Open a text editor with example file `../braket-python-sdk/examples/bell.py`.
1. If desired, modify `folder-name` to the name of the folder to create/use for results in following line:
   `s3_folder = (f"braket-output-{aws_account_id}", "folder-name")`. Save the file.
1. Make sure the virtualenv (`braketvirtenv`) is activated, and then position the cursor in the `/examples` folder of the repo. Assuming you created a virtual environment on your `C:` drive in a folder named `braket`, the cursor should be at the following location:
`c:\braket\braketvirtenv\braket-python-sdk\examples\`.
1. Then use the following command to run the sample:

   ```bash
   python bell.py
   ```

You should see a result similar to the following:
```Counter({'11': 52, '00': 48})```

#### To validate your configuration using a Jupyter notebook
See [Installing the Jupyter Software](https://jupyter.org/install) for information about how to install Jupyter. You can use either JupyterLab or classic Jupyter Notebook.

Run the following commands to install Jupyter and then create a Braket kernel.
```bash
pip install jupyter ipykernel
```

```bash
python -m ipykernel install --user --name braket
```

After you have installed Jupyter, use this command to open a Jupyter notebook so you can use the SDK within the notebook:
```bash
jupyter notebook
```
Jupyter opens in a browser window. Choose **New**, and then under **Notebooks**, choose **braket**.

**Note** If you are using a Jupyter notebook from an prior installation and did not create a Braket kernel, you will not see braket available for the notebook type. Choose Python3 instead. If you choose Python3, you must have the Braket packages installed globally.

Copy the code sample (above) into the notebook. If you want to use a different folder in the bucket, change `folder-name` to the name of the folder to create. If the folder already exists it uses the existing folder.

Choose **Run** to execute the code to confirm that your environment is configured correctly.

When the job completes, you should see output similar to the following:
`Counter({'00': 519, '11': 481})`

**Important** Tasks may not run immediately on the QPU. IonQ runs tasks once every 24 hours. Rigetti tasks run when the QPU is available, with times varying day to day.

#### To validate your quantum algorithm locally

Braket Python SDK comes bundled with an implementation of a quantum simulator that you can run locally. You can use the local simulator to test quantum tasks constructed using the SDK before you submit them to the Amazon Braket service for execution. An example of how to execute the task locally is included in the repo `../examples/local_bell.py`.

#### Debugging logs

Tasks sent to QPUs don't always run right away. For IonQ, jobs are run once every 24 hours. For Rigetti, tasks are queued and run when the QPU is available, with the time varying day to day. To view task status, you can enable debugging logs. An example of how to enable these logs is included in repo: `../examples/debug_bell.py`. This example enables task logging so that status updates are continuously printed to console after a quantum task is executed. The logs can also be configured to save to a file or output to another stream. You can use the debugging example to get information on the tasks you submit, such as the current status, so that you know when your task completes. 

## Running a Quantum Algorithm on a Quantum Computer
With Amazon Braket, you can run your quantum circuit on a physical quantum computer.

The following example executes the same Bell Pair example described to validate your configuration on a Rigetti quantum computer. When you execute your task, Amazon Braket polls for a result. If it a result is not returned within the default polling time, such as when a QPU is unavailable, a local timeout error is returned. You can always restart the polling by using `task.result()`.

However, to avoid receiving timeout errors, you can include `poll_timeout_seconds` parameter and specify a longer polling time. In this example, `poll_timeout_seconds=86400` sets the polling time to one day (24 hours).
```python
import boto3
from braket.circuits import Circuit
from braket.aws import AwsQpu, AwsQpuArns

aws_account_id = boto3.client("sts").get_caller_identity()["Account"]

device = AwsQpu(AwsQpuArns.RIGETTI)
s3_folder = (f"braket-output-{aws_account_id}", "RIGETTI")

bell = Circuit().h(0).cnot(0, 1)
task = device.run(bell, s3_folder) 
print(task.result().measurement_counts)
```

Specify which quantum computer hardware to use by changing the value of the `device_arn` to the value for quantum computer to use:
- **IonQ** "arn:aws:aqx:::qpu:ionq" (Available 4:00 PM to 8:00 PM ET M-F)
- **Rigetti** "arn:aws:aqx:::qpu:rigetti" (Available 11:00 AM to 1:00 PM ET daily)
- **D-Wave** "arn:aws:aqx:::qpu:d-wave" (Available 24/7. See the next section in this document for more information about using D-Wave.)

### Using Amazon Braket with D-Wave QPU
If you want to use [Ocean](https://docs.ocean.dwavesys.com/en/latest/) with the D-Wave QPU, you can install the [braket-ocean-python-plugin](https://github.com/aws/braket-ocean-python-plugin). Information about how to install the plugin is provided in the [README](https://github.com/aws/braket-ocean-python-plugin/blob/master/README.md) for the repo.

### Using Amazon Braket with PennyLane
To use Amazon Braket with Xanadu [PennyLane](https://pennylane.ai/), install the [Amazon Braket plugin for PennyLane](https://github.com/aws/amazon-braket-pennylane-plugin-python). 
Instructions for setting up and using the plugin are provided in the README in the repository.

### Deactivate the virtual environment
After you are finished using the virtual environment to interact with Amazon Braket, you can deactivate it using the following command.

**To deactivate the virtual environment on Mac or Linux**
```bash
source braketvirtenv/bin/deactivate
```

**To deactivate the virtual environment on Windows**
```bash
cd braketvirtenv\scripts
```

```bash
deactivate
```

When you want to use it again, you can reactivate it with the same command you used previously.

## Updating to the latest release
We will periodically make updates and changes the SDK or the model. When you are notified of a change that requires action on your part, use the following steps to update your environment to the latest version.

### Check the version you have installed
You can view the version of the braket packages that you have installed by using the following commands in the virtual environment:
```bash
pip show amazon-braket-default-simulator-python
pip show braket-ir
pip show braket-sdk
```
Compare the version displayed in your local environment with the latest version listed for each of the following release pages:
- [amazon-braket-default-simulator-python](https://github.com/aws/amazon-braket-default-simulator-python/releases) 
- [braket-python-ir](https://github.com/aws/braket-python-ir/releases)
- [braket-python-sdk](https://github.com/aws/braket-python-sdk/releases) 

If the version listed is higher than your local version, you should update to the latest release.

### To get the lastest updates
Perform the steps described in the [Setting up the Amazon Braket Python SDKs](https://github.com/aws/braket-python-sdk/tree/stable/latest#setting-up-the-amazon-braket-python-sdks) section of this document. The links in that section point to the most recent version of the braket-python-sdk, braket-python-ir, amazon-braket-default-simulator-python, and model file you need to set up the new version of the SDK.

You can extract the file to the same location you are using and replace the existing files with the updated SDK. This lets you continue to use the same virtual environment.

## Sample Notebooks
Coming soon

## Braket Python SDK API Reference Documentation
To view the API Reference for the SDK, either download the .zip file or building it in your local environment.

**To download the API Reference .zip file**

Use the following command to download the .zip file
```bash
aws s3 cp s3://braket-external-assets-prod-us-west-2/sdk-docs/built-sdk-documentation.zip braket-sdk-documentation.zip
```
Then extract the `braket-sdk-documentation.zip` file to your local environment. After you extract the file, open the index.html file in the `SDK Documentation` folder.

**To generate the API Reference HTML in your local environment**

To generate the HTML, first change directories (`cd`) to position the cursor in the `braket-python-sdk` directory. Then, run the following command to generate the HTML documentation files:

```bash
tox -e docs
```

To view the generated documentation, open the following file in a browser:
`../braket-python-sdk/build/documentation/html/index.html`

## Install the SDK for Testing
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
Set the `AWS_PROFILE` information in the Prerequisites section of this document.
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
