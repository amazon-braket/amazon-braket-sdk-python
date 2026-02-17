# Translation Guide

TL;DR:

- See `_config.yml`, `index.br.html` and `_includes/`

The translation of this cheat-sheet requires the followings steps:

- Choose a tag for your language, such as `en` for English or `fr` for French;
- On [`_config.yml`](_config.yml), add your tag and translate the given phrases;
- Copy `index.html` to `index.TAG.html`, where TAG is your tag;
- Modify `index.TAG.html`, changing `lang: TAG` and `permalink: /TAG/`;
- Copy the folder `_includes/en/` to `_includes/TAG/`, i.e., create a folder `TAG`
  inside `_includes` with a copy of all the `.md` files; **don't change the .md names**;
- On file `_data/blocks.yml`, add a `  TAG: translated title` line for each title;
- Translate each block in `_includes/TAG`.

