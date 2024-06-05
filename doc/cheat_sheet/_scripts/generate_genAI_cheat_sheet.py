import argparse
import io
import os
import re
import requests
import zipfile


def download_zip_file(version=None):
    if version is None:
        zip_file_url = "https://github.com/amazon-braket/amazon-braket-sdk-python/zipball/jcjaskula-aws/add_cheat_sheet"
    else:
        zip_file_url = f"https://github.com/amazon-braket/amazon-braket-sdk-python/archive/refs/tags/v{version}.zip"

    r = requests.get(zip_file_url)
    return zipfile.ZipFile(io.BytesIO(r.content))


def list_markdown_files(zip_file):
    cs_folder = os.path.join(zip_file.namelist()[0], "doc/cheat_sheet/_includes/en/")
    print(cs_folder)
    excluded_files = ["What-is.md", "Resources.md"]

    zip_files = [
        os.path.join(cs_folder, file.name)
        for file in zipfile.Path(zip_file, at=cs_folder).iterdir()
        if file.name not in excluded_files
    ]
    return zip_files


def concatenate_files(zip_file, files):
    content = {}
    for file in files:
        filename = os.path.split(file)[-1]
        content[filename] = []
        with zip_file.open(file, "r") as f:
            for line in f.readlines():
                if '|' not in line.decode():
                    continue
                result = re.match(
                    r"\|\s*(.*)\s*\|\s*(.*)\s*\|", line.decode()
                )
                if result and len(result.groups()) == 2:
                    content[filename].append(
                        result.groups()
                    )
                else:
                    raise ValueError(f"Invalid line: {line} in {file}")
    return content


def format_and_write(content, destination):
    with open(os.path.join(destination, "genAI_optimized_cheat_sheet.md"), "w") as f:
        f.write("# Braket CheatSheet\n\n")
        for filename, file_content in content.items():
            f.write(f"**{filename[:-3]}**\n\n")
            for description, command in file_content:
                if result := re.match(
                    r"(.*)\<!--\s*LLM:\s(.*)\s*-->(.*)", description
                ):
                    description = "".join(result.groups())
                f.write(f"***{description.strip()}:***\n\n")

                if result := re.match(
                    r"(.*)\<!--\s*LLM:\s(.*)\s*-->(.*)", command
                ):
                    command = "".join(result.groups())               
                if "<br>" in command:
                    command = command.strip().replace('`', '')
                    f.write("```\n{}\n```\n\n".format(command.replace('<br>', '\n')))
                else:
                    f.write(f"{command}\n\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--destination", type=str)
    parser.add_argument("-v", "--version", type=str)

    args = parser.parse_args()
    version = args.version if args.version else None
    destination = args.destination if args.destination else "."

    zip_file = download_zip_file(version)
    markdown_file_names = list_markdown_files(zip_file)
    content = concatenate_files(zip_file, markdown_file_names)
    format_and_write(content, destination)
