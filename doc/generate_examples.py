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
import os
import re
import urllib.request
from typing import Dict, List, Any

# Map directory names to RST filenames and Headers
CATEGORY_MAPPING = {
    "getting_started": {
        "filename": "examples-getting-started.rst",
        "header": "Getting started",
        "description": "Get started on Amazon Braket with some introductory examples."
    },
    "braket_features": {
        "filename": "examples-braket-features.rst",
        "header": "Amazon Braket features",
        "description": "Learn more about the individual features of Amazon Braket."
    },
    "advanced_circuits_algorithms": {
        "filename": "examples-adv-circuits-algorithms.rst",
        "header": "Advanced circuits and algorithms",
        "description": "Learn more about working with advanced circuits and algorithms."
    },
    "hybrid_quantum_algorithms": {
        "filename": "examples-hybrid-quantum.rst",
        "header": "Hybrid quantum algorithms",
        "description": "Learn more about hybrid quantum algorithms."
    },
    "pennylane": {
        "filename": "examples-ml-pennylane.rst",
        "header": "Quantum machine learning and optimization with PennyLane",
        "description": "Learn more about how to combine PennyLane with Amazon Braket."
    },
    "hybrid_jobs": {
        "filename": "examples-hybrid-jobs.rst",
        "header": "Amazon Braket Hybrid Jobs",
        "description": "Learn more about hybrid jobs on Amazon Braket."
    }
}

ENTRIES_URL = "https://raw.githubusercontent.com/amazon-braket/amazon-braket-examples/main/docs/ENTRIES.json"
BASE_REPO_URL = "https://github.com/amazon-braket/amazon-braket-examples/blob/main"

def fetch_entries() -> Dict[str, Any]:
    with urllib.request.urlopen(ENTRIES_URL) as response:
        return json.loads(response.read().decode())

def sanitize_rst_content(text: str) -> str:
    """
    Sanitize content from JSON to be RST-friendly.
    Converts Markdown-style formatting to RST.
    """
    if not text:
        return ""
        
    # Convert _italic_ to *italic*
    # Matches _ followed by non-underscore characters followed by _
    # This prevents matching snake_case_variable unless it is _variable_
    text = re.sub(r'_([^_]+)_', r'*\1*', text)
    
    # Convert `code` to ``code``
    # Markdown uses single backtick for code, RST uses double backticks.
    text = re.sub(r'`([^`]+)`', r'``\1``', text)
    
    # Convert [text](url) to `text <url>`_
    def replace_link(match):
        text = match.group(1)
        url = match.group(2)
        if not url.startswith("http"):
            url = f"{BASE_REPO_URL}/{url}"
        return f"`{text} <{url}>`_"
    
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)
    
    return text

def generate_rst(entries: Dict[str, Any], output_dir: str):
    # Group entries by category
    grouped_entries: Dict[str, List[tuple]] = {key: [] for key in CATEGORY_MAPPING}
    
    for title, entry in entries.items():
        location = entry.get("location", "")
        if not location.startswith("examples/"):
            continue
            
        # Extract the second part of the path, e.g. "getting_started" from "examples/getting_started/..."
        parts = location.split("/")
        if len(parts) < 2:
            continue
            
        category_slug = parts[1]
        
        # Check against CATEGORY_MAPPING keys
        if category_slug in CATEGORY_MAPPING:
           grouped_entries[category_slug].append((title, entry))

    # Generate files
    for category_key, items in grouped_entries.items():
        mapping = CATEGORY_MAPPING[category_key]
        filename = mapping["filename"]
        header = mapping["header"]
        description = mapping["description"]
        
        # Sort items by location to preserve order (assuming numbering in folders)
        items.sort(key=lambda x: x[1].get("location", ""))
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w") as f:
            # Write Header
            f.write("#" * len(header) + "\n")
            f.write(header + "\n")
            f.write("#" * len(header) + "\n\n")
            f.write(description + "\n\n")
            
            f.write(".. toctree::\n")
            f.write("    :maxdepth: 2\n\n")
            
            for title, entry in items:
                location = entry["location"]
                content = entry.get("content", "").strip()
                # Sanitize content
                content = sanitize_rst_content(content)
                
                # Construct link
                link = f"{BASE_REPO_URL}/{location}"
                
                # Format:
                # **********************************************
                # `Title <Link>`_
                # **********************************************
                #
                # Content
                
                link_text = f"`{title} <{link}>`_"
                underline = "*" * len(link_text)
                
                f.write(underline + "\n")
                f.write(link_text + "\n")
                f.write(underline + "\n\n")
                
                if content:
                    f.write(content + "\n\n")

if __name__ == "__main__":
    entries = fetch_entries()
    output_dir = os.path.dirname(os.path.abspath(__file__))
    generate_rst(entries, output_dir)
