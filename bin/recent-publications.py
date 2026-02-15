import operator
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET  # noqa: S405
from datetime import UTC, datetime, timedelta
from pathlib import Path

"""
Run from the root of the git repository, will fetch recent publications related to "Amazon Braket"
from arXiv and update the README.md file.

Usage: python bin/apply-header.py
"""

# Time delta for fetching papers (1 year)
TIME_DELTA = timedelta(days=365)

# Path resolution relative to script location ensures reliability when called from any directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
README_PATH = os.path.join(REPO_ROOT, "README.md")

# ArXiv API endpoint and query parameters
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# Markdown table structure for recent publications
TABLE_STRUCTURE = [
    "",
    "| Year | Month | Title | Authors | Link |",
    "| :--- | :--- | :--- | :--- | :--- |"
]

XML_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}

# The header in README.md under which the recent publications table will be inserted
TARGET_HEADER = "### Recent Publications"


def get_recent_papers():
    """Fetch papers from arXiv since last year related to 'Amazon Braket'.

    Returns:
        list[dict[str, str]]: A list of dictionaries containing paper details
        (year, month, title, authors, url).

    Raises:
        ValueError: If the constructed URL is invalid.
        Exception: If there is an error during the API request or XML parsing.
    """
    now = datetime.now(UTC)
    one_year_ago = now - TIME_DELTA

    # Format dates as YYYYMMDDHHMM (arXiv API requirement)
    start_date = one_year_ago.strftime("%Y%m%d%H%M")
    end_date = now.strftime("%Y%m%d%H%M")

    query = urllib.parse.quote(
        f'all:"Amazon Braket" AND submittedDate:[{start_date} TO {end_date}]'
    )
    url = f"{ARXIV_API_URL}?search_query={query}&sortBy=submittedDate&sortOrder=descending"

    papers = []

    # Ruff S310: Validate URL format to prevent potential issues with malformed URLs
    if not url.startswith(("http:", "https:")):
        raise ValueError("URL must start with 'http:' or 'https:'")

    try:
        with urllib.request.urlopen(url) as response:  # noqa: S310
            # Ruff S314: Given constraint of local lib only,
            # we will use `xml.etree.ElementTree` for XML parsing, but
            # safer alternative would be `defusedxml.ElementTree`
            root = ET.fromstring(response.read().decode("utf-8"))  # noqa: S314

        for entry in root.findall("atom:entry", XML_NAMESPACE):
            pub_date = entry.find("atom:published", XML_NAMESPACE).text

            # Skip entries without a valid publication date
            # since we rely on it for sorting and filtering
            # and it's too slight of a issue to raise an
            # exception for
            if pub_date is None:
                continue

            date_obj = datetime.strptime(pub_date[:10], "%Y-%m-%d").replace(tzinfo=UTC)

            papers.append({
                "year": date_obj.strftime("%Y"),
                "month": date_obj.strftime("%m"),
                "title": entry.find("atom:title", XML_NAMESPACE).text.replace("\n", " ").strip(),
                "authors": f"{entry.find('atom:author/atom:name', XML_NAMESPACE).text} et al.",
                "url": entry.find("atom:link[@rel='alternate']", XML_NAMESPACE).attrib["href"],
            })
    except Exception as e:
        print(f"Fetch error: {e}")

    papers.sort(key=operator.itemgetter("year", "month"), reverse=True)

    return papers


def update_readme(papers):
    """Update the `README.md` file by inserting a markdown table of recent
    publications under the specified header.

    Args:
        papers (list[dict[str, str]]): A list of dictionaries containing paper
        details (year, month, title, authors, url).

    Raises:
        ValueError: If the target header is not found in the README.md file.
    """
    rows = [
        f"| {p['year']} | {p['month']} | {p['title']} | {p['authors']} | [arXiv]({p['url']}) |"
        for p in papers
    ]
    footer = [
        f"\n*Last updated: {datetime.now(UTC).strftime('%Y-%m-%d')}*\n",
        "For the latest publications, run:\n",
        "```\ncd bin && python recent-publications.py\n```\n"
    ]

    table_content = "\n".join(TABLE_STRUCTURE + rows + footer)

    full_content = Path(README_PATH).read_text(encoding="utf-8")

    if TARGET_HEADER not in full_content:
        raise ValueError(f"Target '{TARGET_HEADER}' not found in `README.md.`")

    pre_header, post_header = full_content.split(TARGET_HEADER, 1)

    # Look for the next header after the target section to avoid overwriting other content
    remaining_sections = ""
    next_section_match = re.search(r"\n#+ ", post_header)
    if next_section_match:
        remaining_sections = post_header[next_section_match.start():]

    updated_readme = f"{pre_header}{TARGET_HEADER}\n{table_content}{remaining_sections}"

    Path(README_PATH).write_text(updated_readme, encoding="utf-8")

    print(f"Successfully updated README.md under '{TARGET_HEADER}'")


if __name__ == "__main__":
    if recent_papers := get_recent_papers():
        update_readme(recent_papers)
