from dataclasses import dataclass


@dataclass
class OutputDataConfig:
    def __init__(
        self, s3Path="s3://braket-{region}-{account}/jobs/{jobname}/output", kmsKeyId=None
    ):
        self.s3Path = s3Path
        self.kmsKeyId = kmsKeyId
