import json
import os

import numpy as np
import pennylane as qml
from braket.jobs import save_job_result
from braket.jobs.metrics import log_metric
from scipy.optimize import minimize

import numpy as np
import pennylane as qml


def main():
    print("Starting QCBM training job ...")

    hp_file = os.environ["AMZN_BRAKET_HP_FILE"]
    device_arn = os.environ["AMZN_BRAKET_DEVICE_ARN"]
    input_dir = os.environ["AMZN_BRAKET_INPUT_DIR"]

    # Read the hyperparameters
    with open(hp_file) as f:
        hp_json = json.load(f)
    print("hyperparameters are:", hp_json)

    # device = qml.device(
    #     "braket.aws.qubit",
    #     device_arn=device_arn,
    #     wires=1,
    #     shots=100,
    #     s3_destination_folder=None,
    # )

    device = qml.device("braket.local.qubit", wires=int(hp_json["n_qubits"]))

    print("Loading dataset ...")

    files = os.listdir(f"{input_dir}")
    print(files)

    print(f"{input_dir}/input-data/p_data.npy")

    p_data = np.load(f"{input_dir}/input-data/p_data.npy")

    params = train_circuit(device, hp_json, p_data)

    save_job_result({"params": params.tolist()})


def train_circuit(device, hyperparams, p_data):

    n_qubits = int(hyperparams["n_qubits"])
    n_layers = int(hyperparams["n_layers"])

    init_params = np.random.rand(3 * n_layers * n_qubits)

    qcbm = QCBM(device, n_qubits, n_layers, p_data)

    iteration_number = 0

    def callback(x, iteration_number):
        iteration_number += 1
        # loss = mmd(qcbm(x), p_data)
        loss = kl_divergence(qcbm(x), p_data)
        log_metric(
            metric_name="loss",
            value=loss,
            iteration_number=iteration_number,
        )

    res = minimize(
        lambda x: kl_divergence(qcbm(x), p_data),
        x0=init_params,
        method="Nelder-Mead",
        tol=1e-12,
        options={"maxiter": 200},
        callback=lambda x: callback(x, iteration_number),
    )

    return res.x


class QCBM:
    def __init__(self, device, n_qubits, n_layers, p_data):
        self.dev = device
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.neighbors = [(i, (i + 1) % n_qubits) for i in range(n_qubits)]
        self.p_data = p_data

    def __call__(self, params):
        params = params.reshape(3, self.n_qubits, self.n_layers)

        @qml.qnode(self.dev)
        def qcbm_circuit(params):
            for n in range(self.n_qubits):
                qml.RX(params[0, n, 0], wires=n)
                qml.RZ(params[1, n, 0], wires=n)
                qml.RX(params[2, n, 0], wires=n)
            for L in range(1, self.n_layers):
                self.entangler()
                for n in range(self.n_qubits):
                    qml.RX(params[0, n, L], wires=n)
                    qml.RZ(params[1, n, L], wires=n)
                    qml.RX(params[2, n, L], wires=n)
            return qml.probs(range(self.n_qubits))

        return qcbm_circuit(params)

    def entangler(self):
        for i, j in self.neighbors:
            qml.CNOT(wires=[i, j])


def mmd(px, py, sigma_list=[0.1, 1]):
    x = np.arange(len(px))
    y = np.arange(len(py))
    pxy = px - py
    K = sum(np.exp(-np.abs(x[:, None] - y[None, :]) ** 2 / (2 * s)) for s in sigma_list)
    mmd = pxy @ K @ pxy
    return mmd


def kl_divergence(p, q):
    kl = p @ np.log(p) - p @ np.log(q)
    return kl
