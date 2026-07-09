# BeWordsmith

A tiny, dependency-free knowledge-base / how-to site. Serves a folder of
Markdown files as a dark-themed site with an auto-generated left menu and a
gradient hero header on every page. Standard-library Python only; marked.js +
highlight.js are vendored locally (works offline).

Order sections/pages by prefixing folder or file names with a number
(`1. Intro`, `2. Setup`); the number sets the order and is hidden from the menu label.

## Run

```bash
python3 server.py            # http://localhost:8000
python3 server.py 8137       # custom port
```

## Structure

```
config.json   all settings (title, subtitle, content dir, page word, port)
_app/         vendored marked.js + highlight.js + code theme
_resources/   images (referenced from pages as ../../../_resources/…)
content/      your Markdown — folders become Section → Group → Page
server.py     the whole app
```

## Customize

Edit `config.json`:

```json
{
  "site_title": "BeWordSmith",
  "site_subtitle": "Docs & guides",
  "content_dir": "content",
  "page_word": "page",
  "port": 8000
}
```

A port passed on the command line (`python3 server.py 8137`) overrides
`config.json`. To re-skin, change the `--accent` CSS variable near the top of
the shell styles in `server.py`. Open the in-app **Authoring guide** (bottom of
the sidebar) for formatting help.
