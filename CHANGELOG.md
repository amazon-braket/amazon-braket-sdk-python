# Changelog

## v1.69.0 (2024-02-06)

### Features

 * update OQpy to version 0.3.5

## v1.68.3 (2024-02-05)

### Bug Fixes and Other Changes

 * Allow identities in PauliString observable

## v1.68.2 (2024-01-31)

### Bug Fixes and Other Changes

 * update S3 uri regex for AWS sessions
 * update batch circuit to limit repeat calls

## v1.68.1 (2024-01-29)

### Bug Fixes and Other Changes

 * add force flag for import testing

## v1.68.0 (2024-01-25)

### Features

 * update S3 locations for jobs

## v1.67.0 (2024-01-23)

### Features

 * add queue position to the logs for tasks and jobs

## v1.66.0 (2024-01-11)

### Features

 * update job name to use metadata

## v1.65.1 (2023-12-25)

### Bug Fixes and Other Changes

 * validate out circuits that contain only non-zero-qubit gates

## v1.65.0 (2023-12-21)

### Features

 * add U and GPhase gates

## v1.64.2 (2023-12-19)

### Bug Fixes and Other Changes

 * treating OpenQASM builtin types as constants

## v1.64.1 (2023-12-12)

### Bug Fixes and Other Changes

 * make filter more convenient

## v1.64.0 (2023-12-07)

### Features

 * add str, repr and getitem to BasisState

### Bug Fixes and Other Changes

 * update: adding a test to check for circular imports

## v1.63.0 (2023-12-05)

### Features

 * Allow reservation ARN in task and job creation

### Bug Fixes and Other Changes

 * Add Forte 1 device

## v1.62.1 (2023-11-17)

### Bug Fixes and Other Changes

 * Fix broken link to example notebook
 * update: default no longer returning RETIRED devices from get_devices

### Documentation Changes

 * Add matrix expressions to docstrings

## v1.62.0 (2023-11-09)

### Features

 * Add get_compiled_circuit convenience method

## v1.61.0.post0 (2023-11-07)

### Documentation Changes

 * Improve docstring for make_bound_circuit

## v1.61.0 (2023-11-06)

### Features

 * simplify entry point wrapper

### Bug Fixes and Other Changes

 * fixing some type hints for optional params

## v1.60.2 (2023-11-01)

### Bug Fixes and Other Changes

 * drop task count for batch task tests to 3

## v1.60.1 (2023-11-01)

### Bug Fixes and Other Changes

 * set python container version explicitly
 * set decorator job working directory inside of function
 * s3 config support for decorator jobs

## v1.60.0 (2023-10-31)

### Features

 * support dependency list for decorator hybrid jobs

### Bug Fixes and Other Changes

 * Don't run pulse tests when QPU offline

### Documentation Changes

 * Fix some nits in the decorator doc string
 * update intended audience to include education and research

## v1.59.2 (2023-10-25)

### Bug Fixes and Other Changes

 * remove deprecated as_unitary method

## v1.59.1.post0 (2023-10-24)

### Documentation Changes

 * add the amazon braket tag in the stack exchange URL

## v1.59.1 (2023-10-18)

### Bug Fixes and Other Changes

 * doc fixes

## v1.59.0 (2023-10-17)

### Features

 * use region property

## v1.58.1 (2023-10-16)

### Bug Fixes and Other Changes

 * use separate aws session for python validation

## v1.58.0 (2023-10-16)

### Features

 * job decorator

### Bug Fixes and Other Changes

 * update integ test for non-py310

## v1.57.2 (2023-10-11)

### Bug Fixes and Other Changes

 * Use builtins for type hints

## v1.57.1 (2023-10-05)

### Bug Fixes and Other Changes

 * docs: fix helper docstring

## v1.57.0 (2023-10-04)

### Features

 * wrap non-dict results and update results on subsequent calls
 * job helper functions

### Bug Fixes and Other Changes

 * revert integ test changes

## v1.56.2 (2023-10-03)

### Bug Fixes and Other Changes

 * Refactor Qubit and QubitSet to a separate module

## v1.56.1 (2023-09-27)

