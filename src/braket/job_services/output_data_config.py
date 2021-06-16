from dataclasses import dataclass


@dataclass
class OutputDataConfig:
    """
    Configuration specifying the location for the output of the job.
    """

    s3Path = "s3://braket-{region}-{account}/jobs/{jobname}/output"
    kmsKeyId = None
