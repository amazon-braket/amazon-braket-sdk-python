from dataclasses import dataclass


@dataclass
class CheckpointConfig:
    """
    Configuration specifying the location where checkpoint data would be stored.
    """

    localPath: str = "/opt/jobs/checkpoints"
    s3Uri: str = "s3://braket-{region}-{account}/jobs/{jobname}/checkpoints"