### Bug Fixes and Other Changes

 * fixing search device when don't have access to a region.

## v1.56.0 (2023-09-26)

### Features

 * add queue visibility information

## v1.55.1.post0 (2023-09-18)

### Documentation Changes

 * Remove trailing backquotes
 * add code contributors to the readme
 * change the sphinx requirement to be greater than 7.0.0

## v1.55.1 (2023-09-14)

### Bug Fixes and Other Changes

 * Revert "update: restricting parameter names to not collide with ones we use for OpenQASM generation. (#675)"

### Documentation Changes

 * Replace aws org with amazon-braket

## v1.55.0 (2023-09-09)

### Features

 * add Aria2 enum

## v1.54.3.post0 (2023-09-04)

### Documentation Changes

 * standardize task and job naming to quantum task and hybrid job

## v1.54.3 (2023-08-30)

### Bug Fixes and Other Changes

 * Move inline `_flatten` to top of `qubit_set.py`
 * build(deps): bump actions/setup-python from 4.6.1 to 4.7.0

## v1.54.2 (2023-08-28)

### Bug Fixes and Other Changes

 * readthedocs integration
 * build(deps): bump pypa/gh-action-pypi-publish from 1.8.8 to 1.8.10

## v1.54.1 (2023-08-22)

### Bug Fixes and Other Changes

 * update: restricting parameter names to not collide with ones we use for OpenQASM generation.

## v1.54.0 (2023-08-16)

### Features

 * enable gate calibrations on supported devices

## v1.53.4 (2023-08-15)

### Bug Fixes and Other Changes

 * docs: add mermaid diagram to describe the CI flow

## v1.53.3 (2023-08-08)

### Bug Fixes and Other Changes

 * fix a bug in time series and add trapezoidal time series

## v1.53.2 (2023-08-07)

### Bug Fixes and Other Changes

 * don't wrap FreeParameterExpression input as string

## v1.53.1 (2023-08-03)

### Bug Fixes and Other Changes

 * Support OpenQASM `Program`s in `from_ir`

## v1.53.0.post0 (2023-08-02)

### Documentation Changes

 * fix flake8 issues in tests

## v1.53.0 (2023-07-31)

### Features

 * point image uri to latest tag

### Bug Fixes and Other Changes

 * Update quantum job tests for latest containers
 * build(deps): bump pypa/gh-action-pypi-publish from 1.8.7 to 1.8.8
 * move import back to top level in job example
 * update doc string for handle_parameter_value
 * change all tests in the circuit test path to use with pytest.raises
 * pull latest container image by default

## v1.52.0 (2023-07-25)

### Features

 * Support symbolic expressions in `from_ir`

### Bug Fixes and Other Changes

 * local import in job example
 * Add parameter support

## v1.51.0 (2023-07-21)

### Features

 * add gate calibration data for supported quantum devices

### Bug Fixes and Other Changes

 * revert adding gate calibration data
 * making additional meta available in AHS results
 * handle the optional calibration URL returning None
 * copy calibrations in to_ir

## v1.50.0 (2023-07-19)

### Features

 * Add dot(), power(), and to_circuit() to PauliString

## v1.49.1.post0 (2023-07-17)

### Documentation Changes

 * update aws_quantum_job.py to add pattern for create job_name pa…

## v1.49.1 (2023-07-12)

### Bug Fixes and Other Changes

 * coerce ArbitraryWaveform.amplitudes type

## v1.49.0 (2023-07-10)

### Features

 * OpenQASM to `Circuit` translator

### Bug Fixes and Other Changes

 * Update Braket dependencies
 * update noise operation in program context
 * ci: Harden GitHub Actions

## v1.48.1 (2023-07-07)

### Bug Fixes and Other Changes

 * use event callbacks to add braket user agents

## v1.48.0 (2023-07-06)

### Features

 * draw barrier/delay with qubits

### Bug Fixes and Other Changes

 * constrain boto version
 * pass the expression field when parsing to FreeParameterExpression
 * pass gate modifiers to to_unitary

## v1.47.0 (2023-06-30)

### Features

 * add optional third angle to MS gate

