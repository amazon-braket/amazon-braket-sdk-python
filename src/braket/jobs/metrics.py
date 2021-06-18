from dataclasses import dataclass
from enum import Enum


@dataclass
class MetricDefinition:
    """'name' specifies the name to use for the metric, 'regex' is the regular
    expression used to extract the metric from the logs.
    """

    name: str
    regex: str


class MetricPeriod(Enum):
    """Period over which the cloudwatch metric is aggregated."""

    ONE_MINUTE: int = 60


class MetricStatistic(Enum):
    """Metric data aggregation to use over the specified period."""

    # TODO: Check if we can extract this value directly from CloudWatch from statistics.
    AVG: str = "Average"
