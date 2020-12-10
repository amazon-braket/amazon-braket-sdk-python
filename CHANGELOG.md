# Changelog

## v1.5.1 (2020-12-10)

### Bug Fixes and Other Changes

 * Use current region for simulators in get_devices

## v1.5.0 (2020-12-04)

### Features

 * Always accept identity observable factors

### Documentation Changes

 * backticks for batching tasks
 * add punctuation to aws_session.py
 * fix backticks, missing periods in quantum task docs
 * fix backticks, grammar for aws_device.py

## v1.4.1 (2020-12-04)

### Bug Fixes and Other Changes

 * Correct integ test bucket

## v1.4.0.post0 (2020-12-03)

### Documentation Changes

 * Point README to developer guide

## v1.4.0 (2020-11-26)

### Features

 * Enable retries when retrieving results from AwsQuantumTaskBatch.

## v1.3.1 (2020-11-25)

## v1.3.0 (2020-11-23)

### Features

 * Enable explicit qubit allocation
 * Add support for batch execution

### Bug Fixes and Other Changes

 * Correctly cache status

## v1.2.0 (2020-11-02)

### Features

 * support tags parameter for create method in AwsQuantumTask

## v1.1.4.post0 (2020-10-30)

### Testing and Release Infrastructure

 * update codeowners

## v1.1.4 (2020-10-29)

### Bug Fixes and Other Changes

 * Enable simultaneous measurement of observables with shared factors
 * Add optimization to only poll during execution window

## v1.1.3 (2020-10-20)

### Bug Fixes and Other Changes

 * add observable targets not in instructions to circuit qubit count and qubits

## v1.1.2.post1 (2020-10-15)

### Documentation Changes

 * add sample notebooks link

## v1.1.2.post0 (2020-10-05)

### Testing and Release Infrastructure

 * change check for s3 bucket exists
 * change bucket creation setup for integ tests

## v1.1.2 (2020-10-02)

### Bug Fixes and Other Changes

 * Add error for target qubit set size not equal to operator qubit size in instruction
 * Add error message for running a circuit without instructions

### Documentation Changes

 * Update docstring for measurement_counts

## v1.1.1.post2 (2020-09-29)

### Documentation Changes

 * Add D-Wave Advantage_system1 arn

## v1.1.1.post1 (2020-09-10)

### Testing and Release Infrastructure

 * fix black formatting

## v1.1.1.post0 (2020-09-09)

### Testing and Release Infrastructure

 * Add CHANGELOG.md

## v1.1.1 (2020-09-09)

### Bug Fixes
* Add handling for solution_counts=[] for annealing result

## v1.1.0 (2020-09-08)

### Features
* Add get_devices to search devices based on criteria

### Bug Fixes
* Call async_result() before calling result()
* Convert amplitude result to a complex number

## v1.0.0.post1 (2020-08-14)

### Documentation

* add readthedocs link to README

## v1.0.0 (2020-08-13)

This is the public release of the Amazon Braket Python SDK!

The Amazon Braket Python SDK is an open source library that provides a framework that you can use to interact with quantum computing devices through Amazon Braket.
