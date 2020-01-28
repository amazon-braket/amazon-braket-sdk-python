**This prerelease documentation is confidential and is provided under the terms of your nondisclosure agreement with Amazon Web Services (AWS) or other agreement governing your receipt of AWS confidential information.**

The Amazon Braket Python SDK is an open source library that provides a framework that you can use to interact with quantum computing hardware devices through Amazon Braket.

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
You can configure your environment for the Amazon Braket Python SDK, but you need to be granted permission to access Amazon Braket (Private Beta). Before you can execute code against Amazon Braket. If you’ve not received notification that you have been added to the beta, please contact the Braket team for assistance.

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
Use the following link to an AWS CloudFormation template to automatically create the resources that Amazon Braket uses or interacts with in your account. The template creates the following resources:
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
- [braket-python-sdk](https://github.com/aws/braket-python-sdk/archive/stable/latest.zip)

### Extract the SDK .zip files
Because the files were downloaded directly from GitHub, the folder in the .zip file includes the name of the branch of the GitHub repo that was downloaded, in this case the `stable/latest` branch. But to use the files in the SDK, we need to rename the folder to the original name.

**To rename the folders in the SDK .zip files**
First, extract the .zip files to a location of your choosing. Then open the location where you extracted the folders to. You can use either the GUI file system tools in your OS, or the command line. You should see 2 folders with the following names:
- braket-python-ir-stable-latest
- braket-python-sdk-stable-latest

Rename the folders to the following:
- braket-python-ir
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
from braket.circuits import Circuit
from braket.aws import AwsQuantumSimulator
   
device = AwsQuantumSimulator("arn:aws:aqx:::quantum-simulator:aqx:qs1")
s3_folder = ("braket-output-AWS_ACCOUNT_ID", "folder-name")

bell = Circuit().h(0).cnot(0, 1)
print(device.run(bell, s3_folder).result().measurement_counts)
```

The code sample imports the Amazon Braket framework, then defines the execution environment as the AWSQuantumSimulator and the device to use. The `s3_folder` statement defines the Amazon S3 bucket for job output. It then creates a Bell Pair circuit, executes the circuit on the simulator and prints the results of the job.

### Available Simulators
There are currently three simulators available for Amazon Braket. To specify which simulator to use, change the code sample to replace the value for the `AwsQuantumSimulator` to one of the following values:
- `arn:aws:aqx:::quantum-simulator:aqx:qs1` – a Schrödinger simulator. Simulates exactly running a job on a quantum computer. Limit of 25 qubits. This simulator samples only from the distribution - an array of bit strings that appears as though it came from a quantum computer. Outputs only shots and does not provide a state vector. 
- `arn:aws:aqx:::quantum-simulator:aqx:qs2` – a TensorNetwork simulator. Provides an approximation of running a job on a quantum computer.
-	`arn:aws:aqx:::quantum-simulator:aqx:qs3` – a Schrödinger simulator. Simulates exactly running a job on a quantum computer. This simulator samples from the distribution but includes the entire state vector. This generates more data, and therefore incurs additional costs for storage of data in Amazon S3.

#### To validate your configuration using a Python file
1. Open a text editor.
2. Copy the code sample (above), then paste it into the text editor.
3. Replace the `AWS_ACCOUNT_ID` in the value for `s3_folder` to your 12-digit AWS account ID. It should look similar to the following:
   `s3_folder = ("braket-output-123456789012", "folder-name")`
4. Save the file with the name `bellpair.py`.
5. Use the file system to copy or move the file to your virtual environment. For example, in Windows, use File Explorer to open the `braket` folder in your virtual environment, then paste the file into the braket folder. Confirm that the file was moved to the correct location by viewing the contacts of the folder, such as with the `dir` command in Windows.
6. Run the following command to run the Python file:
   ```bash
   python bellpair.py
   ```
You should see a result similar to the following:
```Counter({'11': 522, '00': 478})```

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

**Note** If you are using a Jupyter notebook from an prior installation and did not create a Braket kernel, you will not see braket available for the notebook type. Choose Python3 instead. If you choose Python3, you must have Python envrironment variables set globally.

Copy the code sample (above) into the notebook. Be sure to change the value for the `s3_folder` to replace `AWS_ACCOUNT_ID` with your 12-digit AWS Account ID. You can find your AWS account ID in the AWS console. The entry should look similar to the following:
`s3_folder = ("braket-output-123456789012", "folder-name")`

Choose **Run** to execute the code to confirm that your environment is configured correctly.

When the job completes, you should see output similar to the following:
`Counter({'00': 519, '11': 481})`

## Running a Quantum Algorithm on a Quantum Computer
With Amazon Braket, you can run your quantum circuit on a physical quantum computer. The steps to do so are the same as those described to validate your environment. Just replace the example code provided in this document with your own code. 

The following example executes the same Bell Pair example described to validate your configuration against an IonQ quantum computer.
```python
from braket.circuits import Circuit
from braket.aws import AwsQpu

device = AwsQpu("arn:aws:aqx:::qpu:ionq")
s3_folder = ("braket-output-AWS_ACCOUNT_ID", "folder-name")

bell = Circuit().h(0).cnot(0, 1)
print(device.run(bell, s3_folder).result().measurement_counts)
```

Specify which quantum computer hardware to use by changing the value of the `device_arn` to the value for quantum computer to use:
- **IonQ** "arn:aws:aqx:::qpu:ionq"
- **Rigetti** "arn:aws:aqx:::qpu:rigetti"
- **D-Wave** Not yet available

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

### To get the lastest updates
Information to be provided when the next update is available.

## Sample Notebooks
Coming soon 

## Documentation
You can generate the documentation for the SDK. First change directories (`cd`) to position the cursor in the (`doc`) directory.
Then run the following command to generate the HTML documentation files:

```bash
make html
```

To view the generated documentation, open the following file in a browser:
`BRAKET_SDK_ROOT/build/documentation/html/index.html`

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
