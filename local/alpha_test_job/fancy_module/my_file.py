def start_here():

    with open("/opt/ml/model/job_started.txt", "w") as f:
        f.write("Test job started!!!!!")

    import boto3
    import os
    from braket.aws import AwsDevice
    import braket._sdk as braket_sdk
    from braket.circuits import Circuit

    os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'

    print(f"In customer script with sdk version {braket_sdk.__version__}")

    with open("/opt/ml/model/braket_version.txt", "w") as f:
        f.write(braket_sdk.__version__)

    device = AwsDevice("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
    #device = AwsDevice("arn:aws:braket:::device/qpu/rigetti/Aspen-9")
    s3_folder = ("amazon-braket-318845237731", "testJobs")

    bell = Circuit().h(0).cnot(0, 1)
    for count in range(5):
        task = device.run(bell, s3_folder, shots=100)
        print(task.result().measurement_counts)

