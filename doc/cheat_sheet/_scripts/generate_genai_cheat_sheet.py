"""Generate a Markdown AI cheat sheet from the rendered cheat sheet blocks.

This script reads the English cheat sheet section order from
doc/cheat_sheet/_data/blocks.yml and concatenates the corresponding Markdown
files from doc/cheat_sheet/_includes/en into doc/genai_cheat_sheet.md.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CHEAT_SHEET_DIR = ROOT / "cheat_sheet"
BLOCKS_FILE = CHEAT_SHEET_DIR / "_data" / "blocks.yml"
EN_INCLUDES_DIR = CHEAT_SHEET_DIR / "_includes" / "en"
DEFAULT_OUTPUT = ROOT / "genai_cheat_sheet.md"


def strip_html_comments(text: str) -> str:
    """Remove inline HTML comments from Markdown content."""
    return re.sub(r"<!--.*?-->", "", text)


def generate(output_path: Path) -> None:
    """Generate the AI-readable cheat sheet Markdown."""
    with BLOCKS_FILE.open("r", encoding="utf-8") as file:
        blocks = yaml.safe_load(file)

    sections: list[str] = ["# Amazon Braket SDK Cheat Sheet", ""]

    for block in blocks:
        title = block["title"]
        filename = block["file"]
        section_path = EN_INCLUDES_DIR / filename

        if not section_path.exists():
            raise FileNotFoundError(f"Missing section file: {section_path}")

        content = section_path.read_text(encoding="utf-8").strip()
        content = strip_html_comments(content)

        sections.append(f"## {title}")
        sections.append("")
        sections.append(content)
        sections.append("")

    output_path.write_text("\n".join(sections).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate doc/genai_cheat_sheet.md from the English cheat sheet blocks."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output Markdown file path.",
    )
    args = parser.parse_args()

    generate(args.output)


if __name__ == "__main__":
    main()
