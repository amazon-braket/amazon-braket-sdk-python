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

with open("README.md") as fh:
    long_description = fh.read()

with open("src/braket/_sdk/_version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")

setup(
    name="amazon-braket-sdk",
    version=version,
    license="Apache License 2.0",
    python_requires=">= 3.9",
    packages=find_namespace_packages(where="src", exclude=("test",)),
    package_dir={"": "src"},
    install_requires=[
        "amazon-braket-schemas>=1.21.3",
        # Pin the latest commit of mcm-sim branch of the amazon-braket-default-simulator repo
        # to get the version of the simulator that supports the mcm=True argument for Monte Carlo
        # simulation of mid-circuit measurement, which AutoQASM requires.
        # NOTE: This change should remain in the feature/autoqasm branch; do not merge to main.
        "amazon-braket-default-simulator @ git+https://github.com/amazon-braket/amazon-braket-default-simulator-python.git@ab068c860963c29842d7649c741f88da669597eb#egg=amazon-braket-default-simulator",  # noqa E501
        "oqpy~=0.3.5",
        "backoff",
        "boltons",
        "boto3>=1.28.53",
        "cloudpickle==2.2.1",
        "diastatic-malt",
        "nest-asyncio",
        "networkx",
        "numpy<2",
        "openpulse",
        "openqasm3",
        "sympy",
        "backports.entry-points-selectable",
        "astunparse",
        "gast",
        "termcolor",
        "openqasm_pygments",
    ],
    extras_require={
        "test": [
            "black",
            "botocore",
            "flake8<=5.0.4",
            "isort",
            "jsonschema==3.2.0",
            "pre-commit",
            "pylint",
            "pytest",
            "pytest-cov",
            "pytest-rerunfailures",
            "pytest-xdist[psutil]",
            "sphinx",
            "sphinx-rtd-theme",
            "sphinxcontrib-apidoc",
            "tox",
        ],
    },
    include_package_data=True,
    url="https://github.com/amazon-braket/amazon-braket-sdk-python",
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
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
