from __future__ import annotations

import argparse
import re
from pathlib import Path


COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _read_value(line: str) -> str:
    return line.split(":", 1)[1].strip().strip("\"'")


def _read_blocks(blocks_file: Path) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for line in blocks_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- file:"):
            if current:
                blocks.append(current)
            current = {"file": _read_value(stripped)}
            continue
        if current is not None and stripped.startswith("title:"):
            current["title"] = _read_value(stripped)

    if current:
        blocks.append(current)
    return blocks


def _section_text(source: Path, lang: str, filename: str) -> str:
    section_path = source / "_includes" / lang / filename
    text = section_path.read_text(encoding="utf-8")
    return COMMENT_RE.sub("", text).strip()


def generate_markdown(source: Path, lang: str) -> str:
    blocks = _read_blocks(source / "_data" / "blocks.yml")
    lines = [
        "# Amazon Braket SDK Cheat Sheet",
        "",
        f"Generated from `{source.as_posix()}/_data/blocks.yml` and `_includes/{lang}/`.",
        "",
    ]

    for block in blocks:
        lines.extend([
            f"## {block['title']}",
            "",
            _section_text(source, lang, block["file"]),
            "",
        ])

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Markdown cheat sheet companion.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("doc/cheat_sheet"),
        help="Jekyll cheat sheet source directory.",
    )
    parser.add_argument("--lang", default="en", help="Language include directory to use.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("doc/genai_cheat_sheet.md"),
        help="Output Markdown file.",
    )
    args = parser.parse_args()

    markdown = generate_markdown(args.source, args.lang)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
