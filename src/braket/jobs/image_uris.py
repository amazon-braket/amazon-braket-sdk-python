# TODO: This function is defined based on the defintiion in the design doc,
# and is subject to change.


def retrieve(framework="pytorch", framework_version="1.8", py_version="3.7"):
    """Retrieves the ECR URI for the Docker image matching the given arguments.

    Args:
        framework (str): The name of the framework or algorithm.
        framework_version (str): The framework or algorithm version. This is required if there is
            more than one supported version for the given framework or algorithm.
        py_version (str, optional): [description]. The Python version. This is required if there is
            more than one supported Python version for the given framework version.

    Returns:
        str: the ECR URI for the corresponding SageMaker Docker image.

    Raises:
        ValueError: If the combination of arguments specified is not supported.
    """
    pass
