# Roadmap

BeWordSmith is **free and open source**. The goal: the best-looking, truly
zero-config Markdown wiki for cheap / shared (cPanel) hosting — no Node, no
database, no build step. We win on **design and out-of-the-box experience**, and
everything ships free (features once scoped as "premium" are now OSS).

## Shipped
- **v1.0** — core: folder-driven navigation, gradient hero, dark theme, built-in
  components (callouts/tabs/accordions/cards), single `config.json`, and two
  backends (Python dev server + PHP for shared hosting) sharing one UI template.
- **v1.1** — client-side full-text search (in-browser index, ranked results with
  highlighted snippets; works on both backends).
- **Polish** — mobile drawer / responsive layout, favicon, optional `donate_url`
  footer link.

## Planned (all free / OSS)
- **Themes** — light mode, curated palettes/fonts, white-label branding.
- **Auth** — password-protect the whole site or specific sections (PHP).
- **In-browser editor / admin** — create, edit, reorder pages; upload images
  (no FTP/git needed). Widens the audience to non-technical users.
- **Ask-the-docs** — local AI chat answering from your Markdown (RAG).
- **Static export + SEO** — pre-rendered HTML, `sitemap.xml`, per-page meta/OG
  tags so public docs rank on search engines.
- **Smaller wins** — "On this page" table of contents, Mermaid diagrams / math,
  versioned docs (v1/v2), privacy-friendly analytics.
- **Install / polish** — one-command launcher, first-run onboarding.

## Notes
- An optional plugin system (already prototyped) can keep the core lean as
  features grow.
- No paid tier — sustained by sponsorship / donations only.

Contributions welcome. See [`CHANGELOG.md`](CHANGELOG.md) for release history.
