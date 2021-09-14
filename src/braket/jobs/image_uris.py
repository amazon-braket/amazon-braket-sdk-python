# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import json
import os
from enum import Enum
from typing import Dict


class Framework(str, Enum):
    """Supported Frameworks for pre-built containers"""

    BASE = "BASE"
    PL_TENSORFLOW = "PL_TENSORFLOW"
    PL_PYTORCH = "PL_PYTORCH"


def retrieve_image(framework: Framework, region: str):
    """Retrieves the ECR URI for the Docker image matching the given arguments.

    Args:
        framework (str): The name of the framework.
        region (str): The AWS region for the docker image.

    Returns:
        str: The ECR URI for the corresponding Amazon Braket Docker image.

    Raises:
        ValueError: If any of the supplied values are invalid or the combination of inputs
            specified is not supported.
    """
    # Validate framework
    framework = Framework(framework)
    config = _config_for_framework(framework)
    framework_version = max(version for version in config["versions"])
    version_config = _extract_config_for_version(config, framework_version)
    registry = _registry_for_region(version_config, region)
    tag = f"{version_config['repository']}:{framework_version}-cpu-py37-ubuntu18.04"
    return f"{registry}.dkr.ecr.{region}.amazonaws.com/{tag}"


def _config_for_framework(framework: Framework) -> Dict[str, str]:
    """Loads the JSON config for the given framework.

    Args:
        framework (Framework): The framework whose config needs to be loaded.

    Returns:
        Dict[str, str]: Dict containing the configuration for the specified framework.
    """
    fname = os.path.join(os.path.dirname(__file__), "image_uri_config", f"{framework.lower()}.json")
    with open(fname) as f:
        return json.load(f)


def _registry_for_region(config: Dict[str, str], region: str) -> str:
    """Retrieves the registry for the specified region from the configuration.

    Args:
        config (Dict[str, str]): Dict containing the framework configuration.
        region (str): str representing the region for which the registry needs to be retrieved.

    Returns:
        str: str specifying the registry for the supplied region.

    Raises:
        ValueError: If the supplied region is invalid or not supported.
    """
    registry_config = config["registries"]
    if region not in registry_config:
        raise ValueError(
            f"Unsupported region: {region}. You may need to upgrade your SDK version for newer "
            f"regions. Supported region(s): {list(registry_config.keys())}"
        )
    return registry_config[region]


def _extract_config_for_version(config: Dict[str, str], framework_version: str) -> Dict[str, str]:
    """Loads the configuration for the specified framework version.

    Args:
        config (Dict[str, str]): The configuration for a specific framework.
        framework_version (str): The version to extract configuration for.

    Returns:
        Dict[str, str]: Dict containing the version specific configuration.

    Raises:
        ValueError: If the specified framework version is invalid or not supported.
    """
    if framework_version in config.get("versions", {}):
        return config["versions"][framework_version]
    raise ValueError(
        f"Unsupported version: {framework_version}. "
        "You may need to upgrade your SDK version for newer versions. "
        f"Supported version(s): {list(config['versions'].keys())}."
    )
