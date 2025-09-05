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

from botocore import awsrequest

import braket._schemas as braket_schemas
import braket._sdk as braket_sdk


def test_default_user_agent(aws_session):
    braket_agents = [
        f"BraketSdk/{braket_sdk.__version__}",
        f"BraketSchemas/{braket_schemas.__version__}",
        "NotebookInstance/",
    ]

    def assert_in_user_agent(request: awsrequest.AWSPreparedRequest, **kwargs):
        user_agent = request.headers.get("User-Agent")
        for agent in braket_agents:
            assert bytes(agent, "utf8") in user_agent

    aws_session.braket_client.meta.events.register("before-send.braket", assert_in_user_agent)
    aws_session.search_devices()


def test_add_user_agent(aws_session):
    aws_session.add_braket_user_agent("foo/1.0")

    def assert_in_user_agent(request: awsrequest.AWSPreparedRequest, **kwargs):
        user_agent = request.headers.get("User-Agent")
        assert b"foo/1.0" in user_agent

    aws_session.braket_client.meta.events.register("before-send.braket", assert_in_user_agent)
    aws_session.search_devices()
