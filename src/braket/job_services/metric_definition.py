from dataclasses import dataclass


@dataclass
class MetricDefinition:
    """'name' specifies the name to use for the metric, 'regex' is the regular
    expression used to extract the metric from the logs."""

    name: str
    regex: str
