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
Update PUBLICATIONS.md with tables of recent arXiv preprints that use or mention Amazon Braket.

Searches the arXiv API for papers mentioning Amazon Braket from the past 12 months,
formats them as markdown tables, and updates the PUBLICATIONS.md file. Uses only the
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
USER_AGENT = "AmazonBraketSDK-Publications/1.0"
MAX_RESULTS_PER_REQUEST = 100
TOTAL_MAX_RESULTS = 500
REQUEST_DELAY_SECONDS = 3

POSITIVE_STRONG_PATTERNS = [
    r"\b(using|via|through) Amazon Braket\b",
    r"\bimplemented .* on Amazon Braket\b",
    r"\bexecuted .* on Amazon Braket\b",
    r"\brun .* on Amazon Braket\b",
    r"\bperformed .* on Amazon Braket\b",
    r"\bexperiments? .* (on|using) Amazon Braket\b",
    r"\bbenchmarked .* on Amazon Braket\b",
    r"\bevaluated .* on Amazon Braket\b",
    r"\bsubmitted .* (to|via|through) Amazon Braket\b",
    r"\baccessed .* hardware .* (via|through|using) Amazon Braket\b",
    r"\bAmazon Braket SDK\b",
    r"\bBraket backend\b",
    r"\bBraket QPU\b",
    r"\bBraket simulator\b",
    r"\bwe (use|used|utilize|utilized) Amazon Braket\b"
]

NEGATIVE_STRONG_PATTERNS = [
    r"\bcompare(d)? .* (with|to) Amazon Braket\b",
    r"\bsurvey (of|about) Amazon Braket\b",
    r"\boverview (of|about) Amazon Braket\b",
    r"\breview (of|about) Amazon Braket\b",
    r"\bplatforms? such as Amazon Braket\b",
    r"\bcloud services? (like|including) Amazon Braket\b",
    r"\bexample (of|such as) Amazon Braket\b",
    r"\bfuture work .* Amazon Braket\b",
    r"\bcompatible with Amazon Braket\b",
    r"\bintegration with Amazon Braket\b",
    r"\bsupport for Amazon Braket\b"
]


def score_text(text: str) -> int:
    """Score text based on positive and negative patterns indicating real usage."""
    score = 0

    for pattern in POSITIVE_STRONG_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            score += 3

    for pattern in NEGATIVE_STRONG_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            score -= 3

    return score


def classify(score: int) -> str:
    """Classify paper based on score."""
    if score >= 3:
        return "likely_real_usage"
    if score > 0:
        return "ambiguous_manual_review"
    return "mention_only"


def _ns(tag: str, namespace: str = ATOM_NS) -> str:
    return f"{{{namespace}}}{tag}"


def fetch_arxiv_papers() -> list[dict]:
    """Query arXiv API for papers mentioning Amazon Braket from the last 12 months."""
    cutoff_date = datetime.now() - timedelta(days=365)
    search_query = 'abs:"Amazon Braket" OR ti:"Amazon Braket"'

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
            title = title_elem.text or "" if title_elem is not None else ""
            combined_text = f"{title} {summary}"

            # Score and classify the paper
            score = score_text(combined_text)
            classification = classify(score)

            title = title.strip().replace("\n", " ")

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
                    "published": published.text.strip(),
                    "score": score,
                    "classification": classification,
                }
            )

        if len(entries) < MAX_RESULTS_PER_REQUEST:
            break
        start += MAX_RESULTS_PER_REQUEST

        if start < TOTAL_MAX_RESULTS:
            time.sleep(REQUEST_DELAY_SECONDS)

    return papers


def _format_table_row(paper: dict) -> str:
    """Format a single paper as a markdown table row."""
    title_escaped = paper["title"].replace("|", "\\|")
    authors_escaped = paper["authors"].replace("|", "\\|")
    arxiv_id = paper["arxiv_id"]
    link = paper.get("link", f"https://arxiv.org/abs/{arxiv_id}")
    return (
        f"| {paper['year']} | {paper['month']} | {title_escaped} | "
        f"{authors_escaped} | [arXiv:{arxiv_id}]({link}) |"
    )


def get_existing_arxiv_ids(content: str) -> set[str]:
    """Extract arxiv IDs from existing PUBLICATIONS.md."""
    arxiv_id_pattern = r"\[arXiv:([\d\.]+)\]"
    return set(re.findall(arxiv_id_pattern, content))


