# Import PennyLane / TF / Torch globally based on input.
# This is necessary so we don't try to e.g. import tensorflow in the Torch container
# Note "global" refers to this module only
def import_interface(interface='autograd'):
    if interface == 'autograd':
        global qml
        qml = __import__('pennylane', globals(), locals()) 
        # Equiv to: import pennylane as qml
    elif interface == 'tf':
        global tf
        tf = __import__('tensorflow', globals(), locals()) 
        # Equiv to: import tensorflow as tf
    elif interface == 'torch':
        global torch
        torch = __import__('torch', globals(), locals()) 
        # Equiv to: import torch

# Initialize params to the appropriate format for the autodiff library.
def initialize_params(np_array, interface='autograd'):
    if interface == 'autograd':
        return np_array
    elif interface == 'tf':
        return tf.Variable(np_array, dtype=tf.float64)
    elif interface == 'torch':
        return torch.tensor(np_array, requires_grad=True)
        
# Returns the gradient descent optimizer to use, based on the ML framework.
def get_sgd_optimizer(params, interface='autograd', stepsize=0.1):
    if interface == 'autograd':
        return qml.GradientDescentOptimizer(stepsize=stepsize)
    elif interface == 'tf':
        return tf.keras.optimizers.SGD(learning_rate=stepsize)
    elif interface == 'torch':
        return torch.optim.SGD([params], lr=stepsize)
    
# Convert params to base Numpy arrays.
def convert_params_to_numpy(params, interface='autograd'):
    if interface == 'autograd':
        return params.numpy()
    elif interface == 'tf':
        return params.numpy()
    elif interface == 'torch':
        return params.detach().numpy()

# Evaluate the cost function, then take a step.
def get_cost_and_step(cost_function, params, optimizer, interface='autograd'):
    if interface == 'autograd':
        params, cost_before = optimizer.step_and_cost(cost_function, params)
    elif interface == 'tf':
        def tf_cost():
            global _cached_cost_before
            _cached_cost_before = cost_function(params)
            return _cached_cost_before
        optimizer.minimize(tf_cost, params)
        cost_before = _cached_cost_before
        
#         Alternative:
#         with tf.GradientTape() as tape:
#             cost_before = cost_function(params)

#         gradients = tape.gradient(cost_before, params)
#         optimizer.apply_gradients(((gradients, params),))
    elif interface == 'torch':
        optimizer.zero_grad()
        cost_before = cost_function(params)
        cost_before.backward()
        optimizer.step()
    else:
        pass

    return params, float(cost_before)