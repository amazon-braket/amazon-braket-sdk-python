"""
Queries the arXiv API for papers mentioning "Amazon Braket" from the past
12 months and updates README.md with a markdown table of those publications.

Uses only the Python standard library (no third-party dependencies).
The script is idempotent — safe to run repeatedly.

Usage: python bin/update_braket_publications.py
"""

import datetime
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
README_PATH = "README.md"
BEGIN_MARKER = "<!-- BEGIN_RECENT_PUBLICATIONS -->"
END_MARKER = "<!-- END_RECENT_PUBLICATIONS -->"
INSERT_BEFORE = "## Braket Python SDK API Reference Documentation"
MAX_AUTHORS = 3


def build_query_url():
    """Construct the arXiv API query URL for the past 12 months."""
    today = datetime.date.today()
    start = today - datetime.timedelta(days=365)
    date_range = f"[{start.strftime('%Y%m%d')}0000 TO {today.strftime('%Y%m%d')}2359]"
    search_query = f'all:"Amazon Braket" AND submittedDate:{date_range}'
    params = urllib.parse.urlencode(
        {
            "search_query": search_query,
            "start": 0,
            "max_results": 200,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    return f"{ARXIV_API_URL}?{params}"


def parse_entry(entry):
    """Parse a single Atom XML entry into a paper dict, or None if malformed."""
    id_el = entry.find(f"{ATOM_NS}id")
    title_el = entry.find(f"{ATOM_NS}title")
    published_el = entry.find(f"{ATOM_NS}published")
    author_els = entry.findall(f"{ATOM_NS}author")

    if id_el is None or title_el is None or published_el is None or not author_els:
        return None

    # arXiv ID: strip URL prefix and version suffix (e.g. "2601.14036v1" -> "2601.14036")
    raw_id = id_el.text.strip()
    arxiv_id = raw_id.rsplit("/", 1)[-1]
    arxiv_id = re.sub(r"v\d+$", "", arxiv_id)

    title = " ".join(title_el.text.split())

    authors = []
    for author_el in author_els:
        name_el = author_el.find(f"{ATOM_NS}name")
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    if not authors:
        return None

    if len(authors) > MAX_AUTHORS:
        author_str = ", ".join(authors[:MAX_AUTHORS]) + ", et al."
    else:
        author_str = ", ".join(authors)

    published = published_el.text.strip()
    try:
        pub_date = datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))
    except ValueError:
        return None

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": author_str,
        "year": pub_date.year,
        "month": pub_date.month,
    }


def fetch_papers():
    """Fetch and parse arXiv papers mentioning Amazon Braket."""
    url = build_query_url()
    print(f"Querying arXiv API: {url}")

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"Error fetching arXiv data: {e}", file=sys.stderr)
        sys.exit(1)

    root = ET.fromstring(data)
    papers = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        paper = parse_entry(entry)
        if paper is not None:
            papers.append(paper)

    return papers


def format_publications_table(papers):
    """Build the markdown section including sentinel markers."""
    lines = [
        BEGIN_MARKER,
        "",
        "## Recent Publications Using Amazon Braket",
        "",
        "| Year | Month | Title | Authors | Link |",
        "|------|-------|-------|---------|------|",
    ]
    for p in papers:
        link = f"[arXiv:{p['arxiv_id']}](https://arxiv.org/abs/{p['arxiv_id']})"
        lines.append(f"| {p['year']} | {p['month']} | {p['title']} | {p['authors']} | {link} |")
    lines.append("")
    lines.append("*To update this table, run `python bin/update_braket_publications.py` from the repository root.*")
    lines.append("")
    lines.append(END_MARKER)
    return "\n".join(lines)


def update_readme(table_section):
    """Insert or replace the publications table in README.md (idempotent)."""
    try:
        with open(README_PATH, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {README_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    marker_pattern = re.compile(
        rf"{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL,
    )

    if marker_pattern.search(content):
        new_content = marker_pattern.sub(table_section, content)
        print("Replaced existing publications section in README.md.")
    elif INSERT_BEFORE in content:
        new_content = content.replace(
            INSERT_BEFORE,
            table_section + "\n\n" + INSERT_BEFORE,
        )
        print("Inserted new publications section into README.md.")
    else:
        print(
            f'Error: Could not find markers or "{INSERT_BEFORE}" heading in {README_PATH}.',
            file=sys.stderr,
        )
        sys.exit(1)

    with open(README_PATH, "w") as f:
        f.write(new_content)


def main():
    papers = fetch_papers()
    print(f"Found {len(papers)} paper(s) from the past 12 months.")

    if not papers:
        print("No papers found. README.md was not modified.")
        return

    table_section = format_publications_table(papers)
    update_readme(table_section)


if __name__ == "__main__":
    main()
