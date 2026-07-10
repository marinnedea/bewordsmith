# Changelog

All notable changes to **BeWordSmith** are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Optional **`donate_url`** config — when set, shows a "☕ Buy me a coffee" link
  in the sidebar footer. Blank by default (hidden).

## [1.1.0] — 2026-07-10

### Added
- **Client-side full-text search.** The sidebar box now searches page *content*
  (not just titles): results show the page, its breadcrumb, and a snippet with
  the match highlighted; clicking opens the page. Zero dependencies, no server
  and no build — the index is fetched and built in the browser, so it works on
  both the Python and PHP backends. Clearing the box restores the menu.

## [1.0.0] — 2026-07-10

First public release.

### Added
- **Folder-driven navigation** — top-level folders are Sections, sub-folders are
  Groups, and `.md` files are Pages. The left menu regenerates on every load.
- **Gradient hero header** on every page, built automatically from the page's
  title, breadcrumb (eyebrow) and first paragraph (lead).
- **Dark theme** with one-color theming: set `accent` and the derived tints
  (`--accent-rgb` / `--accent-hi`) re-skin the whole UI.
- **Built-in components** — callouts, collapsible sections (`<details>`), tabs,
  card grids, callout rows and key lines — plain Markdown plus a little HTML.
- **Offline Markdown rendering** via locally-vendored marked.js + highlight.js
  (no CDN, no build step, no database).
- **Single `config.json`** for all settings: `site_title`, `site_subtitle`,
  `content_dir`, `page_word`, `host`, `port`, `base_path`, `accent`, `home`,
  and a `menu` map for per-path label/order overrides.
- **Ordering** via numeric filename prefixes (`1. `, `2. `), stripped from labels.
- **Two backends, one UI** — a Python standard-library dev server (`server.py`)
  and a PHP backend (`index.php`) for Apache / nginx / shared (cPanel) hosting,
  both filling the shared `_app/shell.html` template.
- **`base_path`** support for mounting under a sub-path behind a reverse proxy.
- In-app **authoring guide** and a live demo at [bewordsmith.com](https://bewordsmith.com).

[1.1.0]: https://github.com/marinnedea/bewordsmith/releases/tag/v1.1.0
[1.0.0]: https://github.com/marinnedea/bewordsmith/releases/tag/v1.0.0
