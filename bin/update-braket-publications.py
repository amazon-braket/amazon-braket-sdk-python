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

"""
Update README.md with a table of recent arXiv preprints that use Amazon Braket.

Searches the arXiv API for papers mentioning Amazon Braket from the past 12 months,
formats them as a markdown table, and updates the README.md file. Uses only the
standard library and requires no API keys or paid services.

Usage:
    python bin/update-braket-publications.py

Run from the repository root. The script takes no input arguments.
"""

import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ARXIV_API_BASE = "http://export.arxiv.org/api/query"
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
USER_AGENT = "AmazonBraketSDK-Publications/1.0"
MAX_RESULTS_PER_REQUEST = 100
TOTAL_MAX_RESULTS = 500
REQUEST_DELAY_SECONDS = 3


def _ns(tag: str, namespace: str = ATOM_NS) -> str:
    return f"{{{namespace}}}{tag}"


def fetch_arxiv_papers() -> list[dict]:
    """Query arXiv API for papers mentioning Amazon Braket from the last 12 months."""
    cutoff_date = datetime.now() - timedelta(days=365)
    search_query = "all:Braket"

    papers: list[dict] = []
    start = 0

    while start < TOTAL_MAX_RESULTS:
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": MAX_RESULTS_PER_REQUEST,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        url = f"{ARXIV_API_BASE}?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": USER_AGENT})

        try:
            with urlopen(request, timeout=30) as response:
                data = response.read()
        except URLError as e:
            sys.exit(f"Network error fetching arXiv: {e}")

        root = ET.fromstring(data)
        entries = root.findall(f".//{_ns('entry')}")

        for entry in entries:
            id_elem = entry.find(_ns("id"))
            if id_elem is None or id_elem.text is None:
                continue
            if "arxiv.org/api/errors" in id_elem.text:
                continue
            arxiv_url = id_elem.text.strip()
            arxiv_id_match = re.search(r"arxiv\.org/abs/(\S+)", arxiv_url)
            if not arxiv_id_match:
                continue
            arxiv_id = re.sub(r"v\d+$", "", arxiv_id_match.group(1))

            published = entry.find(_ns("published"))
            if published is None or published.text is None:
                continue
            try:
                dt = datetime.fromisoformat(
                    published.text.replace("Z", "+00:00").replace("-00:00", "+00:00")
                )
            except ValueError:
                continue

            if dt.date() < cutoff_date.date():
                continue

            title_elem = entry.find(_ns("title"))
            summary_elem = entry.find(_ns("summary"))
            summary = summary_elem.text or "" if summary_elem is not None else ""
            combined_text = f"{title_elem.text or ''} {summary}".lower()
            if "amazon" not in combined_text or "braket" not in combined_text:
                continue

            title_elem = entry.find(_ns("title"))
            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else ""

            authors = []
            for author in entry.findall(_ns("author")):
                name_elem = author.find(_ns("name"))
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            papers.append(
                {
                    "year": str(dt.year),
                    "month": dt.strftime("%B"),
                    "title": title,
                    "authors": ", ".join(authors) if authors else "",
                    "link": f"https://arxiv.org/abs/{arxiv_id}",
                    "arxiv_id": arxiv_id,
                }
            )

        if len(entries) < MAX_RESULTS_PER_REQUEST:
            break
        start += MAX_RESULTS_PER_REQUEST

        if start < TOTAL_MAX_RESULTS:
            time.sleep(REQUEST_DELAY_SECONDS)

    return papers


def build_markdown_table(papers: list[dict]) -> str:
    """Build a markdown table from paper records."""
    if not papers:
        return "## Recent Publications Using Amazon Braket\n\nNo recent publications found."

    lines = [
        "## Recent Publications Using Amazon Braket",
        "",
        "| Year | Month | Title | Authors | Link |",
        "|------|-------|-------|---------|------|",
    ]

    for p in papers:
        title_escaped = p["title"].replace("|", "\\|")
        authors_escaped = p["authors"].replace("|", "\\|")
        lines.append(
            f"| {p['year']} | {p['month']} | {title_escaped} | "
            f"{authors_escaped} | [arXiv:{p['arxiv_id']}]({p['link']}) |"
        )

    return "\n".join(lines)


def update_readme(readme_path: Path, table_content: str) -> None:
    """Insert or replace the publications table in README.md."""
    content = readme_path.read_text(encoding="utf-8")

    marker_start = "<!-- BEGIN_RECENT_PUBLICATIONS -->"
    marker_end = "<!-- END_RECENT_PUBLICATIONS -->"

    if marker_start in content and marker_end in content:
        pattern = re.compile(
            re.escape(marker_start) + r".*?" + re.escape(marker_end),
            re.DOTALL,
        )
        new_block = f"{marker_start}\n{table_content}\n{marker_end}"
        content = pattern.sub(new_block, content)
    else:
        insert_after = "## Sample Notebooks"
        if insert_after in content:
            idx = content.find(insert_after)
            section_end = content.find("\n## ", idx + 1)
            if section_end == -1:
                section_end = len(content)
            insert_pos = section_end
            new_block = f"\n\n{marker_start}\n{table_content}\n{marker_end}\n"
            content = content[:insert_pos] + new_block + content[insert_pos:]
        else:
            content += f"\n\n{marker_start}\n{table_content}\n{marker_end}\n"

    readme_path.write_text(content, encoding="utf-8")


def main() -> None:
    """Fetch Braket papers from arXiv and update README.md."""
    repo_root = Path(__file__).resolve().parent.parent
    readme_path = repo_root / "README.md"

    if not readme_path.exists():
        sys.exit(f"README.md not found at {readme_path}")

    papers = fetch_arxiv_papers()
    if not papers:
        print("No papers found. README may be unchanged.")
        return

    table_content = build_markdown_table(papers)
    update_readme(readme_path, table_content)
    print(f"Updated README.md with {len(papers)} publication(s).")


if __name__ == "__main__":
    main()