### Bug Fixes and Other Changes

 * mixed free parameters and floats

## v1.46.0 (2023-06-29)

### Features

 * add string support for FreeParameterExpressions

## v1.45.0 (2023-06-28)

### Features

 * enum for device arns

## v1.44.0 (2023-06-26)

### Features

 * add support for qubits in pulse delay and barrier

## v1.43.0 (2023-06-22)

### Features

 * add support for Python 3.11

## v1.42.2 (2023-06-20)

### Bug Fixes and Other Changes

 * pulse plotting with barriers that have no argument

## v1.42.1 (2023-06-07)

### Bug Fixes and Other Changes

 * Add more information to docstring about job name requirements

## v1.42.0 (2023-06-05)

### Features

 * support for the run_batch() method on LocalSimulator

## v1.41.0 (2023-05-30)

### Features

 * AHS ir valid input for `LocalSimulator`

### Bug Fixes and Other Changes

 * re-enable & update content as per BCS

## v1.40.0 (2023-05-25)

### Features

 * gate modifiers

## v1.39.1 (2023-05-18)

### Bug Fixes and Other Changes

 * exclude default none for kms
 * test: Rename ionQdevice to Harmony in tests
 * making kms key optional

### Testing and Release Infrastructure

 * twine check action

## v1.39.0 (2023-05-16)

### Features

 * Introduce error mitigation

## v1.38.3 (2023-05-16)

### Bug Fixes and Other Changes

 * Remove `exclude_none` from device params

## v1.38.2 (2023-05-16)

### Bug Fixes and Other Changes

 * docs: add a linter to check proper rst formatting and fix up incorrect docs

## v1.38.1 (2023-05-11)

### Bug Fixes and Other Changes

 * hardcode the language used by Sphinx instead of falling back on the default

## v1.38.0 (2023-05-01)

### Features

 * add tagging for python 3.10 images

## v1.37.1 (2023-04-25)

### Bug Fixes and Other Changes

 * test: fix tox parallel issues with unsorted sets
 * Mock task creation against QPUs for tracker
 * test: order terminal states for quantum jobs

### Testing and Release Infrastructure

 * speed up unit testing by automatically parallelizing the CPU workers for test runs

## v1.37.0 (2023-04-11)

### Features

 * Introduce AHS-related utils from examples repo
 * upgrade container URIs for python 3.9

### Bug Fixes and Other Changes

 * correct the python version in the container integ tests to the correct one
 * Use device-specific poll interval if provided

## v1.36.5 (2023-04-03)

### Bug Fixes and Other Changes

 * support adding a single instruction to moments
 * typo in noise_model.py

## v1.36.4 (2023-03-27)

### Bug Fixes and Other Changes

 * Export from ahs and timings modules

## v1.36.3 (2023-03-21)

### Bug Fixes and Other Changes

 * ignore CompilerDirective when calculating unitary
 * add DoubleAngledGate as exported symbol

## v1.36.2.post0 (2023-03-16)

### Documentation Changes

 * update README information

## v1.36.2 (2023-03-14)

### Bug Fixes and Other Changes

 * update job test for python3.8
 * Look for price offer url in env variable

## v1.36.1 (2023-03-07)

### Bug Fixes and Other Changes

 * test: make simulator tracking integ test more robust

## v1.36.0 (2023-03-03)

### Deprecations and Removals

 * deprecate python 3.7

### Bug Fixes and Other Changes

 * Take advantage of some nice Python 3.8 features
 * Include setuptools in requirements

## v1.35.5 (2023-02-16)

### Bug Fixes and Other Changes

 * Prevent float-FreeParameter comparison
 * build(deps): bump aws-actions/stale-issue-cleanup from 3 to 6

### Documentation Changes

 * Remove black badge

### Testing and Release Infrastructure

 * add dependabot updates for GH actions
 * change publish to pypi wf to use release/v1

## v1.35.4.post0 (2023-02-15)

### Documentation Changes

 * Add note to call result to estimate sim tasks

### Testing and Release Infrastructure

 * update github workflows for node12 retirement

## v1.35.4 (2023-02-09)

