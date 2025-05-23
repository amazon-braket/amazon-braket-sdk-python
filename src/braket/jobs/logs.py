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

import os
import sys
from collections.abc import Generator

##############################################################################
#
# Support for reading logs
#
##############################################################################
from typing import ClassVar, NamedTuple, Optional

from botocore.exceptions import ClientError

from braket.aws.aws_session import AwsSession


# Position is a tuple that includes the last read timestamp and the number of items that were read
# at that time. This is used to figure out which event to start with on the next read.
class Position(NamedTuple):
    timestamp: str
    skip: bool


class ColorWrap:
    """A callable that prints text in a different color depending on the instance.
    Up to 5 if the standard output is a terminal or a Jupyter notebook cell.
    """

    # For what color each number represents, see
    # https://misc.flogisoft.com/bash/tip_colors_and_formatting#colors
    _stream_colors: ClassVar = [34, 35, 32, 36, 33]

    def __init__(self, force: bool = False):
        """Initialize a `ColorWrap`.

        Args:
            force (bool): If True, the render output is colorized wherever the
                output is. Default: False.
        """
        self.colorize = force or sys.stdout.isatty() or os.environ.get("JPY_PARENT_PID", None)

    def __call__(self, index: int, s: str):
        """Prints the string, colorized or not, depending on the environment.

        Args:
            index (int): The instance number.
            s (str): The string to print.
        """
        if self.colorize:
            self._color_wrap(index, s)
        else:
            print(s)

    def _color_wrap(self, index: int, s: str) -> None:
        """Prints the string in a color determined by the index.

        Args:
            index (int): The instance number.
            s (str): The string to print (color-wrapped).
        """
        print(f"\x1b[{self._stream_colors[index % len(self._stream_colors)]}m{s}\x1b[0m")


def multi_stream_iter(
    aws_session: AwsSession, log_group: str, streams: list[str], positions: dict[str, Position]
) -> Generator[tuple[int, dict]]:
    """Iterates over the available events coming from a set of log streams.
    Log streams are in a single log group interleaving the events from each stream,
    so they yield in timestamp order.

    Args:
        aws_session (AwsSession): The AwsSession for interfacing with CloudWatch.
        log_group (str): The name of the log group.
        streams (list[str]): A list of the log stream names. The the stream number is
            the position of the stream in this list.
        positions (dict[str, Position]): A list of (timestamp, skip) pairs which represent
            the last record read from each stream.

    Yields:
        Generator[tuple[int, dict]]: A tuple of (stream number, cloudwatch log event).
    """
    event_iters = [
        log_stream(aws_session, log_group, s, positions[s].timestamp, positions[s].skip)
        for s in streams
    ]
    events = []
    for s in event_iters:
        try:
            events.append(next(s))
        except StopIteration:  # noqa: PERF203
            events.append(None)

    while any(events):
        i = events.index(min(events, key=lambda x: x["timestamp"] if x else float("inf")))
        yield i, events[i]
        try:
            events[i] = next(event_iters[i])
        except StopIteration:
            events[i] = None


def log_stream(
    aws_session: AwsSession, log_group: str, stream_name: str, start_time: int = 0, skip: int = 0
) -> Generator[dict]:
    """A generator for log items in a single stream.
    This yields all the items that are available at the current moment.

    Args:
        aws_session (AwsSession): The AwsSession for interfacing with CloudWatch.
        log_group (str): The name of the log group.
        stream_name (str): The name of the specific stream.
        start_time (int): The time stamp value to start reading the logs from. Default: 0.
        skip (int): The number of log entries to skip at the start. Default: 0 (This is for
            when there are multiple entries at the same timestamp.)

    Yields:
        Generator[dict]: A CloudWatch log event with the following key-value pairs:
        'timestamp' (int): The time of the event.
        'message' (str): The log event data.
        'ingestionTime' (int): The time the event was ingested.
    """
    next_token = None

    event_count = 1
    while event_count > 0:
        response = aws_session.get_log_events(
            log_group,
            stream_name,
            start_time,
            start_from_head=True,
            next_token=next_token,
        )
        next_token = response["nextForwardToken"]
        events = response["events"]
        event_count = len(events)
        if event_count > skip:
            events = events[skip:]
            skip = 0
        else:
            skip -= event_count
            events = []
        yield from events


def flush_log_streams(
    aws_session: AwsSession,
    log_group: str,
    stream_prefix: str,
    stream_names: list[str],
    positions: dict[str, Position],
    stream_count: int,
    has_streams: bool,
    color_wrap: ColorWrap,
    state: list[str],
    queue_position: Optional[str] = None,
) -> bool:
    """Flushes log streams to stdout.

    Args:
        aws_session (AwsSession): The AwsSession for interfacing with CloudWatch.
        log_group (str): The name of the log group.
        stream_prefix (str): The prefix for log streams to flush.
        stream_names (list[str]): A list of the log stream names. The position of the stream in
            this list is the stream number. If incomplete, the function will check for remaining
            streams and mutate this list to add stream names when available, up to the
            `stream_count` limit.
        positions (dict[str, Position]): A dict mapping stream numbers to (timestamp, skip) pairs
            which represent the last record read from each stream. The function will update this
            list after being called to represent the new last record read from each stream.
        stream_count (int): The number of streams expected.
        has_streams (bool): Whether the function has already been called once all streams have
            been found. This value is possibly updated and returned at the end of execution.
        color_wrap (ColorWrap): An instance of ColorWrap to potentially color-wrap print statements
            from different streams.
        state (list[str]): The previous and current state of the job.
        queue_position (Optional[str]): The current queue position. This is not passed in if the job
            is ran with `quiet=True`

    Raises:
        Exception: Any exception found besides a ResourceNotFoundException.

    Returns:
        bool: Returns 'True' if any streams have been flushed.
    """
    if len(stream_names) < stream_count:
        # Log streams are created whenever a container starts writing to stdout/err,
        # so this list may be dynamic until we have a stream for every instance.
        try:
            streams = aws_session.describe_log_streams(
                log_group,
                stream_prefix,
                limit=stream_count,
            )
            # stream_names = [...] wouldn't modify the list by reference.
            new_streams = [
                s["logStreamName"]
                for s in streams["logStreams"]
                if s["logStreamName"] not in stream_names
            ]
            stream_names.extend(new_streams)
            positions |= [
                (s, Position(timestamp=0, skip=0)) for s in stream_names if s not in positions
            ]
        except ClientError as e:
            # On the very first training job run on an account, there's no
            # log group until the container starts logging, so ignore any
            # errors thrown about that until logging begins.
            err = e.response.get("Error", {})
            if err.get("Code") != "ResourceNotFoundException":
                raise

    if stream_names:
        if not has_streams:
            print()
            has_streams = True
        for idx, event in multi_stream_iter(aws_session, log_group, stream_names, positions):
            color_wrap(idx, event["message"])
            ts, count = positions[stream_names[idx]]
            if event["timestamp"] == ts:
                positions[stream_names[idx]] = Position(timestamp=ts, skip=count + 1)
            else:
                positions[stream_names[idx]] = Position(timestamp=event["timestamp"], skip=1)
    elif queue_position is not None and state[1] == "QUEUED":
        print(f"Job queue position: {queue_position}", end="\n", flush=True)
    elif state[0] != state[1] and state[1] == "RUNNING" and queue_position is not None:
        print("Running:", end="\n", flush=True)
    else:
        print(".", end="", flush=True)
    return has_streams
