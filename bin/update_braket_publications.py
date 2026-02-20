"""
Queries the arXiv API for papers that *use* Amazon Braket and updates
PUBLICATIONS.md with a markdown table of those publications.

Papers that merely mention Amazon Braket (e.g. in a list of platforms) without
actually using it are filtered out by inspecting the abstract for usage signals.

Uses only the Python standard library (no third-party dependencies).
The script is idempotent -- safe to run repeatedly.

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
PUBLICATIONS_PATH = "PUBLICATIONS.md"
BEGIN_MARKER = "<!-- BEGIN_AUTO_PUBLICATIONS -->"
END_MARKER = "<!-- END_AUTO_PUBLICATIONS -->"
MAX_AUTHORS = 3

# ---------------------------------------------------------------------------
# Filtering: distinguish papers that *use* Braket from those that only mention it
# ---------------------------------------------------------------------------

# Patterns that indicate actual usage of Amazon Braket.
# Each pattern is matched case-insensitively against the abstract.
USAGE_PATTERNS = [
    # verb + preposition + Braket
    r"(?:us(?:e|ed|es|ing)|ran|run(?:s|ning)?|execut(?:e[ds]?|ing)|"
    r"deploy(?:ed|s|ing)?|implement(?:ed|s|ing)?|"
    r"test(?:ed|s|ing)?|benchmark(?:ed|s|ing)?|"
    r"simulat(?:e[ds]?|ing)|access(?:ed|es|ing)?|"
    r"perform(?:ed|s|ing)?|conduct(?:ed|s|ing)?|"
    r"built|develop(?:ed|s|ing)?)"
    r"\s+(?:\w+\s+){0,4}(?:on|via|through|with|using)?\s*"
    r"(?:the\s+)?(?:Amazon\s+)?Braket",
    # preposition + Braket (e.g. "on Amazon Braket", "via Amazon Braket")
    r"(?:on|via|through|using)\s+(?:the\s+)?Amazon\s+Braket",
    # Braket SDK / service / hardware / device mentions
    r"(?:Amazon\s+)?Braket\s+(?:SDK|service|simulator|hardware|device|QPU|"
    r"quantum\s+(?:computer|processor|hardware|device))",
    # "available through/on/via Amazon Braket"
    r"available\s+(?:on|through|via)\s+(?:the\s+)?Amazon\s+Braket",
    # passive usage: "Braket was/is used"
    r"(?:Amazon\s+)?Braket\s+(?:was|is|has\s+been)\s+"
    r"(?:used|employed|utilized|leveraged)",
    # code-level references
    r"braket\.(?:aws|circuits|devices|ir)",
]

# Patterns that indicate a mere mention / listing (not actual usage).
MENTION_ONLY_PATTERNS = [
    r"(?:such\s+as|like|including|e\.g\.?\s*,?|for\s+(?:example|instance))"
    r"\s+.*?Amazon\s+Braket",
    r"(?:such\s+as|like|including|e\.g\.?\s*,?|for\s+(?:example|instance))"
    r"\s+.*?Braket",
    # Braket listed alongside other platforms in a comma/and list
    r"(?:IBM|Google|Microsoft|Rigetti|Azure|Qiskit)"
    r"[\w\s,]*(?:and|,)\s*Amazon\s+Braket",
    r"Amazon\s+Braket[\w\s,]*(?:and|,)\s*"
    r"(?:IBM|Google|Microsoft|Rigetti|Azure|Qiskit)",
    # parenthetical mention: "(e.g., Amazon Braket, IBM Qiskit)"
    r"\([^)]*Amazon\s+Braket[^)]*\)",
]


def is_actual_braket_usage(abstract):
    """Return True if the abstract suggests the paper actually uses Amazon Braket,
    rather than just mentioning it in passing."""
    if not abstract:
        return False

    text = " ".join(abstract.split())

    has_usage = any(re.search(p, text, re.IGNORECASE) for p in USAGE_PATTERNS)
    has_mention_only = any(
        re.search(p, text, re.IGNORECASE) for p in MENTION_ONLY_PATTERNS
    )

    # If we find clear usage signals, include the paper.
    if has_usage:
        return True

    # If we only find listing/mention patterns, exclude it.
    if has_mention_only:
        return False

    # If "Amazon Braket" is in the abstract but matched neither category,
    # include it (benefit of the doubt).
    return True


# ---------------------------------------------------------------------------
# arXiv API query and parsing
# ---------------------------------------------------------------------------


def build_query_url():
    """Construct the arXiv API query URL for the past 12 months."""
    today = datetime.date.today()
    start = today - datetime.timedelta(days=365)
    date_range = (
        f"[{start.strftime('%Y%m%d')}0000 TO {today.strftime('%Y%m%d')}2359]"
    )
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
    summary_el = entry.find(f"{ATOM_NS}summary")
    author_els = entry.findall(f"{ATOM_NS}author")

    if id_el is None or title_el is None or published_el is None or not author_els:
        return None

    # arXiv ID: strip URL prefix and version suffix
    raw_id = id_el.text.strip()
    arxiv_id = raw_id.rsplit("/", 1)[-1]
    arxiv_id = re.sub(r"v\d+$", "", arxiv_id)

    title = " ".join(title_el.text.split())

    abstract = ""
    if summary_el is not None and summary_el.text:
        abstract = summary_el.text.strip()

    # Filter: skip papers that only mention Braket without using it
    if not is_actual_braket_usage(abstract):
        print(f"  Filtered out (mention-only): {title}")
        return None

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
    """Fetch and parse arXiv papers that use Amazon Braket."""
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


# ---------------------------------------------------------------------------
# PUBLICATIONS.md generation
# ---------------------------------------------------------------------------


def format_publications_table(papers):
    """Build the auto-generated section with sentinel markers."""
    lines = [
        BEGIN_MARKER,
        "",
        "| Year | Month | Title | Authors | Link |",
        "|------|-------|-------|---------|------|",
    ]
    for p in papers:
        link = f"[arXiv:{p['arxiv_id']}](https://arxiv.org/abs/{p['arxiv_id']})"
        lines.append(
            f"| {p['year']} | {p['month']} | {p['title']} | {p['authors']} | {link} |"
        )
    lines.append("")
    lines.append(END_MARKER)
    return "\n".join(lines)


def update_publications(table_section):
    """Insert or replace the auto-generated table in PUBLICATIONS.md (idempotent).

    Content outside the sentinel markers is preserved, allowing manual edits.
    If PUBLICATIONS.md does not exist it is created from scratch.
    """
    today = datetime.date.today().isoformat()

    try:
        with open(PUBLICATIONS_PATH, "r") as f:
            content = f.read()
    except FileNotFoundError:
        content = None

    if content is not None:
        marker_pattern = re.compile(
            rf"{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}",
            re.DOTALL,
        )
        if marker_pattern.search(content):
            new_content = marker_pattern.sub(table_section, content)
            # Update the "Last updated" line if present
            new_content = re.sub(
                r"_Last updated: \d{4}-\d{2}-\d{2}_",
                f"_Last updated: {today}_",
                new_content,
            )
            print("Replaced existing auto-generated section in PUBLICATIONS.md.")
        else:
            # Markers not found; append the section
            new_content = content.rstrip() + "\n\n" + table_section + "\n"
            print("Appended auto-generated section to PUBLICATIONS.md.")
    else:
        # Create the file from scratch
        new_content = (
            "# Recent Publications Using Amazon Braket\n"
            "\n"
            "This file lists recent arXiv preprints that use Amazon Braket.\n"
            "\n"
            f"_Last updated: {today}_\n"
            "\n"
            f"{table_section}\n"
            "\n"
            "*This table is updated automatically. "
            "Run `python bin/update_braket_publications.py` to refresh manually.*\n"
        )
        print("Created PUBLICATIONS.md.")

    with open(PUBLICATIONS_PATH, "w") as f:
        f.write(new_content)


def main():
    papers = fetch_papers()
    print(f"Found {len(papers)} paper(s) from the past 12 months.")

    if not papers:
        print("No papers found. PUBLICATIONS.md was not modified.")
        return

    table_section = format_publications_table(papers)
    update_publications(table_section)


if __name__ == "__main__":
    main()