def append_new_entries(
    content: str, new_using: list[dict], new_mentioning: list[dict]
) -> str:
    """Append new entries to existing PUBLICATIONS.md content."""
    lines = content.rstrip().split("\n")

    # Find where to insert new entries (last row of each table)
    using_section_end = -1
    mentioning_section_end = -1
    using_section_start = -1

    for i, line in enumerate(lines):
        if "## Publications Using Amazon Braket" in line:
            using_section_start = i
            # Find the last table row in this section
            j = i + 1
            while j < len(lines) and not lines[j].startswith("##"):
                if lines[j].startswith("|") and "|" in lines[j] and not lines[j].startswith("|---"):
                    using_section_end = j
                j += 1
        elif "## Publications Mentioning Amazon Braket" in line:
            # Find the last table row in this section
            j = i + 1
            while j < len(lines) and not lines[j].startswith("##"):
                if lines[j].startswith("|") and "|" in lines[j] and not lines[j].startswith("|---"):
                    mentioning_section_end = j
                j += 1

    # Insert new entries
    result_lines = list(lines)
    insert_offset = 0

    # Append to "Publications Using Amazon Braket" section
    if new_using:
        if using_section_end >= 0:
            # Insert after last row
            new_rows = [_format_table_row(p) for p in new_using]
            for idx, row in enumerate(new_rows):
                result_lines.insert(using_section_end + 1 + idx + insert_offset, row)
            insert_offset += len(new_rows)
        elif using_section_start >= 0:
            # Section exists but no rows, add after header
            new_rows = [_format_table_row(p) for p in new_using]
            # After header, blank line, table header, separator
            header_end = using_section_start + 3
            for idx, row in enumerate(new_rows):
                result_lines.insert(header_end + idx + insert_offset, row)
            insert_offset += len(new_rows)

    # Append to "Publications Mentioning Amazon Braket" section
    if new_mentioning:
        if mentioning_section_end >= 0:
            # Insert after last row
            new_rows = [_format_table_row(p) for p in new_mentioning]
            for idx, row in enumerate(new_rows):
                result_lines.insert(mentioning_section_end + 1 + idx + insert_offset, row)
        else:
            # Section doesn't exist, add it at the end
            new_section = [
                "",
                "## Publications Mentioning Amazon Braket",
                "",
                "| Year | Month | Title | Authors | Link |",
                "|------|-------|-------|---------|------|",
            ]
            new_section.extend(_format_table_row(p) for p in new_mentioning)
            result_lines.extend(new_section)

    return "\n".join(result_lines)


def create_initial_file(using_papers: list[dict], mentioning_papers: list[dict]) -> str:
    """Create initial PUBLICATIONS.md file if it doesn't exist."""
    lines = [
        "# Recent Publications Using Amazon Braket",
        "",
    ]

    if using_papers:
        lines.extend(
            [
                "## Publications Using Amazon Braket",
                "",
                "| Year | Month | Title | Authors | Link |",
                "|------|-------|-------|---------|------|",
            ]
        )
        lines.extend(_format_table_row(p) for p in using_papers)
        lines.append("")

    if mentioning_papers:
        lines.extend(
            [
                "## Publications Mentioning Amazon Braket",
                "",
                "| Year | Month | Title | Authors | Link |",
                "|------|-------|-------|---------|------|",
            ]
        )
        lines.extend(_format_table_row(p) for p in mentioning_papers)

    return "\n".join(lines)


def update_publications_file(publications_path: Path, content: str) -> None:
    """Write the publications table to PUBLICATIONS.md."""
    publications_path.write_text(content, encoding="utf-8")


def main() -> None:
    """Fetch Braket papers from arXiv and append new ones to PUBLICATIONS.md."""
    repo_root = Path(__file__).resolve().parent.parent
    publications_path = repo_root / "PUBLICATIONS.md"

    # Get existing arxiv IDs
    existing_ids = set()
    if publications_path.exists():
        existing_content = publications_path.read_text(encoding="utf-8")
        existing_ids = get_existing_arxiv_ids(existing_content)
    else:
        existing_content = ""

    # Fetch new papers from arXiv
    new_papers = fetch_arxiv_papers()

    # Filter to only new papers
    new_using = [
        p
        for p in new_papers
        if p["classification"] == "likely_real_usage"
        and p["arxiv_id"] not in existing_ids
    ]
    new_mentioning = [
        p
        for p in new_papers
        if p["classification"] != "likely_real_usage"
        and p["arxiv_id"] not in existing_ids
    ]

    if not new_using and not new_mentioning:
        print("No new publications found.")
        return

    # Append new entries to existing file or create new file
    if publications_path.exists() and existing_content:
        content = append_new_entries(existing_content, new_using, new_mentioning)
    else:
        content = create_initial_file(new_using, new_mentioning)

    update_publications_file(publications_path, content)

    total_new = len(new_using) + len(new_mentioning)
    msg = (
        f"Added {total_new} new publication(s) to PUBLICATIONS.md: "
        f"{len(new_using)} using Amazon Braket, "
        f"{len(new_mentioning)} mentioning Amazon Braket."
    )
    print(msg)


if __name__ == "__main__":
    main()
