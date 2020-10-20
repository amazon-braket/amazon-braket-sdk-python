# Changelog

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
