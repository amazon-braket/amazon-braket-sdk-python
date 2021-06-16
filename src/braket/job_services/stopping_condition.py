from dataclasses import dataclass


@dataclass
class StoppingCondition:
    """
    Conditions denoting when the job should be forcefully stopped.
    """

    maxRuntimeInSeconds: int = 100_000
    maxTaskLimit: int = 5 * 24 * 60 * 60
