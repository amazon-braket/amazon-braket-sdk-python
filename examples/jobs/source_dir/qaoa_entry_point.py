import os
import json
import time

import numpy as np
import braket._sdk as braket_sdk

from braket.jobs import load_job_checkpoint, save_job_checkpoint, save_job_result
from braket.jobs.metrics import log_metric

import networkx as nx
import pennylane as qml
from matplotlib import pyplot as plt

# Import util file from source directory
import source_dir.qaoa_utils as qaoa_utils
            
def init_pl_device(device_arn, num_nodes, max_parallel):
    s3_bucket = os.environ["AMZN_BRAKET_OUT_S3_BUCKET"]
    s3_prefix = "pennylane-test"
    s3_folder = (s3_bucket, s3_prefix)
    print(f"s3_folder: {s3_folder}")
    
    return qml.device(
        "braket.aws.qubit",
        device_arn=device_arn,
        wires=num_nodes,
        shots=1000,
        s3_destination_folder=s3_folder,
        parallel=True,
        max_parallel=max_parallel,
        # poll_timeout_seconds=30,
    )

def start_here():
    # lets see the env variables
    # print statements can be viewed in cloudwatch
    print(os.environ)

    input_dir = os.environ["AMZN_BRAKET_INPUT_DIR"]
    output_dir = os.environ["AMZN_BRAKET_JOB_RESULTS_DIR"]
    job_name = os.environ["AMZN_BRAKET_JOB_NAME"]
    checkpoint_dir = os.environ["AMZN_BRAKET_CHECKPOINT_DIR"]
    hp_file = os.environ["AMZN_BRAKET_HP_FILE"]
    device_arn = os.environ["AMZN_BRAKET_DEVICE_ARN"]

    with open(f"{output_dir}/job_started.txt", "w") as f:
        f.write("Test QAOA job started!!!!!")

    print(f"In entry point script with sdk version {braket_sdk.__version__}")

    # Read the hyperparameters
    with open(hp_file, "r") as f:
        hyperparams = json.load(f)
    print(hyperparams)
    
    num_nodes = int(hyperparams['num_nodes'])
    num_edges = int(hyperparams['num_edges'])
    p = int(hyperparams['p'])
    seed = int(hyperparams['seed'])
    max_parallel = int(hyperparams['max_parallel'])
    num_iterations = int(hyperparams['num_iterations'])
    interface = hyperparams['interface']
    if 'copy_checkpoints_from_job' in hyperparams:
        copy_checkpoints_from_job = hyperparams['copy_checkpoints_from_job'].split("/", 2)[-1]
    else:
        copy_checkpoints_from_job = None
    
    # Import interface (PennyLane / TensorFlow / PyTorch)
    qaoa_utils.import_interface(interface=interface)
    
    # Try to open input file if it exists, otherwise generate random graph
    try:
        g = nx.read_adjlist(f"{input_dir}/input-graph/input-data.adjlist", nodetype=int)
        print("Read graph from input file")
    except FileNotFoundError:
        g = nx.gnm_random_graph(num_nodes, num_edges, seed=seed)
        print("No input file found, generated random graph")

    # Draw graph to an output file
    positions = nx.spring_layout(g, seed=seed)
    nx.draw(g, with_labels=True, pos=positions, node_size=600)
    plt.savefig(f"{output_dir}/graph.png")

    # Set up the QAOA problem
    cost_h, mixer_h = qml.qaoa.maxcut(g)
    
    def qaoa_layer(gamma, alpha):
        qml.qaoa.cost_layer(gamma, cost_h)
        qml.qaoa.mixer_layer(alpha, mixer_h)
        
    def circuit(params, **kwargs):
        for i in range(num_nodes):
            qml.Hadamard(wires=i)
        qml.layer(qaoa_layer, p, params[0], params[1])
    
    dev = init_pl_device(device_arn, num_nodes, max_parallel)
    
    np.random.seed(seed)
    cost_function = qml.ExpvalCost(circuit, cost_h, dev, optimize=True, interface=interface)
    
    # Load checkpoint if it exists
    if copy_checkpoints_from_job:
        checkpoint_1 = load_job_checkpoint(
            copy_checkpoints_from_job,
            checkpoint_file_suffix="checkpoint-1",
        )
        start_iteration = checkpoint_1['iteration']
        params = qaoa_utils.initialize_params(np.array(checkpoint_1['params']), interface)
        print("Checkpoint loaded")
    else:
        start_iteration = 0
        params = qaoa_utils.initialize_params(0.01 * np.random.uniform(size=[2, p]), interface=interface)
    
    optimizer = qaoa_utils.get_sgd_optimizer(params, interface=interface)
    print("Optimization start")
    
    for iteration in range(start_iteration, num_iterations):    
        t0 = time.time()
    
        # Evaluates the cost, then does a gradient step to new params
        params, cost_before = qaoa_utils.get_cost_and_step(cost_function, params, optimizer, interface=interface)
        # Convert params to a Numpy array so they're easier to handle for us
        np_params = qaoa_utils.convert_params_to_numpy(params, interface=interface)

        t1 = time.time()
    
        if iteration == 0:
            print("Initial cost:", cost_before)
        else:
            print(f"Cost at step {iteration}:", cost_before)

        # Log the current loss as a metric
        log_metric(
            metric_name="Cost",
            value=cost_before,
            timestamp=t1,
            iteration_number=iteration,
        )
            
        # Save the current params and previous cost to a checkpoint
        save_job_checkpoint(
            checkpoint_data={"iteration": iteration+1, "params": np_params.tolist(), "cost_before": cost_before},
            checkpoint_file_suffix="checkpoint-1",
        )
        
        with open(f"{output_dir}/cost_evolution.txt", "a") as f:
            f.write(f"{iteration} {cost_before} \n")
        
        print(f"Completed iteration {iteration + 1}")
        print(f"Time to complete iteration: {t1 - t0} seconds")

    final_cost = float(cost_function(params))
    log_metric(
        metric_name="Cost",
        value=final_cost,
        timestamp=time.time(),
        iteration_number=num_iterations,
    )

    with open(f"{output_dir}/cost_evolution.txt", "a") as f:
        f.write(f"{num_iterations} {final_cost} \n")
    print(f"Cost at step {num_iterations}:", final_cost)
                             
    # We're done with the job, so save the result.
    # This will be returned in job.result()
    save_job_result(
        {
            "params": np_params.tolist(),
            "cost": final_cost
        }
    )
