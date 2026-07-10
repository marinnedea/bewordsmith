# BeWordSmith

A tiny, dependency-free knowledge-base / how-to site. Serves a folder of
Markdown files as a dark-themed site with an auto-generated left menu and a
gradient hero header on every page. marked.js + highlight.js are vendored
locally (works offline).

**🔗 Live demo:** [bewordsmith.com](https://bewordsmith.com) — the site there is itself built with BeWordSmith.

Order sections/pages by prefixing folder or file names with a number
(`1. Intro`, `2. Setup`); the number sets the order and is hidden from the menu label.

## Run it — two ways (pick one)

**Python** — a local dev server, no dependencies beyond Python 3:

```bash
python3 server.py            # http://localhost:8000
python3 server.py 8137       # custom port
```

**PHP** — for Apache / nginx / shared (cPanel) hosting, where PHP is available
by default and no long-running process is allowed:

```bash
# local test:
php -S localhost:8000 index.php
# on shared hosting: just upload the folder — index.php is the entry point.
```

Both backends read the same `config.json` and `content/`, and render the exact
same UI from the shared `_app/shell.html` template.

## Structure

```
config.json      all settings (title, accent, host, port, base_path, home, menu)
index.php        PHP backend (Apache/nginx/shared hosting)
server.py        Python backend (local dev server)
.htaccess        Apache config for shared hosting
_app/shell.html  the shared UI template (both backends fill it in)
_app/            vendored marked.js + highlight.js + code theme
_resources/      images (referenced from pages as ../../../_resources/…)
content/         your Markdown — folders become Section → Group → Page
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
