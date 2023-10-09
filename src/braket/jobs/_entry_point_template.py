run_entry_point = """
import cloudpickle
# from braket.jobs import save_job_result
from braket.jobs_data import PersistedJobDataFormat

# load and run serialized entry point function
recovered = cloudpickle.loads({serialized})
def {function_name}():
    result = recovered()
    if result is not None:
        save_job_result(result, data_format=PersistedJobDataFormat.PICKLED_V4)
    return result
"""

symlink_input_data = '''
from pathlib import Path

# map of data sources to lists of matched local files
prefix_matches = {prefix_matches}

def make_link(input_link_path, input_data_path):
    """ Create symlink from input_link_path to input_data_path. """
    input_link_path.parent.mkdir(parents=True, exist_ok=True)
    input_link_path.symlink_to(input_data_path)
    print(input_link_path, '->', input_data_path)

for channel, data in {input_data_items}:

    if channel in {prefix_channels}:
        # link all matched files
        for input_link_name in prefix_matches[channel]:
            input_link_path = Path(input_link_name)
            input_data_path = Path(get_input_data_dir(channel)) / input_link_path.name
            make_link(input_link_path, input_data_path)

    else:
        input_link_path = Path(data)
        if channel in {directory_channels}:
            # link directory source directly to input channel directory
            input_data_path = Path(get_input_data_dir(channel))
        else:
            # link file source to file within input channel directory
            input_data_path = Path(get_input_data_dir(channel), Path(data).name)
        make_link(input_link_path, input_data_path)
'''
