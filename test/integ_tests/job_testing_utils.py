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

import re

from braket.aws import AwsSession
from braket.jobs import Framework, retrieve_image


def decorator_python_version():
    aws_session = AwsSession()
    image_uri = retrieve_image(Framework.BASE, aws_session.region)
    tag = aws_session.get_full_image_tag(image_uri)
    major_version, minor_version = re.search(r"-py(\d)(\d+)-", tag).groups()
    return int(major_version), int(minor_version)
