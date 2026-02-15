# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import json
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import TypeAlias

# --- Type Aliases ---
# Represents the parsed JSON: mapping entry names to their metadata dictionaries
RawEntries: TypeAlias = dict[str, dict[str, str]]

# Represents a single processed example containing 'name', 'url', and 'description'
ProcessedEntry: TypeAlias = dict[str, str]

# Maps a main topic string to a list of its processed entries
SubTopicMap: TypeAlias = dict[str, list[ProcessedEntry]]

SCRIPT_DIR = Path(__file__).parent
REPO_BASE_URL = "https://github.com/amazon-braket/amazon-braket-examples/tree/main/"


def get_entries_json(entries_url: str) -> RawEntries:
    """Fetch and parse JSON entries from the given URL.

    Args:
        entries_url (str): The URL pointing to the JSON file to be fetched.

    Returns:
        RawEntries: A dictionary containing the parsed JSON data.

    Raises:
        urllib.error.URLError: If there is a network issue or the URL cannot be reached.
        json.JSONDecodeError: If the downloaded content is not valid JSON.
    """
    with urllib.request.urlopen(entries_url) as response:
        return json.loads(response.read().decode("utf-8"))


def update_toctree_file(file_path: Path, new_content: list[str]) -> None:
    """Find the toctree directive in a file, truncate the file there, and append new content.

    Args:
        file_path (Path): The pathlib.Path object pointing to the target .rst file.
        new_content (list[str]): A list of string lines to append after the toctree.

    Returns:
        None

    Raises:
        OSError: If there is an issue reading from or writing to the file.
    """
    if not file_path.exists():
        return

    with file_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    insert_at = 0
    for i, line in enumerate(lines):
        if line.strip().startswith(".. toctree::"):
            insert_at = (
                i + 3
            )  # Keeps the toctree and immediate config (like :maxdepth: 1)
            break

    with file_path.open("w", encoding="utf-8") as f:
        f.writelines(lines[:insert_at])
        f.writelines(new_content)


def process_entries(entries_json: RawEntries) -> tuple[list[str], SubTopicMap]:
    """Extract topics and deduplicate sub-topics from the entries JSON.

    Args:
        entries_json (RawEntries): The raw dictionary of entries parsed from JSON.

    Returns:
        tuple[list[str], SubTopicMap]: A tuple containing:
            - A list of unique topic strings.
            - A dictionary mapping topic strings to lists of sub-topic dictionaries.
    """
    topics: list[str] = []
    sub_topics: SubTopicMap = defaultdict(list)
    seen_sub_topics: dict[str, set[str]] = defaultdict(set)

    for name, entry in entries_json.items():
        location = entry.get("location", "")
        parts = location.split("/")

        # Validate that the path structure is at least "examples/topic/subtopic"
        if len(parts) > 2 and parts[0] == "examples":
            topic = parts[1]
            if topic not in topics:
                topics.append(topic)

            sub_topic = parts[2]

            # Deduplicate by tracking the sub_topic string
            if sub_topic not in seen_sub_topics[topic]:
                seen_sub_topics[topic].add(sub_topic)
                sub_topics[topic].append(
                    {
                        "name": name,
                        "url": f"{REPO_BASE_URL}{location}",
                        "description": entry.get("content", ""),
                    }
                )

    return topics, sub_topics


def main() -> None:
    """Execute the main script logic to fetch entries and update Sphinx documentation files.

    Returns:
        None

    Raises:
        Exception: If there is an unexpected error during execution, URL fetching, or file I/O.
    """
    entries_url = "https://raw.githubusercontent.com/amazon-braket/amazon-braket-examples/refs/heads/main/docs/ENTRIES.json"
    entries_json = get_entries_json(entries_url)

    topics, sub_topics = process_entries(entries_json)

    # Update the main examples list
    main_examples_file = SCRIPT_DIR / "examples.rst"
    main_toctree_lines = [
        f"   examples-{topic.replace('_', '-')}.rst\n" for topic in topics
    ]
    update_toctree_file(main_examples_file, main_toctree_lines)

    # Generate or update individual topic files
    for topic, entries in sub_topics.items():
        example_file = SCRIPT_DIR / f"examples-{topic.replace('_', '-')}.rst"

        # Create base file layout if it doesn't exist
        if not example_file.exists():
            title = f"{topic.capitalize()} Examples"
            border = "#" * len(title)
            with example_file.open("w", encoding="utf-8") as f:
                f.write(f"{border}\n{title}\n{border}\n\n")
                f.write(".. toctree::\n\t:maxdepth: 1\n\n")

        # Compile link lines
        topic_lines = []
        for entry in entries:
            link_text = f"`{entry['name']} <{entry['url']}>`_"
            link_border = "*" * len(link_text)

            topic_lines.extend(
                [
                    f"{link_border}\n",
                    f"{link_text}\n",
                    f"{link_border}\n\n",
                    f"{entry['description']}\n\n",
                ]
            )

        update_toctree_file(example_file, topic_lines)


if __name__ == "__main__":
    main()
