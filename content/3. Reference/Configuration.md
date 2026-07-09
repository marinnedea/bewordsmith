# Configuration

All settings live in the config block at the top of `server.py`.

| Setting | Default | What it does |
| --- | --- | --- |
| `SITE_TITLE` | `BeWordsmith` | Sidebar brand and browser tab title |
| `SITE_SUBTITLE` | `Docs & guides` | Small line under the brand |
| `CONTENT_DIR` | `content` | Folder holding your Markdown |
| `PAGE_WORD` | `page` | Noun used in the menu counts |

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
