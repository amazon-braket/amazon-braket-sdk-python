# Translation

Thank you for your interest in translating the Amazon Braket cheat sheet!

## How to translate

1.  Copy the `doc/cheat_sheet/_includes/en/` directory to a new directory with your language code.
    For example, for a French translation: `doc/cheat_sheet/_includes/fr/`

2.  Translate the content of each `.md` file, keeping the table structure intact.
    *   **Only translate the text after the `|` separators** — the pipe characters that separate columns.
        Leave pipe characters, filenames, code snippets, and links unchanged.

3.  Add your language code to `doc/cheat_sheet/_data/blocks.yml`.
    For example, `fr: Votre titre` for a French title.

4.  Add your language to `doc/cheat_sheet/_config.yml` under the `t:` section.

5.  Create an `index.<lang>.html` page (e.g., `index.fr.html`) with `lang: <lang>` in the front matter.

6.  Submit a pull request with your translation.

## How to add or modify sections

1.  Add a new `.md` file in `doc/cheat_sheet/_includes/en/` (or your language directory).
2.  Add an entry for it in `doc/cheat_sheet/_data/blocks.yml`.
    - `file`: The filename of your new section.
    - `title`: The display title in English.
    - `fr`: (optional) The display title in French.
3.  Submit a pull request with your changes.
