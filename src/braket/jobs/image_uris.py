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
from functools import cache


class Framework(str, Enum):
    """Supported Frameworks for pre-built containers"""

    BASE = "BASE"
    PL_TENSORFLOW = "PL_TENSORFLOW"
    PL_PYTORCH = "PL_PYTORCH"


def built_in_images(region: str) -> set[str]:
    """Checks a region for built in Braket images.

    Args:
        region (str): The AWS region to check for images

    Returns:
        set[str]: returns a set of built images
    """
    return {retrieve_image(framework, region) for framework in Framework}


@cache
def retrieve_image(framework: Framework, region: str) -> str:
    """Retrieves the ECR URI for the Docker image matching the specified arguments.

    Args:
        framework (Framework): The name of the framework.
        region (str): The AWS region for the Docker image.

    Returns:
        str: The ECR URI for the corresponding Amazon Braket Docker image.

    Raises:
        ValueError: If any of the supplied values are invalid or the combination of inputs
            specified is not supported.
    """
    # Validate framework
    framework = Framework(framework)
    config = _config_for_framework(framework)
    registry = _registry_for_region(config, region)
    tag = f"{config['repository']}:latest"
    return f"{registry}.dkr.ecr.{region}.amazonaws.com/{tag}"


def _config_for_framework(framework: Framework) -> dict[str, str]:
    """Loads the JSON config for the given framework.

    Args:
        framework (Framework): The framework whose config needs to be loaded.

    Returns:
        dict[str, str]: Dict that contains the configuration for the specified framework.
    """
    fname = os.path.join(os.path.dirname(__file__), "image_uri_config", f"{framework.lower()}.json")
    with open(fname, encoding="utf-8") as f:
        return json.load(f)


def _registry_for_region(config: dict[str, str], region: str) -> str:
    """Retrieves the registry for the specified region from the configuration.

    Args:
        config (dict[str, str]): Dict containing the framework configuration.
        region (str): str that specifies the region for which the registry is retrieved.

    Returns:
        str: str that specifies the registry for the supplied region.

    Raises:
        ValueError: If the supplied region is invalid or not supported.
    """
    if region not in (supported_regions := config["supported_regions"]):
        raise ValueError(
            f"Unsupported region: {region}. You may need to upgrade your SDK version for newer "
            f"regions. Supported region(s): {supported_regions}"
        )
    return config["registry"]
