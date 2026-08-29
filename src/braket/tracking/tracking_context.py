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

import threading


class TrackingContext:
    def __init__(self):
        self._trackers = set()
        self._lock = threading.Lock()

    def register_tracker(self, tracker: Tracker) -> None:  # ruff:ignore[undefined-name]
        """Registers a tracker.

        Args:
            tracker (Tracker): The tracker.
        """
        with self._lock:
            self._trackers.add(tracker)

    def deregister_tracker(self, tracker: Tracker) -> None:  # ruff:ignore[undefined-name]
        """Deregisters a tracker.

        Args:
            tracker (Tracker): The tracker.
        """
        with self._lock:
            self._trackers.remove(tracker)

    def broadcast_event(self, event: _TrackingEvent) -> None:  # ruff:ignore[undefined-name]
        """Broadcasts an event to all trackers.

        Args:
            event (_TrackingEvent): The event to broadcast.
        """
        # Iterate over a snapshot so that trackers registering or deregistering
        # concurrently (or from receive_event) cannot mutate the set mid-iteration.
        with self._lock:
            trackers = list(self._trackers)
        for tracker in trackers:
            tracker.receive_event(event)

    def active_trackers(self) -> set:
        """Gets the active trackers.

        Returns:
            set: The set of active trackers.
        """
        return self._trackers


_tracking_context = TrackingContext()
register_tracker = _tracking_context.register_tracker
deregister_tracker = _tracking_context.deregister_tracker
broadcast_event = _tracking_context.broadcast_event
active_trackers = _tracking_context.active_trackers
