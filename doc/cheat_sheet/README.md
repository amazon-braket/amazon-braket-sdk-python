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

The cheat sheet is a standalone Jekyll project under `doc/cheat_sheet`. Use
Ruby 3.1 or a newer Ruby 3.x release, install Bundler, then install the GitHub
Pages-compatible Jekyll bundle. Ruby 4 is not currently supported by the
current GitHub Pages dependency stack.

From the repository root:

```bash
ruby --version
gem install bundler
BUNDLE_GEMFILE=doc/cheat_sheet/Gemfile bundle install
```

Build the site from the repository root with the same source path as the
GitHub Pages workflow:

```bash
BUNDLE_GEMFILE=doc/cheat_sheet/Gemfile bundle exec jekyll build --source doc/cheat_sheet --destination build/cheat_sheet
python3 doc/cheat_sheet/_scripts/generate_markdown.py --output build/cheat_sheet/genai_cheat_sheet.md
```

Alternatively, install and build from inside `doc/cheat_sheet`:

```bash
cd doc/cheat_sheet
bundle install
bundle exec jekyll build --source . --destination ../../build/cheat_sheet
python3 _scripts/generate_markdown.py --output ../../build/cheat_sheet/genai_cheat_sheet.md
```

The Gemfile includes `csv` and `bigdecimal` explicitly because newer Ruby
versions no longer load every library used by the GitHub Pages-compatible
Jekyll stack as a default gem. If Jekyll reports `cannot load such file --
csv` or `cannot load such file -- bigdecimal`, pull the latest Gemfile and
rerun the relevant `bundle install` command above before `bundle exec`.

If Bundler reports that Ruby 4 does not satisfy the Gemfile, switch to a Ruby
3.x runtime before installing the bundle. For example, on Homebrew use
`brew install ruby@3.3` and run the commands with
`PATH="/opt/homebrew/opt/ruby@3.3/bin:$PATH"`.

If Ruby/Jekyll is not available, run the Python generator and `tox -e docs` to
check the repository documentation path.
