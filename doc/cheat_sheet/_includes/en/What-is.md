[Amazon Braket](https://aws.amazon.com/braket/) is a fully managed AWS service for building, testing, and running quantum algorithms on managed simulators, local simulators, emulators, and supported quantum hardware.

| Need | Start with |
|---|---|
| Build a circuit | `from braket.circuits import Circuit` |
| Run on AWS | `from braket.aws import AwsDevice` |
| Run locally | `from braket.devices import LocalSimulator` |
| Run many parameter sets together | `from braket.program_sets import CircuitBinding, ProgramSet` |
| Run quantum-classical code | `from braket.jobs import hybrid_job` |
