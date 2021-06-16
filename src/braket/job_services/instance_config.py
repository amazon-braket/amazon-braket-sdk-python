from dataclasses import dataclass


@dataclass
class InstanceConfig:
    """
    Configuration of the instances to be used for executing the job.
    """

    instanceType: str = "ml.m5.large"
    instanceCount: int = 1
    volumeSizeInGB: int = 30
    volumeKmsKey: str = None
