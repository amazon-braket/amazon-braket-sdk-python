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

from dataclasses import dataclass


@dataclass
class _TrackingEvent:
    arn: str


@dataclass
class _TaskCreationEvent(_TrackingEvent):
    shots: int
    is_job_task: bool
    device: str


@dataclass
class _TaskCompletionEvent(_TrackingEvent):
    execution_duration: float | None
    status: str
    has_reservation_arn: bool = False


@dataclass
class _TaskStatusEvent(_TrackingEvent):
    status: str
