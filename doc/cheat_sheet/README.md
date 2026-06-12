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


## Generating the AI cheat sheet

The AI-readable Markdown cheat sheet is generated from the English cheat sheet blocks.

From the repository root, run:

```bash
python doc/cheat_sheet/_scripts/generate_genai_cheat_sheet.py
```

This updates:

```text
doc/genai_cheat_sheet.md
```

## Building the webpage locally

The cheat sheet webpage is a Jekyll site. Local builds require Ruby, Bundler, and the Ruby gems listed in `doc/cheat_sheet/Gemfile`.

### 1. Install Ruby

Install Ruby for your operating system.

On Windows, use RubyInstaller for Windows and make sure Ruby is added to your `PATH`.

Check the installation:

```bash
ruby --version
gem --version
```

### 2. Install Bundler

Bundler is Ruby's dependency manager. It provides the `bundle` command.

```bash
gem install bundler
```

Check that Bundler is available:

```bash
bundle --version
```

### 3. Install the Jekyll dependencies

From the repository root, run:

```bash
cd doc/cheat_sheet
bundle install
```

### 4. Serve the site locally

From `doc/cheat_sheet`, run:

```bash
bundle exec jekyll serve
```

Then open the local URL printed by Jekyll, usually:

```text
http://127.0.0.1:4000/
```

### Troubleshooting

If `bundle` is not recognized, Ruby/Bundler is not installed or Ruby is not on your `PATH`.

If Jekyll fails on Ruby 3 with a missing `webrick` error, run:

```bash
bundle install
```

The `Gemfile` already includes `webrick` for local serving.
