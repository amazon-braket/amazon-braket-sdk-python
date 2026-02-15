import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET  # noqa: S405
from datetime import datetime, timedelta

# Path resolution relative to script location ensures reliability when called from any directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
README_PATH = os.path.join(REPO_ROOT, "README.md")

# The header in README.md under which the recent publications table will be inserted
TARGET_HEADER = "### Recent Publications"


def get_recent_papers():
    """Fetch papers from arXiv since last year related to 'Amazon Braket'.

    Returns:
        list[dict[str, str]]: A list of dictionaries containing paper details
        (year, month, title, authors, url).

    Raises:
        Exception: If there is an error during the API request or XML parsing.
    """
    now = datetime.now()
    one_year_ago = now - timedelta(days=365)

    # Format dates as YYYYMMDDHHMM (arXiv API requirement)
    start_date = one_year_ago.strftime("%Y%m%d%H%M")
    end_date = now.strftime("%Y%m%d%H%M")

    raw_query = f'all:"Amazon Braket" AND submittedDate:[{start_date} TO {end_date}]'
    query = urllib.parse.quote(raw_query)

    url = f"http://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=descending"

    papers = []

    try:
        with urllib.request.urlopen(url) as response:
            root = ET.fromstring(response.read().decode("utf-8"))

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            pub_date = entry.find("atom:published", ns).text

            if pub_date is None:
                continue

            date_obj = datetime.strptime(pub_date[:10], "%Y-%m-%d")

            papers.append({
                "year": date_obj.strftime("%Y"),
                "month": date_obj.strftime("%m"),
                "title": entry.find("atom:title", ns).text.replace("\n", " ").strip(),
                "authors": f"{entry.find('atom:author/atom:name', ns).text} et al.",
                "url": entry.find("atom:link[@rel='alternate']", ns).attrib["href"],
            })
    except Exception as e:
        print(f"Fetch error: {e}")

    papers.sort(key=lambda x: (x['year'], x['month']), reverse=True)

    return papers


def update_readme(papers):
    """Updates the README.md file by inserting a markdown table of recent
    publications under the specified header.

    Args:
        papers (list[dict[str, str]]): A list of dictionaries containing paper
        details (year, month, title, authors, url).

    Raises:
        ValueError: If the target header is not found in the README.md file.
    """
    header = [
        "",
        "| Year | Month | Title | Authors | Link |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]
    rows = [
        f"| {p['year']} | {p['month']} | {p['title']} | {p['authors']} | [arXiv]({p['url']}) |"
        for p in papers
    ]
    footer = [f"\n*Last updated: {datetime.now().strftime('%Y-%m-%d')}*\n"]

    table_content = "\n".join(header + rows + footer)

    with open(README_PATH, "r", encoding="utf-8") as f:
        full_content = f.read()

    if TARGET_HEADER not in full_content:
        raise ValueError(f"Target '{TARGET_HEADER}' not found in README.md.")

    pre_header, post_header = full_content.split(TARGET_HEADER, 1)

    # Look for the next header after the target section to avoid overwriting other content
    remaining_sections = ""
    next_section_match = re.search(r"\n#+ ", post_header)
    if next_section_match:
        remaining_sections = post_header[next_section_match.start():]

    updated_readme = f"{pre_header}{TARGET_HEADER}\n{table_content}{remaining_sections}"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_readme)

    print(f"Successfully updated README.md under '{TARGET_HEADER}'")


if __name__ == "__main__":
    if recent_papers := get_recent_papers():
        update_readme(recent_papers)
