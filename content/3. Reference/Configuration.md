# Configuration

All settings live in a single **`config.json`** file next to `server.py`:

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
  "donate_url": ""
}
```

| Key | Default | What it does |
| --- | --- | --- |
| `site_title` | `BeWordSmith` | Sidebar brand and browser tab title |
| `site_subtitle` | `Docs & guides` | Small line under the brand |
| `content_dir` | `content` | Folder holding your Markdown |
| `page_word` | `page` | Noun used in the menu counts |
| `host` | `127.0.0.1` | Bind address. Use `0.0.0.0` for LAN / containers |
| `port` | `8000` | Port to serve on (a CLI arg like `server.py 8137` overrides it) |
| `base_path` | `""` | Mount under a sub-path (see below) |
| `accent` | `#FF671D` | Theme color (hex). Re-skins the whole UI |
| `home` | `""` | Default landing page — a page path or title; blank = auto |
| `donate_url` | `""` | Optional "Buy me a coffee" footer link. An external URL opens in a new tab; a page path/title opens that page (e.g. a support page with a QR). Blank = hidden |

Any key you omit falls back to its built-in default, so a partial (or missing) `config.json` still works.

## Theming

Set `accent` to any hex color and the whole UI re-skins — the lighter text tint
and translucent hover/active fills are derived from it automatically:

```json
{ "accent": "#3b82f6" }
```

## Serving behind nginx / Apache

For a subdomain root (e.g. `docs.example.com`), just proxy to the app and set
`host` as needed:

```nginx
location / { proxy_pass http://127.0.0.1:8000; }
```

To mount under a **sub-path** (e.g. `example.com/docs/`), set `base_path` and
forward the prefix (note: no trailing slash on `proxy_pass`, so the prefix is
kept):

```json
{ "base_path": "/docs" }
```
```nginx
location /docs/ { proxy_pass http://127.0.0.1:8000; }
```

`base_path` prefixes every generated URL and the server strips it from incoming
requests, so assets, the page tree, and images all resolve correctly.

## Folder rules

- Top-level folders in `content/` become **Sections**.
- Subfolders become **Groups**; `.md` files become **Pages**.
- Names sort naturally; prefix with `1. `, `2. ` to force order — the number is hidden in the menu label.
- Folders named `_resources`, `_app`, `_help` are ignored by the menu.

## Custom menu labels & order (optional)

The `menu` block in `config.json` overrides the label and/or order of any
folder or file **without renaming it on disk**. Key each entry by its path
(relative to the project, forward slashes):

```json
"menu": {
  "content/2. Guides": { "label": "User Guides", "order": 5 },
  "content/1. Getting Started/1. Introduction.md": { "label": "Start here" },
  "content/3. Reference": { "order": 0 }
}
```

- `label` — text shown in the menu instead of the (cleaned) file/folder name.
- `order` — a number on the **same scale as the numeric prefixes**. Items with
  an order (from here *or* a `1. ` prefix) sort first by that number; use a
  smaller number to come before a prefixed item (e.g. `0` beats `1. `).
- Both fields are optional, and anything not listed keeps its normal
  prefix / natural-sort behavior.
