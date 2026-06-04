\# Amazon Braket SDK Cheat Sheet



This directory contains the source files for the Amazon Braket SDK cheat sheet.



\## Structure



\- `\_data/blocks.yml` controls the order of cheat sheet sections.

\- `\_includes/en/\*.md` contains the individual cheat sheet sections.

\- `index.html` renders the cheat sheet using the configured blocks.

\- `genai\_cheat\_sheet.md` contains a generated Markdown version for text-based use.



\## Adding a new section



1\. Create a new Markdown file in `\_includes/en/`.

2\. Add the file to `\_data/blocks.yml`.

3\. Keep the section in the compact two-column format:



```markdown

| Task | Code |

|---|---|

| Description | `code\_snippet` |

