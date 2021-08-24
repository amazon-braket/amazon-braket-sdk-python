import time
from typing import Optional, Union


def log_metric(
    metric_name: str,
    value: Union[float, int],
    timestamp: Optional[float] = None,
    iteration_number: Optional[int] = None,
) -> None:
    """
    Records Braket Job metrics.

    Args:
      metric_name (str) : The name of the metric.
      value (Union[float, int]) : The value of the metric
      timestamp (Optional[float]) : The timestamp of the metric, specified as the time in seconds
         since the epoch. Optional - will default to the current system time if not specified.
      iteration_number (Optional[int]) : The iteration number of the metric. Optional.
    """
    logged_timestamp = timestamp or time.time()
    metric_list = [f"Metrics - timestamp={logged_timestamp}; {metric_name}={value};"]
    if iteration_number is not None:
        metric_list.append(f" iteration_number={iteration_number};")
    metric_line = "".join(metric_list)
    print(metric_line)
