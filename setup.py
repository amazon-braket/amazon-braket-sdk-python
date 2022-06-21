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

import distutils.cmd
import os
import subprocess
import sysconfig
from pathlib import Path

from setuptools import find_namespace_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("src/braket/_sdk/_version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")


class InstallOQ3Command(distutils.cmd.Command):
    """A custom command to install OpenQASM 3 and build grammars"""

    description = "install OQ3"
    user_options = []

    def initialize_options(self):
        """Set default values for options."""
        pass

    def finalize_options(self):
        """Post-process options."""
        pass

    def run(self):
        """Run command."""
        curdir = os.getcwd()
        if not Path("antlr-4.9.2-complete.jar").is_file():
            subprocess.check_call(
                ["curl", "-O", "https://www.antlr.org/download/antlr-4.9.2-complete.jar"]
            )
        classpath = Path(
            f".:{curdir}",
            f"antlr-4.9.2-complete.jar:{os.environ.get('CLASSPATH', '')}",
        )
        antlr4 = (
            f'java -Xmx500M -cp "{Path(curdir, f"antlr-4.9.2-complete.jar:{classpath}")}" '
            f"org.antlr.v4.Tool"
        )

        os.chdir(
            Path(
                "/",
                *sysconfig.get_paths()["purelib"].split("/"),
                "braket",
                "default_simulator",
                "openqasm",
            )
        )
        subprocess.check_call(
            [
                *antlr4.split(),
                "-Dlanguage=Python3",
                "-visitor",
                "BraketPragmas.g4",
                "-o",
                "dist",
            ]
        )
        os.chdir(curdir)

        if not Path("openqasm").is_dir():
            subprocess.check_call(["git", "clone", "https://github.com/Qiskit/openqasm.git"])
        os.chdir(Path("openqasm", "source", "grammar"))
        subprocess.check_call(
            [
                *antlr4.split(),
                "-o",
                "openqasm_reference_parser",
                "-Dlanguage=Python3",
                "-visitor",
                "qasm3Lexer.g4",
                "qasm3Parser.g4",
            ]
        )
        subprocess.check_call(
            [
                *antlr4.split(),
                "-o",
                Path("..", "openqasm", "openqasm3", "antlr"),
                "-Dlanguage=Python3",
                "-visitor",
                "qasm3Lexer.g4",
                "qasm3Parser.g4",
            ]
        )
        subprocess.check_call(["pip", "install", "."])
        os.chdir(Path("..", "openqasm"))
        subprocess.check_call(["pip", "install", "."])
        os.chdir(Path("..", "..", ".."))


setup(
    name="amazon-braket-sdk",
    version=version,
    license="Apache License 2.0",
    python_requires=">= 3.7.2",
    packages=find_namespace_packages(where="src", exclude=("test",)),
    package_dir={"": "src"},
    install_requires=[
        (
            "amazon-braket-schemas "
            "@ git+https://github.com/aws/amazon-braket-schemas-python.git"
            "@feature/openqasm-local-simulator"
        ),
        (
            "amazon-braket-default-simulator "
            "@ git+https://github.com/aws/amazon-braket-default-simulator-python.git"
            "@openqasm-local-simulator"
        ),
        "backoff",
        "boltons",
        "boto3",
        "nest-asyncio",
        "networkx",
        "numpy",
        "sympy",
    ],
    extras_require={
        "test": [
            "black",
            "botocore",
            "coverage==5.5",
            "flake8",
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
        ]
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    cmdclass={
        "install_oq3": InstallOQ3Command,
    },
)
