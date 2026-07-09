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

Everything is in `config.json`:

```json
{
  "site_title": "BeWordSmith",
  "site_subtitle": "Docs & guides",
  "content_dir": "content",
  "page_word": "page",
  "host": "127.0.0.1",
  "port": 8000,
  "base_path": "",
  "accent": "#FF671D",
  "home": "",
  "menu": {}
}
```

- `accent` re-skins the whole UI from one hex color.
- `host`/`port` set the bind address (CLI port arg overrides `port`).
- `base_path` mounts the site under a sub-path behind a reverse proxy.
- `home` picks the landing page; `menu` overrides labels/order per path.

Any omitted key falls back to a built-in default. Open the in-app **Authoring
guide** (bottom of the sidebar), or **Reference → Configuration**, for details
including nginx/Apache examples.
