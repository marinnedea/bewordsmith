# Plugin architecture (proposal)

> **Status: optional / future.** BeWordSmith is fully open source, and features
> can be built straight into the core (as full-text search was). A small plugin
> system is a *possible* way to keep the core lean as more features land — this
> note captures the design so it isn't lost. Nothing here is required.

## The two-backend reality

A feature can touch three layers, with very different costs:

| Layer | Cross-backend? |
| --- | --- |
| **Frontend** (JS/CSS in `_app/`) | ✅ served identically by Python & PHP — write once |
| **Server-side** (endpoints, request handling, file writes) | ⚠️ per-backend |

Rules of thumb:
- Do as much as possible **client-side** — e.g. full-text search is 100%
  in-browser, so it works on both backends with no server code.
- For genuinely server-side features (auth, an editor, an AI proxy), **target
  PHP first** — that's the shared-hosting deployment target. Add Python hooks
  only for local-dev parity when needed.

## Plugin manifest (`plugin.json`)

```json
{
  "name": "search",
  "version": "1.0.0",
  "requires": { "core": ">=1.0.0" },
  "backends": ["frontend"],
  "assets": { "js": ["search.js"], "css": ["search.css"] },
  "server": { "php": "search.php" }
}
```

- `requires.core` — checked against the core version; incompatible plugins are
  skipped with a clear reason ("works with version X").
- `backends` — declares where it runs (`frontend`, `php`, `python`).

## Hook surface the core would expose

- **Frontend:** a global `BWS` object with lifecycle hooks (`onInit`,
  `onPageLoad(page)`, `afterRender(dom)`) and **UI slots** (toolbar, right-rail
  for a table-of-contents, below-hero, sidebar-footer) so plugins add UI without
  patching the shell. The shell reads an enabled-plugin list and injects each
  plugin's JS/CSS.
- **Server (PHP):** a `/plugin/<name>/…` route dispatch, a **request filter**
  (so e.g. `auth` can gate a request before the page is served), and a **tree
  filter** (to modify the generated menu).
- **Config:** each plugin reads its own section of `config.json`.

## Loader flow

1. Scan `plugins/*/plugin.json`.
2. Check `requires.core` vs the core version — skip if incompatible.
3. Load the plugin: inject its assets and include its server handler.
4. Return a per-plugin decision (enabled + reason) so the shell can surface a
   notice for anything skipped.

## Sequencing (if pursued)

1. Add the plugin loader + hook API to the core.
2. Convert **themes / white-label** into the first plugin to dogfood the API.
3. Move further features (auth, editor, ask-the-docs) to plugins as they're built
   — or keep building them into the core directly, whichever stays simpler.
