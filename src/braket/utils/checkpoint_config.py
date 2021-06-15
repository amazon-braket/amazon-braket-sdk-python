from dataclasses import dataclass


@dataclass
class CheckpointConfig(object):
    def __init__(
        self,
        localPath="/opt/jobs/checkpoints",
        s3Uri="s3://braket-{region}-{account}/jobs/{jobname}/checkpoints",
    ):
        self.s3Uri = s3Uri
        self.localPath = localPath
