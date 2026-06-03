# Amazon Braket SDK Cheat Sheet

This directory contains the source for the Amazon Braket SDK cheat sheet. The
GitHub Pages workflow builds the site from this Jekyll project and publishes a
Markdown companion file for readers who want a plain-text reference.

## Update Existing Sections

1. Edit the relevant file in `_includes/en/`.
2. Keep entries compact. The cheat sheet should point to the API quickly, not
   duplicate the full documentation.
3. Prefer snippets that are valid against the current SDK source or examples.
4. Regenerate the Markdown companion:

   ```bash
   python3 doc/cheat_sheet/_scripts/generate_markdown.py
   ```

## Add A Section

1. Add a Markdown file in `_includes/en/`, for example
   `_includes/en/NewFeature.md`.
2. Add the section to `_data/blocks.yml` in the order it should appear:

   ```yaml
   - file: NewFeature.md
     title: New feature
   ```

3. Regenerate `doc/genai_cheat_sheet.md` with the command above.

## Build Locally

Use the same source path as the GitHub Pages workflow:

```bash
bundle exec jekyll build --source doc/cheat_sheet --destination build/cheat_sheet
python3 doc/cheat_sheet/_scripts/generate_markdown.py --output build/cheat_sheet/genai_cheat_sheet.md
```

If Ruby/Jekyll is not available, run the Python generator and `tox -e docs` to
check the repository documentation path.
