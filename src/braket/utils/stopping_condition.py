from dataclasses import dataclass


@dataclass
class StoppingCondition:
    def __init__(self, maxRuntimeInSeconds: int = 100_000, maxTaskLimit: int = 5 * 24 * 60 * 60):
        self.maxRuntimeInSeconds = maxRuntimeInSeconds
        self.maxTaskLimit = maxTaskLimit
