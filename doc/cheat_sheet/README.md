# Amazon Braket SDK Cheat Sheet

A one-page, browsable reference for the most common Amazon Braket SDK calls,
published as a static site to GitHub Pages and mirrored as a single flat
Markdown file for LLM agents.

This directory contains the **source**. The published site is built from it by
the [`publish-cheat-sheet.yml`](../../.github/workflows/publish-cheat-sheet.yml)
workflow on every push to `main`.

## Layout

```
doc/cheat_sheet/
├── _config.yml            # Jekyll config + per-language UI strings
├── _data/blocks.yml       # the ordered list of sections (the source of truth for order)
├── _includes/
│   ├── blocks.html        # renders each section from blocks.yml
│   ├── header.html        # the language switcher
│   ├── en/*.md            # English sections   (one Markdown table per topic)
│   └── fr/*.md            # French sections     (same code, translated descriptions)
├── _layouts/default.html  # page shell
├── _scripts/
│   ├── verify_snippets.py            # tests the snippets against the installed SDK
│   └── generate_genai_cheat_sheet.py # builds ../genai_cheat_sheet.md
├── index.html             # English entry point
├── index.fr.html          # French entry point
└── cheatsheet.css         # styling
```

The generated companion file lives at [`../genai_cheat_sheet.md`](../genai_cheat_sheet.md).

## A section is a small Markdown table

Each file in `_includes/en/` is a borderless two-column table, one row per call:

```markdown
| Imports | `from braket.circuits import Circuit` |
| Create a circuit | `circuit = Circuit()` |
```

The left cell is a short description, the right cell is the code (wrap code in
backticks). Use `<br>` to put several lines in one cell.

### Hints for the LLM file

The HTML site hides comments, but the GenAI file keeps them. Use them to add
context that only a machine reader needs:

```markdown
| Create a circuit<!-- LLM: . Note the number of qubits is not a constructor argument--> | `circuit = Circuit()` |
```

The hint text is folded into the description in `genai_cheat_sheet.md`.

## Add or edit a section

1. Edit the relevant file in `_includes/en/` (or create a new `NewTopic.md`).
2. If it is a **new** section, register it in `_data/blocks.yml` at the position
   you want it to appear:
   ```yaml
   - file: NewTopic.md
     title: New Topic
     fr: Nouveau sujet
   ```
3. Add the matching translation in `_includes/fr/NewTopic.md`. **Keep the code
   identical to English** — only translate the descriptions. Every section must
   exist in every language or the site build fails.
4. Verify and regenerate (below).

## Verify your changes

The snippets are executable, not decorative. Run the verifier against an
installed copy of the SDK:

```bash
pip install .
python doc/cheat_sheet/_scripts/verify_snippets.py
```

It checks that:

- every `import` in the cheat sheet resolves against the SDK,
- every translated section carries the **same code** as English,
- the GenAI Markdown file is in sync, and
- the local (non-cloud) snippets actually run on `LocalSimulator` and friends.

## Regenerate the GenAI file

After changing any section, rebuild the flat Markdown companion:

```bash
python doc/cheat_sheet/_scripts/generate_genai_cheat_sheet.py
```

Use `--check` to verify it is up to date without writing (this is what CI runs):

```bash
python doc/cheat_sheet/_scripts/generate_genai_cheat_sheet.py --check
```

## Preview the site locally

The site is a standard Jekyll project. The [`Gemfile`](Gemfile) here pins Jekyll
so you get a faithful local preview of the same sources. (The published site is
built by GitHub Pages via the publish workflow, not from this Gemfile.)

### Prerequisites

You need Ruby and Bundler. Check what you have:

```bash
ruby --version      # 3.0 or newer is fine
bundler --version   # if this fails, run: gem install bundler
```

If you do not have Ruby, follow the Jekyll install guide for your OS:
https://jekyllrb.com/docs/installation/

### Build and serve

From this directory:

```bash
cd doc/cheat_sheet
bundle install                 # installs Jekyll and its dependencies (first time only)
bundle exec jekyll serve       # builds the site and starts a local server
```

Then open http://127.0.0.1:4000 in your browser. The French page is at
http://127.0.0.1:4000/fr/.

> The `Gemfile` includes `webrick` because Ruby 3.0+ no longer ships it in the
> standard library and `jekyll serve` needs it. If you ever see a `webrick`
> `LoadError`, run `bundle install` again.

## Add a new language

See [`Translation.md`](Translation.md) for the end-to-end steps (new `_config.yml`
strings, an `index.TAG.html`, and a translated `_includes/TAG/` folder).

## How it is published

On every push to `main`, the publish workflow builds the Jekyll site, regenerates
`genai_cheat_sheet.md`, and deploys to GitHub Pages. Pull requests do **not**
deploy; instead [`validate-cheat-sheet.yml`](../../.github/workflows/validate-cheat-sheet.yml)
runs the verifier so broken snippets are caught before merge.
