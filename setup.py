# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from setuptools import find_namespace_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("src/braket/_sdk/_version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")

setup(
    name="amazon-braket-sdk",
    version=version,
    license="Apache License 2.0",
    python_requires=">= 3.8.2",
    packages=find_namespace_packages(where="src", exclude=("test",)),
    package_dir={"": "src"},
    install_requires=[
        "amazon-braket-schemas>=1.18.0",
        # Pin the latest commit of mcm-sim branch of aws/amazon-braket-default-simulator-python.git
        # to get the version of the simulator that supports the mcm=True argument for Monte Carlo
        # simulation of mid-circuit measurement, which AutoQASM requires.
        # NOTE: This change should remain in the feature/autoqasm branch; do not merge to main.
        "amazon-braket-default-simulator @ git+https://github.com/aws/amazon-braket-default-simulator-python.git@731f2545961abb41dcf13bf26e99f4ded79a15aa#egg=amazon-braket-default-simulator",  # noqa E501
        # Pin the latest commit of the qubit-array branch of ajberdy/oqpy.git to get the version of
        # oqpy which contains changes that AutoQASM relies on, including the QubitArray type.
        # NOTE: This change should remain in the feature/autoqasm branch; do not merge to main.
        "oqpy @ git+https://github.com/ajberdy/oqpy.git@7e5885af6193009265c8195dad7553db02bdfd96#egg=oqpy",  # noqa E501
        "setuptools",
        "backoff",
        "boltons",
        "boto3>=1.22.3",
        "nest-asyncio",
        "networkx",
        "numpy",
        "openpulse",
        "openqasm3",
        "sympy",
        "astunparse",
        "gast",
        "termcolor",
    ],
    extras_require={
        "test": [
            "black",
            "botocore",
            "flake8<=5.0.4",
            "flake8-rst-docstrings",
            "isort",
            "jsonschema==3.2.0",
            "pre-commit",
            "pylint",
            "pytest",
            "pytest-cov",
            "pytest-rerunfailures",
            "pytest-xdist",
            "sphinx",
            "sphinx-rtd-theme",
            "sphinxcontrib-apidoc",
            "tox",
        ],
    },
    include_package_data=True,
    url="https://github.com/aws/amazon-braket-sdk-python",
    author="Amazon Web Services",
    description=(
        "An open source library for interacting with quantum computing devices on Amazon Braket"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="Amazon AWS Quantum",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
