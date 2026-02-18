#!/usr/bin/env python3
"""
Update README.md with recent arXiv preprints that mention Amazon Braket.

Purpose:
    This script queries the arXiv API for papers from the past 12 months that
    mention "Amazon Braket" anywhere in the metadata (title, abstract, or comments),
    and updates a markdown table in README.md.

Usage:
    python bin/update_braket_papers.py

Requirements:
    - Existing project dependencies: requests, feedparser
    - README.md should contain markers:
        <!-- PAPER_START -->
        <!-- PAPER_END -->
      If markers are not present, the section will be appended automatically.

Behavior:
    - Searches arXiv
    - Filters papers to the past 12 months
    - Includes papers mentioning "Braket" anywhere in title, abstract, or comments
    - Outputs a markdown table ordered as:
        Year | Month | Title | Authors | Link
    - Link text is formatted as: arXiv:XXXX.XXXXX
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import feedparser

ARXIV_API = "http://export.arxiv.org/api/query"
QUERY = 'all:"Amazon Braket"'
MAX_RESULTS = 100

SCRIPT_DIR = Path(__file__).resolve().parent
README_PATH = SCRIPT_DIR.parent / "README.md"

START_MARKER = "<!-- PAPER_START -->"
END_MARKER = "<!-- PAPER_END -->"


def extract_arxiv_id(entry):
    """Filtering the arXiv identifier (without version suffix)."""
    entry_id = getattr(entry, "id", "") or getattr(entry, "link", "")

    if "/abs/" in entry_id:
        arxiv_part = entry_id.split("/abs/")[-1]
        return arxiv_part.split("v")[0]

    link = getattr(entry, "link", "")
    if "/abs/" in link:
        arxiv_part = link.split("/abs/")[-1]
        return arxiv_part.split("v")[0]

    return ""


def extract_canonical_link(entry):
    """Extract the canonical arXiv abstract link (for citation)."""
    # Prefer explicit abs link if present in links
    for l in getattr(entry, "links", []):
        href = getattr(l, "href", "")
        if "arxiv.org/abs/" in href:
            return href

    # Fallback to entry.link (usually already the abs page)
    return getattr(entry, "link", "")


def fetch_papers():
    """Fetch and filter arXiv papers with Amazon Braket in the last 12 months."""
    params = {
        "search_query": QUERY,
        "start": 0,
        "max_results": MAX_RESULTS,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:
        response = requests.get(ARXIV_API, params=params, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error: Failed to fetch data from arXiv API: {e}", file=sys.stderr)
        return []

    feed = feedparser.parse(response.text)

    if not getattr(feed, "entries", None):
        return []

    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    papers = []

    for entry in feed.entries:
        try:
            title = entry.title.replace("\n", " ").strip()
        except AttributeError:
            continue

        summary = getattr(entry, "summary", "") or ""
        comments = getattr(entry, "arxiv_comment", "") or ""

        # "Anywhere" mention requirement: title + abstract + comments
        text_blob = f"{title} {summary} {comments}".lower()
        if "braket" not in text_blob:
            continue

        # Parse publication date (arXiv uses UTC with Z suffix)
        try:
            published = datetime.strptime(
                entry.published, "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
        except (AttributeError, ValueError):
            continue

        # Filter to past 12 months
        if published < one_year_ago:
            continue

        # Authors
        try:
            authors = ", ".join(author.name for author in entry.authors)
        except AttributeError:
            authors = "Unknown"

        year = published.strftime("%Y")
        month = published.strftime("%m")

        link = extract_canonical_link(entry)
        arxiv_id = extract_arxiv_id(entry)

        # Sanitize table-breaking characters
        title = title.replace("|", " ")
        authors = authors.replace("|", " ")

        papers.append(
            {
                "year": year,
                "month": month,
                "title": title,
                "authors": authors,
                "link": link,
                "arxiv_id": arxiv_id,
                "published": published,
            }
        )

    # Sort newest first by full datetime
    papers.sort(key=lambda x: x["published"], reverse=True)
    return papers


def generate_table(papers):
    """Generate markdown table: Year | Month | Title | Authors | Link."""
    header = [
        "| Year | Month | Title | Authors | Link |",
        "|------|-------|-------|---------|------|",
    ]

    if not papers:
        return "_No Amazon Braket papers found on arXiv in the past 12 months._"

    rows = []
    for p in papers:
        if p["arxiv_id"]:
            link_text = f"arXiv:{p['arxiv_id']}"
        else:
            link_text = "arXiv"

        link_md = f"[{link_text}]({p['link']})"
        row = (
            f"| {p['year']} | {p['month']} | {p['title']} | "
            f"{p['authors']} | {link_md} |"
        )
        rows.append(row)

    return "\n".join(header + rows)


def update_readme(table_md):
    """Insert or update the Braket papers section in README.md."""
    if not README_PATH.exists():
        print("Error: README.md not found.", file=sys.stderr)
        return False

    try:
        content = README_PATH.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error: Failed to read README.md: {e}", file=sys.stderr)
        return False

    new_block = f"{START_MARKER}\n{table_md}\n{END_MARKER}"

    if START_MARKER in content and END_MARKER in content:
        try:
            before = content.split(START_MARKER)[0]
            after = content.split(END_MARKER)[1]
            updated_content = before + new_block + after
        except IndexError:
            print("Error: Malformed markers in README.md.", file=sys.stderr)
            return False
    else:
        section_header = (
            "\n\n## Research Using Amazon Braket\n\n"
        )
        updated_content = content + section_header + new_block

    try:
        README_PATH.write_text(updated_content, encoding="utf-8")
    except Exception as e:
        print(f"Error: Failed to write README.md: {e}", file=sys.stderr)
        return False

    return True


def main():
    """Main entry point for updating the README with relevant papers."""
    print("Querying arXiv for Amazon Braket papers from the past 12 months")

    papers = fetch_papers()

    if not papers:
        print("Warning: No relevant papers found.")

    table_md = generate_table(papers)

    success = update_readme(table_md)
    if not success:
        sys.exit(1)

    print(f"README.md successfully updated with {len(papers)} papers.")


if __name__ == "__main__":
    main()