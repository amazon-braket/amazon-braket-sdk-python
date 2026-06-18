#!/usr/bin/env python3
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

"""Generate the GenAI-optimized cheat sheet.

The browsable cheat sheet is an HTML site, but a single flat Markdown file is
much easier for an LLM agent to ingest in one shot. This script flattens the
ordered English sections (``_data/blocks.yml`` + ``_includes/en/*.md``) into
``doc/genai_cheat_sheet.md``.

Unlike the original prototype, it reads the local source tree directly -- no
network download -- so it is safe to run in CI. ``<!-- LLM: ... -->`` hints that
are hidden in the HTML site are folded into the text here, since they exist to
help machine readers.

Usage::

    python doc/cheat_sheet/_scripts/generate_genai_cheat_sheet.py          # write
    python doc/cheat_sheet/_scripts/generate_genai_cheat_sheet.py --check  # verify in sync
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CHEAT_SHEET_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = CHEAT_SHEET_DIR.parents[1]
OUTPUT = REPO_ROOT / "doc" / "genai_cheat_sheet.md"

# Prose sections without API snippets are not useful to a coding agent.
EXCLUDED_FILES = {"What-is.md", "Resources.md"}

_BLOCK_FILE = re.compile(r"-\s*file:\s*(\S+)")
_BLOCK_TITLE = re.compile(r"\s+title:\s*(.+)")
_LLM_HINT = re.compile(r"<!--\s*LLM:\s*(.*?)\s*-->")


def _read_blocks(blocks_path: Path) -> list[dict[str, str]]:
    """Parse ``blocks.yml`` (file/title order) without a YAML dependency."""
    blocks: list[dict[str, str]] = []
    for line in blocks_path.read_text(encoding="utf-8").splitlines():
        if file_match := _BLOCK_FILE.match(line):
            blocks.append({"file": file_match.group(1).strip()})
        elif (title_match := _BLOCK_TITLE.match(line)) and blocks and "title" not in blocks[-1]:
            blocks[-1]["title"] = title_match.group(1).strip()
    return blocks


def _fold_hints(text: str) -> str:
    """Drop the ``<!-- LLM: ... -->`` markers but keep their hint text."""
    return _LLM_HINT.sub(lambda match: match.group(1), text).strip()


def _rows(section: Path) -> list[tuple[str, str]]:
    """Return ``(description, command)`` pairs for each table row of a section."""
    rows: list[tuple[str, str]] = []
    for line in section.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = line.strip().strip("|").split("|", 1)
        if len(cells) != 2:
            continue
        description, command = cells[0].strip(), cells[1].strip()
        if set(description) <= {"-", ":"} and set(command) <= {"-", ":"}:
            continue  # markdown header separator row
        rows.append((_fold_hints(description), command))
    return rows


def render(source_dir: Path = CHEAT_SHEET_DIR) -> str:
    """Render the flat GenAI cheat sheet as a string."""
    blocks = _read_blocks(source_dir / "_data" / "blocks.yml")
    lines = ["# Braket CheatSheet", ""]
    for block in blocks:
        filename = block["file"]
        if filename in EXCLUDED_FILES:
            continue
        rows = _rows(source_dir / "_includes" / "en" / filename)
        if not rows:
            continue
        lines.append(f"**{block.get('title', filename[:-3])}**")
        lines.append("")
        for description, command in rows:
            lines.append(f"***{description}:***")
            lines.append("")
            command = _fold_hints(command)
            if "<br>" in command:
                code = command.replace("<br>", "\n").replace("`", "").strip()
                lines.extend(["```", code, "```"])
            else:
                lines.append(command)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed file matches the source instead of writing it",
    )
    args = parser.parse_args()

    rendered = render()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            print(
                f"{OUTPUT.relative_to(REPO_ROOT)} is out of date. "
                "Run: python doc/cheat_sheet/_scripts/generate_genai_cheat_sheet.py"
            )
            return 1
        print(f"{OUTPUT.relative_to(REPO_ROOT)} is in sync.")
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)} ({rendered.count(chr(10))} lines).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
