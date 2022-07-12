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

from unittest.mock import Mock

from braket.tracking.tracking_context import (
    active_trackers,
    broadcast_event,
    deregister_tracker,
    register_tracker,
)


def test_tracking_context():
    assert active_trackers() == set()


def test_register_deregister_tracker():
    register_tracker("foo")
    assert active_trackers() == {"foo"}
    register_tracker("bar")
    register_tracker("bar")
    assert active_trackers() == {"foo", "bar"}
    deregister_tracker("foo")
    assert active_trackers() == {"bar"}
    deregister_tracker("bar")


def test_broadcast_event():
    tracker = Mock()
    register_tracker(tracker)
    broadcast_event("EVENT")
    tracker.receive_event.assert_called_with("EVENT")
    deregister_tracker(tracker)
