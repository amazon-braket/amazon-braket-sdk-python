from dataclasses import dataclass


@dataclass
class InstanceConfig:
    def __init__(
        self,
        instanceType: str = "ml.m5.large",
        instanceCount: int = 1,
        volumeSizeInGB: int = 30,
        volumeKmsKey: str = None,
    ):
        self.instanceType = instanceType
        self.instanceCount = instanceCount
        self.volumeSizeInGB = volumeSizeInGB
        self.volumeKmsKey = volumeKmsKey