### Bug Fixes and Other Changes

 * update: adding build for python 3.10
 * copy session with env and profile.

## v1.35.3 (2023-01-17)

### Bug Fixes and Other Changes

 * update: updating for Aspen-M3

## v1.35.2 (2023-01-04)

### Bug Fixes and Other Changes

 * specify all for density matrix target
 * remove OS signaling from run_batch unit test
 * update ascii symbols for angled gate adjoint
 * remove ascii_characters dynamic property for sum observables
 * abort batch task submission on interrupt

## v1.35.1 (2022-12-08)

### Bug Fixes and Other Changes

 * Hamiltonian ascii simplification

## v1.35.0 (2022-12-07)

### Features

 * adjoint gradient

### Bug Fixes and Other Changes

 * docs: Update examples-getting-started.rst
 * loosen oqpy requirement

## v1.34.3.post0 (2022-11-21)

### Testing and Release Infrastructure

 * Remove Ocean plugin from dependent tests

## v1.34.3 (2022-11-17)

### Bug Fixes and Other Changes

 * remove d-wave content

## v1.34.2 (2022-11-17)

### Bug Fixes and Other Changes

 * Plot the phase between 0 and 2*pi

## v1.34.1 (2022-11-15)

### Bug Fixes and Other Changes

 * update import path in error message

## v1.34.0 (2022-11-14)

### Features

 * adding Braket checkstyle checks.

## v1.33.2 (2022-11-10)

### Bug Fixes and Other Changes

 * Reference code from the current commit for dependent tests

## v1.33.1 (2022-11-08)

### Bug Fixes and Other Changes

 * bump oqpy version

## v1.33.0.post0 (2022-11-02)

### Documentation Changes

 * update example notebook links

## v1.33.0 (2022-11-01)

### Features

 * Support analog Hamiltonian simulations

## v1.32.1.post0 (2022-10-25)

### Documentation Changes

 * update FreeParameter class with example

## v1.32.1 (2022-10-24)

### Bug Fixes and Other Changes

 * require boto containing latest API changes

## v1.32.0 (2022-10-20)

### Features

 * Add support for pulse control

## v1.31.1 (2022-10-12)

### Bug Fixes and Other Changes

 * update inputs on program's copy

## v1.31.0 (2022-09-26)

### Features

 * support inputs in the device interface

### Bug Fixes and Other Changes

 * add missing case for input handling
 * don't provide profile name for default profile

## v1.30.2 (2022-09-22)

### Bug Fixes and Other Changes

- copy profile name

## v1.30.1 (2022-09-20)

### Bug Fixes and Other Changes

- update paths within docker image to posix

## v1.30.0 (2022-09-16)

### Features

- IonQ native gates

## v1.29.4 (2022-09-08)

### Bug Fixes and Other Changes

- Simultaneous measurement of identity on all qubits

## v1.29.3 (2022-09-05)

### Bug Fixes and Other Changes

- making local jobs stream output.

## v1.29.2 (2022-08-25)

### Bug Fixes and Other Changes

- Updating documentation and type hints.

## v1.29.1 (2022-08-18)

### Bug Fixes and Other Changes

- updating test cost tracking integ test to use M2.

## v1.29.0.post0 (2022-08-17)

### Testing and Release Infrastructure

- Avoid mutation of fixtures

## v1.29.0 (2022-08-10)

### Features

- Pauli strings

### Testing and Release Infrastructure

- Don't run tests on push to feature branches
- Add SF plugin to dependent tests

## v1.28.1 (2022-08-05)

### Bug Fixes and Other Changes

- fix future warning

## v1.28.0 (2022-08-05)

### Features

- OpenQASM default IR and OpenQASM Local Simulator

### Bug Fixes and Other Changes

- update simulator version
- handle -0 edge case in result type hash

## v1.27.1 (2022-07-29)

### Bug Fixes and Other Changes

- customer script errors not shown when local jobs run from a notebook.

## v1.27.0 (2022-07-26)

### Features

- provide easy mechanism to update the local container when running local job.

## v1.26.2 (2022-07-21)

### Bug Fixes and Other Changes

- docs: Update README to include guidance for integrations

