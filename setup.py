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
        "amazon-braket-schemas>=1.23.0",
        "amazon-braket-default-simulator>=1.26.0",
        "oqpy~=0.3.5",
        "backoff",
        "boltons",
        "boto3>=1.28.53",
        # SageMaker pinned cloudpickle==2.2.1
        # see https://github.com/aws/sagemaker-python-sdk/issues/4871
        "cloudpickle==2.2.1",
        "nest-asyncio",
        "networkx",
        "numpy",
        "openpulse",
        "openqasm3",
        "sympy",
        "backports.entry-points-selectable",
    ],
    extras_require={
        "test": [
            "black",
            "botocore",
            "flake8",
            "isort",
            "jsonschema==3.2.0",
            "pre-commit",
            "pylint",
            "pytest",
            "pytest-cov",
            "pytest-rerunfailures",
            "pytest-xdist[psutil]",
            "tox",
        ],
        "docs": [
            "sphinx",
            "sphinx-rtd-theme",
            "sphinxcontrib-apidoc",
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
