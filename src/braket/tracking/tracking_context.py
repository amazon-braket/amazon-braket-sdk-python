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

from __future__ import annotations


class TrackingContext:
    def __init__(self):
        self._trackers = set()

    def register_tracker(self, tracker: Tracker):  # noqa F821
        self._trackers.add(tracker)

    def deregister_tracker(self, tracker: Tracker):  # noqa F821
        self._trackers.remove(tracker)

    def broadcast_event(self, event: _TrackingEvent):  # noqa F821
        for tracker in self._trackers:
            tracker.receive_event(event)

    def active_trackers(self):
        return self._trackers


_tracking_context = TrackingContext()
register_tracker = _tracking_context.register_tracker
deregister_tracker = _tracking_context.deregister_tracker
broadcast_event = _tracking_context.broadcast_event
active_trackers = _tracking_context.active_trackers