## v1.26.1 (2022-07-19)

### Bug Fixes and Other Changes

- Lazily parse schemas for devices so getDevice calls do not rely …

## v1.26.0 (2022-07-18)

### Features

- SDK Cost Tracker

## v1.25.2 (2022-06-22)

### Bug Fixes and Other Changes

- Set the range for amazon-braket-schemas to >= 1.10.0 for the latest device schemas needed.

## v1.25.1.post0 (2022-06-17)

### Documentation Changes

- remove s3 references from README

## v1.25.1 (2022-06-16)

### Bug Fixes and Other Changes

- change failureReason string check to let test pass

## v1.25.0 (2022-06-08)

### Features

- Add method for updating the user agent for braket client

## v1.24.0 (2022-06-02)

### Features

- Add support for photonic computations

## v1.23.2 (2022-05-24)

### Bug Fixes and Other Changes

- pin coverage dependency only for test extra

## v1.23.1 (2022-05-20)

### Bug Fixes and Other Changes

- removing validation for disable_qubit_rewiring

## v1.23.0 (2022-05-19)

### Features

- allow job role to be set via env variable
- allow user to set region+endpoint through env variables

## v1.22.0 (2022-05-18)

### Features

- Noise models

## v1.21.1 (2022-05-17)

### Bug Fixes and Other Changes

- broken links for examples

## v1.21.0 (2022-05-10)

### Features

- Gate and Circuit inversion

## v1.20.0 (2022-05-04)

### Features

- support local simulators for jobs

## v1.19.0 (2022-04-19)

### Deprecations and Removals

- use to_unitary rather than as_unitary.

### Bug Fixes and Other Changes

- align ECR gate definition with OQC
- add device arn error handling for badly formed ARNs

## v1.18.2 (2022-04-18)

### Bug Fixes and Other Changes

- stringify hyperparameters automatically

## v1.18.1 (2022-04-14)

### Bug Fixes and Other Changes

- add exception handling to local job test
- Run github workflows on feature branches

## v1.18.0.post0 (2022-04-06)

### Documentation Changes

- Specify DEVICE_REGIONS docs.

## v1.18.0 (2022-03-07)

### Features

- Add support for running OpenQASM programs

## v1.17.0 (2022-03-02)

### Features

- Add parameterized circuits

## v1.16.1 (2022-03-01)

### Bug Fixes and Other Changes

- Add the OQC ARN to the integ tests

## v1.16.0 (2022-02-27)

### Features

- LHR region configuration

### Bug Fixes and Other Changes

- Oqc release

## v1.15.0 (2022-02-15)

### Features

