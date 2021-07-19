def start_here():

    with open("/opt/ml/model/job_started.txt", "w") as f:
        f.write("Test job started!!!!!")

    import os

    import numpy as np

    import braket._sdk as braket_sdk
    from braket.aws import AwsDevice
    from braket.circuits import Circuit

    def list_files(startpath):
        for root, dirs, files in os.walk(startpath):
            level = root.replace(startpath, "").count(os.sep)
            indent = " " * 4 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 4 * (level + 1)
            for f in files:
                print(f"{subindent}{f}")

    print(list_files("/opt"))
    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"

    print(f"In customer script with sdk version {braket_sdk.__version__}")

    with open("/opt/ml/input/config/hyperparameters.json") as f:
        print(f.readlines())

    inputdata = np.genfromtxt(
        "/opt/ml/input/data/csvinput/csv-data/inputdata.csv",
        delimiter=",",
    )
    assert inputdata == np.array(
        [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
        ]
    )

    with open("/opt/ml/model/braket_version.txt", "w") as f:
        f.write(braket_sdk.__version__)

    device = AwsDevice("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
    # device = AwsDevice("arn:aws:braket:::device/qpu/rigetti/Aspen-9")
    s3_folder = ("amazon-braket-318845237731", "testJobs")

    bell = Circuit().h(0).cnot(0, 1)
    for count in range(5):
        task = device.run(bell, s3_folder, shots=100)
        print(task.result().measurement_counts)
