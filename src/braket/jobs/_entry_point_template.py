run_entry_point = """
import cloudpickle
import os
from braket.jobs import get_results_dir, save_job_result
from braket.jobs_data import PersistedJobDataFormat


# load and run serialized entry point function
recovered = cloudpickle.loads({serialized})
def {function_name}():
    try:
        # set working directory to results dir
        os.chdir(get_results_dir())

        # create symlinks to input data
        links = link_input()

        result = recovered()
    finally:
        clean_links(links)
    if result is not None:
        save_job_result(result, data_format=PersistedJobDataFormat.PICKLED_V4)
    return result
"""

symlink_input_data = '''
from pathlib import Path
from braket.jobs import get_input_data_dir


def make_link(input_link_path, input_data_path, links):
    """ Create symlink from input_link_path to input_data_path. """
    input_link_path.parent.mkdir(parents=True, exist_ok=True)
    input_link_path.symlink_to(input_data_path)
    print(input_link_path, '->', input_data_path)
    links[input_link_path] = input_data_path


def link_input():
    links = {{}}
    dirs = set()
    # map of data sources to lists of matched local files
    prefix_matches = {prefix_matches}

    for channel, data in {input_data_items}:

        if channel in {prefix_channels}:
            # link all matched files
            for input_link_name in prefix_matches[channel]:
                input_link_path = Path(input_link_name)
                input_data_path = Path(get_input_data_dir(channel)) / input_link_path.name
                make_link(input_link_path, input_data_path, links)

        else:
            input_link_path = Path(data)
            if channel in {directory_channels}:
                # link directory source directly to input channel directory
                input_data_path = Path(get_input_data_dir(channel))
            else:
                # link file source to file within input channel directory
                input_data_path = Path(get_input_data_dir(channel), Path(data).name)
            make_link(input_link_path, input_data_path, links)

    return links


def clean_links(links):
    for link, target in links.items():
        if link.is_symlink and link.readlink() == target:
            link.unlink()

        if link.is_relative_to(Path()):
            for dir in link.parents[:-1]:
                try:
                    dir.rmdir()
                except:
                    # directory not empty
                    pass
'''