- Update region switching for regional device arns (#169)

## v1.14.0.post0 (2022-02-11)

### Documentation Changes

- fix documentation on environment variable to match the code.

## v1.14.0 (2022-02-02)

### Features

- adding TwoQubitPauliChannel

## v1.13.0 (2022-01-27)

### Features

- added controlled-sqrt-not gate

## v1.12.0 (2022-01-25)

### Features

- Added is_available property to AwsDevice
- optimize IAM role retrieval

### Bug Fixes and Other Changes

- Enable jobs integration tests

## v1.11.1 (2021-12-09)

### Bug Fixes and Other Changes

- remove extraneous reference from local job container setup

## v1.11.0 (2021-12-02)

### Features

- Adding integration tests for DM1

## v1.10.0 (2021-11-29)

### Features

- Add support for jobs

### Bug Fixes and Other Changes

- Skip jobs integration tests

## v1.9.5.post0 (2021-11-04)

### Testing and Release Infrastructure

- Pin docutils<0.18 in doc requirements

## v1.9.5 (2021-10-05)

### Bug Fixes and Other Changes

- Pin Coverage 5.5

## v1.9.4 (2021-10-04)

### Bug Fixes and Other Changes

- fixed a spelling nit

## v1.9.3 (2021-10-01)

### Bug Fixes and Other Changes

- rigetti typo

## v1.9.2 (2021-09-30)

## v1.9.1 (2021-09-24)

### Bug Fixes and Other Changes

- Have tasks that are failed output the failure reason from tas…

## v1.9.0 (2021-09-09)

### Features

- Verbatim boxes

## v1.8.0 (2021-08-23)

### Features

- Calculate arbitrary observables when `shots=0`

### Bug Fixes and Other Changes

- Remove immutable default args

## v1.7.5 (2021-08-18)

### Bug Fixes and Other Changes

- Add test for local simulator device names

### Documentation Changes

- Add documentation for support

### Testing and Release Infrastructure

- Update copyright notice

## v1.7.4 (2021-08-06)

### Bug Fixes and Other Changes

- Flatten Tensor Products

## v1.7.3.post0 (2021-08-05)

### Documentation Changes

- Modify README.md to include update instructions

## v1.7.3 (2021-07-22)

### Bug Fixes and Other Changes

- Add json schema validation for dwave device schemas.

## v1.7.2 (2021-07-14)

### Bug Fixes and Other Changes

- add json validation for device schema in unit tests

## v1.7.1 (2021-07-02)

### Bug Fixes and Other Changes

- Result Type syntax in IR
- Update test_circuit.py

## v1.7.0 (2021-06-25)

### Features

- code Circuit.as_unitary()

### Bug Fixes and Other Changes

- allow integral number types that aren't type int

## v1.6.5 (2021-06-23)

### Bug Fixes and Other Changes

- Get qubit count without instantiating op
- Require qubit indices to be integers

## v1.6.4 (2021-06-10)

### Bug Fixes and Other Changes

- fallback on empty dict for device level parameters

## v1.6.3 (2021-06-04)

### Bug Fixes and Other Changes

- use device data to create device level parameter data when creating a…

## v1.6.2 (2021-05-28)

### Bug Fixes and Other Changes

- exclude null values from device parameters for annealing tasks

## v1.6.1 (2021-05-25)

### Bug Fixes and Other Changes

- copy the boto3 session using the default botocore session

## v1.6.0.post0 (2021-05-24)

### Documentation Changes

- Add reference to the noise simulation example notebook

## v1.6.0 (2021-05-24)

### Features

- Noise operators

### Testing and Release Infrastructure

- Use GitHub source for tox tests

## v1.5.16 (2021-05-05)

### Bug Fixes and Other Changes

- Added /taskArn to id field in AwsQuantumTask **repr**

### Documentation Changes

- Fix link, typos, order

## v1.5.15 (2021-04-08)

### Bug Fixes and Other Changes

- stop manually managing waiting treads in quantum task batch requests

## v1.5.14 (2021-04-07)

### Bug Fixes and Other Changes

- roll back dwave change
- Dwave roll back
- use device data to create device level parameter data when creating a quantum annealing task

## v1.5.13 (2021-03-26)

### Bug Fixes and Other Changes

- check for task completion before entering async event loop
- remove unneeded get_quantum_task calls

## v1.5.12 (2021-03-25)

### Bug Fixes and Other Changes

- Update user_agent for AwsSession

## v1.5.11 (2021-03-22)

### Bug Fixes and Other Changes

- Fix broken repository links

## v1.5.10.post2 (2021-03-19)

### Testing and Release Infrastructure

- Run unit tests for dependent packages

## v1.5.10.post1 (2021-03-16)

### Documentation Changes

- Remove STS calls from examples

## v1.5.10.post0 (2021-03-11)

### Testing and Release Infrastructure

- Add Python 3.9

## v1.5.10 (2021-03-03)

### Bug Fixes and Other Changes

- Don't return NotImplemented for boolean
- Use np.eye for identity
- AngledGate equality checks angles
- Unitary equality checks matrix
- Remove hardcoded device ARNs

### Documentation Changes

- Wording changes
- Add note about AWS region in README

### Testing and Release Infrastructure

- Use main instead of PyPi for build dependencies
- very minor test changes

## v1.5.9.post0 (2021-02-22)

### Documentation Changes

- remove unneeded calls to sts from the README
- adjust s3_folder naming in README to clarify which bucket to use

## v1.5.9 (2021-02-06)

### Bug Fixes and Other Changes

- Search for unknown QPUs

## v1.5.8 (2021-01-29)

### Bug Fixes and Other Changes

- Remove redundant statement, boost coverage
- convert measurements to indices without allocating a high-dimens…

### Testing and Release Infrastructure

- Raise coverage to 100%

## v1.5.7 (2021-01-27)

### Bug Fixes and Other Changes

- More scalable eigenvalue calculation

## v1.5.6 (2021-01-21)

### Bug Fixes and Other Changes

- ensure AngledGate casts its angle argument to float so it can be…

## v1.5.5 (2021-01-15)

### Bug Fixes and Other Changes

- get correct event loop for task results after running a batch over multiple threads

## v1.5.4 (2021-01-12)

### Bug Fixes and Other Changes

- remove window check for polling-- revert to polling at all times
- update result_types to use hashing

### Testing and Release Infrastructure

- Enable Codecov

## v1.5.3 (2020-12-31)

### Bug Fixes and Other Changes

- Update range of random qubit in test_qft_iqft_h

## v1.5.2.post0 (2020-12-30)

### Testing and Release Infrastructure

- Add build badge
- Use GitHub Actions for CI

## v1.5.2 (2020-12-22)

### Bug Fixes and Other Changes

- Get regions for QPUs instead of providers
- Do not search for simulators in wrong region

## v1.5.1 (2020-12-10)

### Bug Fixes and Other Changes

- Use current region for simulators in get_devices

## v1.5.0 (2020-12-04)

### Features

- Always accept identity observable factors

### Documentation Changes

- backticks for batching tasks
- add punctuation to aws_session.py
- fix backticks, missing periods in quantum task docs
- fix backticks, grammar for aws_device.py

## v1.4.1 (2020-12-04)

### Bug Fixes and Other Changes

- Correct integ test bucket

## v1.4.0.post0 (2020-12-03)

### Documentation Changes

- Point README to developer guide

## v1.4.0 (2020-11-26)

### Features

- Enable retries when retrieving results from AwsQuantumTaskBatch.

## v1.3.1 (2020-11-25)

## v1.3.0 (2020-11-23)

### Features

- Enable explicit qubit allocation
- Add support for batch execution

### Bug Fixes and Other Changes

- Correctly cache status

## v1.2.0 (2020-11-02)

### Features

- support tags parameter for create method in AwsQuantumTask

## v1.1.4.post0 (2020-10-30)

### Testing and Release Infrastructure

- update codeowners

## v1.1.4 (2020-10-29)

### Bug Fixes and Other Changes

- Enable simultaneous measurement of observables with shared factors
- Add optimization to only poll during execution window

## v1.1.3 (2020-10-20)

### Bug Fixes and Other Changes

- add observable targets not in instructions to circuit qubit count and qubits

## v1.1.2.post1 (2020-10-15)

### Documentation Changes

- add sample notebooks link

## v1.1.2.post0 (2020-10-05)

### Testing and Release Infrastructure

- change check for s3 bucket exists
- change bucket creation setup for integ tests

## v1.1.2 (2020-10-02)

### Bug Fixes and Other Changes

- Add error for target qubit set size not equal to operator qubit size in instruction
- Add error message for running a circuit without instructions

### Documentation Changes

- Update docstring for measurement_counts

## v1.1.1.post2 (2020-09-29)

### Documentation Changes

- Add D-Wave Advantage_system1 arn

## v1.1.1.post1 (2020-09-10)

### Testing and Release Infrastructure

- fix black formatting

## v1.1.1.post0 (2020-09-09)

### Testing and Release Infrastructure

- Add CHANGELOG.md

## v1.1.1 (2020-09-09)

### Bug Fixes

- Add handling for solution_counts=[] for annealing result

## v1.1.0 (2020-09-08)

### Features

- Add get_devices to search devices based on criteria

### Bug Fixes

- Call async_result() before calling result()
- Convert amplitude result to a complex number

## v1.0.0.post1 (2020-08-14)

### Documentation

- add readthedocs link to README

## v1.0.0 (2020-08-13)

This is the public release of the Amazon Braket Python SDK!

The Amazon Braket Python SDK is an open source library that provides a framework that you can use to interact with quantum computing devices through Amazon Braket.
