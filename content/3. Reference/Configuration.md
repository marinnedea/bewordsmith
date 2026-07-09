# Configuration

All settings live in a single **`config.json`** file next to `server.py`:

```json
{
  "site_title": "BeWordSmith",
  "site_subtitle": "Docs & guides",
  "content_dir": "content",
  "page_word": "page",
  "port": 8000
}
```

| Key | Default | What it does |
| --- | --- | --- |
| `site_title` | `BeWordSmith` | Sidebar brand and browser tab title |
| `site_subtitle` | `Docs & guides` | Small line under the brand |
| `content_dir` | `content` | Folder holding your Markdown |
| `page_word` | `page` | Noun used in the menu counts |
| `port` | `8000` | Port to serve on (a CLI arg like `server.py 8137` overrides it) |

Any key you omit falls back to its built-in default, so a partial (or missing) `config.json` still works.

## Theming

The palette is a set of CSS variables at the top of the shell styles. The most useful one:

```css
--accent: #FF671D;   /* change this to re-skin the whole site */
```

## Folder rules

- Top-level folders in `content/` become **Sections**.
- Subfolders become **Groups**; `.md` files become **Pages**.
- Names sort naturally; prefix with `1. `, `2. ` to force order — the number is hidden in the menu label.
- Folders named `_resources`, `_app`, `_help` are ignored by the menu.
