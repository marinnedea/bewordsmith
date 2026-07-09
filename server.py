#!/usr/bin/env python3
"""
BeWordsmith — a tiny, dependency-free knowledge-base / how-to site.

Serves a folder of Markdown files as a dark-themed site with a collapsible
left menu that mirrors your folders:  Section / Group / Page.  Markdown is
rendered in the browser with locally-vendored marked.js + highlight.js
(no CDN, works offline). Images resolve because relative paths are preserved.

Drop new folders/files into content/ and refresh — the menu rebuilds itself.
Order things by prefixing folder/file names with a number ("1. ", "2. "):
the number sets the order and is stripped from the label shown in the menu.

No external Python dependencies — standard library only.

Usage:
    python3 server.py [port]      # default port 8000
Then open http://localhost:8000/
"""

import json
import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# Web root = this script's folder. Pages reference images via
# ../../../_resources/... which resolves against this root.
ROOT = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ config ---
# Everything is configured in config.json (next to this script). The values
# below are the built-in defaults used when config.json is missing a key, so
# the site still runs with no config file at all.
DEFAULTS = {
    "site_title": "BeWordSmith",     # sidebar brand + browser tab title
    "site_subtitle": "Docs & guides",  # small line under the brand
    "content_dir": "content",        # folder (next to this script) holding your Markdown
    "page_word": "page",             # noun used for the per-section counts ("3 pages")
    "port": 8000,                    # default port (a CLI arg still overrides it)
    "menu": {},                      # optional per-path label/order overrides (see below)
}


def load_config():
    cfg = dict(DEFAULTS)
    path = os.path.join(ROOT, "config.json")
    try:
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
        cfg.update({k: v for k, v in user.items() if k in DEFAULTS})
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, OSError) as exc:
        print(f"⚠ config.json ignored ({exc}); using defaults", file=sys.stderr)
    return cfg


CONFIG = load_config()
SITE_TITLE = CONFIG["site_title"]
SITE_SUBTITLE = CONFIG["site_subtitle"]
CONTENT_DIR = CONFIG["content_dir"]
PAGE_WORD = CONFIG["page_word"]
# Optional menu overrides: { "content/2. Guides": {"label": "User Guides", "order": 5}, ... }
# keyed by the item's path (relative to this script, forward slashes). Both
# fields optional; anything omitted falls back to prefix/natural-sort behavior.
MENU = CONFIG["menu"] if isinstance(CONFIG.get("menu"), dict) else {}
# -----------------------------------------------------------------------------

_num_re = re.compile(r"(\d+)")
# Optional ordering prefix on a folder/file name: "1. ", "02) ", "3 - ", "4_".
# It controls sort order (via natural_key) and is hidden from the menu label.
_order_prefix_re = re.compile(r"^\s*\d+\s*[.)_-]\s*")
_prefix_num_re = re.compile(r"^\s*(\d+)\s*[.)_-]")


def natural_key(name):
    """Natural sort: 'Page 2' < 'Page 10'. A leading number ('1. ', '2. ')
    is honoured, so prefixing names forces order (prefix hidden in the label)."""
    parts = [int(p) if p.isdigit() else p.lower() for p in _num_re.split(name)]
    return parts


def display_name(name):
    """Strip an optional leading ordering prefix so labels read cleanly."""
    return _order_prefix_re.sub("", name)


def clean_title(filename):
    base = re.sub(r"\.md$", "", filename, flags=re.IGNORECASE)
    return display_name(base)


def _prefix_order(name):
    m = _prefix_num_re.match(name)
    return int(m.group(1)) if m else None


def sort_key(name, path):
    """Order by (explicit JSON order → numeric prefix → nothing). Items with an
    order come first (by that number); the rest sort naturally by name."""
    order = (MENU.get(path) or {}).get("order")
    if order is None:
        order = _prefix_order(name)
    try:
        order = None if order is None else float(order)
    except (TypeError, ValueError):
        order = None
    nk = natural_key(display_name(name))
    return (0, order, nk) if order is not None else (1, nk)


def label_for(name, path, is_file):
    """Custom label from config wins; else the cleaned name."""
    lbl = (MENU.get(path) or {}).get("label")
    if lbl:
        return lbl
    return clean_title(name) if is_file else display_name(name)


def list_md(path):
    try:
        entries = os.listdir(path)
    except OSError:
        return []
    files = [e for e in entries if e.lower().endswith(".md")]
    return sorted(files, key=natural_key)


def list_dirs(path, prefix=None):
    try:
        entries = os.listdir(path)
    except OSError:
        return []
    dirs = []
    for e in entries:
        full = os.path.join(path, e)
        if not os.path.isdir(full):
            continue
        if e in ("_resources", "_app", "_help", "pluginAssets") or e.startswith("."):
            continue
        if prefix and not e.lower().startswith(prefix.lower()):
            continue
        dirs.append(e)
    return sorted(dirs, key=natural_key)


def build_tree():
    """Every top-level folder in content/ is a Section; its subfolders are
    Groups; the .md files are Pages. A .md placed directly in a Section folder
    is a section-level page."""
    base = os.path.join(ROOT, CONTENT_DIR)

    def pages_in(dir_path, path_prefix):
        files = list_md(dir_path)
        files.sort(key=lambda f: sort_key(f, f"{path_prefix}/{f}"))
        return [{"title": label_for(f, f"{path_prefix}/{f}", True),
                 "path": f"{path_prefix}/{f}", "type": "md"} for f in files]

    tree = {"sections": []}
    sections = list_dirs(base)
    sections.sort(key=lambda d: sort_key(d, f"{CONTENT_DIR}/{d}"))
    for section in sections:
        section_path = os.path.join(base, section)
        s_prefix = f"{CONTENT_DIR}/{section}"
        node = {"title": label_for(section, s_prefix, False),
                "pages": pages_in(section_path, s_prefix), "groups": []}
        groups = list_dirs(section_path)
        groups.sort(key=lambda d: sort_key(d, f"{s_prefix}/{d}"))
        for group in groups:
            g_prefix = f"{s_prefix}/{group}"
            g_pages = pages_in(os.path.join(section_path, group), g_prefix)
            if g_pages:
                node["groups"].append(
                    {"title": label_for(group, g_prefix, False), "pages": g_pages})
        if node["pages"] or node["groups"]:
            tree["sections"].append(node)
    return tree


SHELL = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__SITE_TITLE__</title>
<link rel="stylesheet" href="/_app/github-dark.min.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&display=swap" rel="stylesheet">
<script src="/_app/marked.min.js"></script>
<script src="/_app/highlight.min.js"></script>
<style>
  :root {
    /* Cohesive dark palette. Change --accent to re-skin the whole site. */
    --bg: #0b0d12;
    --bg-elev: #14171d;
    --bg-hover: #1b1f27;
    --bg-active: rgba(255,103,29,.13);   /* orange tint — matches the accent */
    --border: #262b34;
    --border-2: #343b47;
    --text: #f1f3f6;
    --muted: #aab2bf;
    --text-dim: #79828f;
    --accent: #FF671D;      /* accent — swap for your brand color */
    --accent-soft: rgba(255,103,29,.10);
    --accent-2: #6ea8fe;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body {
    display: flex;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); overflow: hidden;
  }

  /* ---- Sidebar ---- */
  #sidebar {
    width: 340px; min-width: 260px; max-width: 620px;
    background: var(--bg); border-right: 1px solid var(--border);
    display: flex; flex-direction: column; height: 100vh;
  }
  #brand {
    position: relative; height: 46px; padding: 0 18px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 11px; flex: 0 0 auto; overflow: hidden;
  }
  /* faint orange corner glow — echoes the hero's gradient */
  #brand::before { content: ""; position: absolute; inset: 0; pointer-events: none;
    background: radial-gradient(150px 90px at 0% 0%, rgba(255,103,29,.18), transparent 72%); }
  #brand > * { position: relative; z-index: 1; }
  #brand .dot { width: 11px; height: 11px; border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, #ff8a3d, var(--accent));
    box-shadow: 0 0 12px rgba(255,103,29,.7); flex: 0 0 auto; }
  #brand h1 { font-family: "Poppins", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 15px; margin: 0; font-weight: 700; letter-spacing: .1px; color: #fff; }
  #brand .sub { font-size: 10.5px; color: var(--text-dim); margin-top: 2px;
    text-transform: uppercase; letter-spacing: .08em; }

  #search-wrap { padding: 12px; border-bottom: 1px solid var(--border); flex: 0 0 auto; }
  #search { width: 100%; padding: 8px 11px; font-size: 13px;
    background: var(--bg-elev); color: var(--text);
    border: 1px solid var(--border); border-radius: 8px; outline: none;
    transition: border-color .12s, box-shadow .12s; }
  #search::placeholder { color: var(--text-dim); }
  #search:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }

  #nav { overflow-y: auto; flex: 1 1 auto; padding: 10px 0 24px; }
  #nav::-webkit-scrollbar { width: 9px; }
  #nav::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 5px;
    border: 2px solid var(--bg); }

  /* Sections read as uppercase labels; groups as sub-labels;
     pages as clean inset menu items (no icons, rounded hover/active pills). */
  .section { margin-bottom: 6px; }
  .section > .row { font-family: "Poppins", -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: .09em;
    color: var(--text-dim); }
  .section > .row:hover { color: var(--muted); background: transparent; }
  .group > .row { font-size: 12.5px; color: var(--muted); font-weight: 500; }
  .group > .row:hover { color: var(--text); background: transparent; }
  .row { display: flex; align-items: center; gap: 8px; padding: 7px 16px;
    cursor: pointer; user-select: none; }
  .caret { display: inline-block; width: 10px; text-align: center; color: var(--text-dim);
    transition: transform .12s ease; flex: 0 0 auto; font-size: 9px; opacity: .75; }
  .collapsed > .row > .caret { transform: rotate(-90deg); }
  .collapsed > .children { display: none; }

  .section > .children > .group > .row { padding-left: 16px; }

  .leaf { position: relative; display: flex; align-items: center; margin: 1px 8px;
    padding: 6px 12px; cursor: pointer; font-size: 12.5px; color: var(--muted);
    border-radius: 7px; line-height: 1.35; transition: background .12s, color .12s; }
  .section > .children > .leaf { padding-left: 16px; }
  .group > .children .leaf { padding-left: 30px; }
  .leaf:hover { background: var(--bg-hover); color: var(--text); }
  .leaf.active { background: var(--bg-active); color: #ffb27a; font-weight: 600; }
  /* small accent tick on the active item */
  .leaf.active::before { content: ""; position: absolute; left: 4px; top: 50%;
    transform: translateY(-50%); width: 3px; height: 15px; border-radius: 2px; background: var(--accent); }
  .count { margin-left: auto; font-size: 10px; color: var(--text-dim); font-weight: 500;
    background: var(--bg-elev); border: 1px solid var(--border); border-radius: 10px; padding: 1px 7px; }
  .hidden { display: none !important; }

  /* Footer help entry — separated from the main menu */
  #sidebar-foot { flex: 0 0 auto; border-top: 1px solid var(--border); padding: 10px 12px; background: var(--bg); }
  .foot-link { display: flex; align-items: center; gap: 9px; padding: 9px 12px; border-radius: 8px;
    font-size: 12.5px; color: var(--muted); cursor: pointer; border: 1px solid var(--border);
    background: var(--bg-elev); transition: color .12s, border-color .12s, background .12s; }
  .foot-link .fi { font-size: 14px; color: var(--accent); flex: 0 0 auto; }
  .foot-link:hover { color: var(--text); border-color: rgba(255,103,29,.4); background: var(--accent-soft); }
  .foot-link.active { color: #ffb27a; border-color: rgba(255,103,29,.5); background: var(--bg-active); }

  /* ---- Main ---- */
  #main { flex: 1 1 auto; display: flex; flex-direction: column; height: 100vh; min-width: 0; }
  #topbar { height: 46px; flex: 0 0 auto; display: flex; align-items: center; gap: 12px;
    padding: 0 16px; border-bottom: 1px solid var(--border);
    background: var(--bg); font-size: 13px; color: var(--text-dim); }
  #crumb { color: var(--muted); font-weight: 500; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; }
  #topbar .spacer { flex: 1; }
  #topbar button { background: var(--bg-elev); color: var(--text-dim); border: 1px solid var(--border);
    border-radius: 6px; padding: 5px 10px; font-size: 12px; cursor: pointer; white-space: nowrap; }
  #topbar button:hover { color: var(--text); border-color: var(--accent); }
  #prev-next { display: flex; gap: 6px; }

  #scroll { flex: 1 1 auto; overflow-y: auto; }
  #content { width: 100%; }
  .md-wrap { max-width: 940px; margin: 0 auto; padding: 30px 48px 120px; }

  /* ===== Hero header (design language from the IRM SE Demo Scripts page) ===== */
  .hero { position: relative; overflow: hidden; border-bottom: 1px solid var(--border);
    background: #0b0d12; padding: 58px 48px 44px; }
  .hero::before { content: ""; position: absolute; inset: 0; z-index: 0; pointer-events: none;
    background:
      radial-gradient(620px 320px at 6% 125%, rgba(255,103,29,.34), transparent 62%),
      radial-gradient(720px 360px at 94% -25%, rgba(139,92,246,.40), transparent 60%); }
  .hero-inner { position: relative; z-index: 1; max-width: 940px; margin: 0 auto; }
  .hero .hero-eyebrow { color: #ffb27a; font-size: 12px; letter-spacing: .14em;
    text-transform: uppercase; font-weight: 700; margin: 0 0 12px; }
  .hero-title { font-family: "Poppins", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-weight: 800; font-size: clamp(28px, 3.6vw, 50px); line-height: 1.06; letter-spacing: -.015em;
    color: #fff; margin: 0; }
  .hero-lead { font-size: 17px; line-height: 1.5; color: #c9d1d9; max-width: 760px; margin: 16px 0 0; }
  .hero-title { overflow-wrap: break-word; }
  @media (max-width: 900px) {
    #sidebar { width: 240px; min-width: 190px; }
    .hero { padding: 34px 22px 26px; }
    .md-wrap { padding: 22px 22px 100px; }
    .hero-title { font-size: clamp(22px, 6vw, 34px); }
  }

  /* Full-bleed embedded HTML pages (cloned standalone pages). */
  body.page-mode #scroll { overflow: hidden; }
  body.page-mode #content { max-width: none; margin: 0; padding: 0; height: 100%; }
  .page-frame { width: 100%; height: 100%; border: 0; display: block; background: var(--bg); }

  /* ---- Rendered markdown ---- */
  .md { color: #c9d1d9; font-size: 15px; line-height: 1.65; word-wrap: break-word; }
  .md h1, .md h2, .md h3, .md h4 { color: var(--text); line-height: 1.3; margin: 1.4em 0 .6em; }
  .md h1 { font-size: 1.9em; border-bottom: 1px solid var(--border); padding-bottom: .3em; margin-top: 0; }
  .md h2 { font-size: 1.45em; border-bottom: 1px solid var(--border); padding-bottom: .3em; }
  .md h3 { font-size: 1.2em; }
  .md a { color: var(--accent-2); text-decoration: none; }
  .md a:hover { text-decoration: underline; }
  .md p, .md li { color: #c9d1d9; }
  .md strong { color: var(--text); }
  .md ul, .md ol { padding-left: 1.6em; }
  .md li { margin: .25em 0; }
  .md img { max-width: 100%; height: auto; border-radius: 6px; border: 1px solid var(--border);
    background: #fff; display: block; margin: 14px 0; }
  .md hr { border: 0; border-top: 1px solid var(--border); margin: 1.6em 0; }
  .md blockquote { margin: 1em 0; padding: .4em 1em; color: var(--text-dim);
    border-left: 3px solid var(--accent); background: var(--bg-elev); border-radius: 0 6px 6px 0; }
  .md code { background: #161b22; color: #f0883e; padding: .15em .4em; border-radius: 5px;
    font-size: .88em; font-family: "SF Mono", ui-monospace, Menlo, Consolas, monospace; }
  .md pre { background: #161b22 !important; border: 1px solid var(--border); border-radius: 8px;
    padding: 14px 16px; overflow-x: auto; margin: 14px 0; }
  .md pre code { background: transparent !important; color: #c9d1d9; padding: 0; font-size: .86em; }
  .md table { border-collapse: collapse; margin: 14px 0; display: block; overflow-x: auto; }
  .md th, .md td { border: 1px solid var(--border); padding: 7px 12px; }
  .md thead th { background: var(--bg-hover); color: var(--text); }
  .md tbody tr:nth-child(even) { background: var(--bg-elev); }
  .md kbd { border: 1px solid var(--border); border-bottom-width: 2px; border-radius: 4px;
    padding: 1px 5px; background: var(--bg-hover); font-size: .85em; }

  /* ===== Cloned "IRM SE Demo Scripts" components (accordions + CSS tabs) ===== */
  .md .eyebrow { font-size: 11px; text-transform: uppercase; letter-spacing: .12em;
    color: var(--accent); font-weight: 700; margin: 0 0 4px; }

  /* accordions (native <details>) */
  .md details { border: 1px solid var(--border); border-radius: 10px; background: var(--bg-elev);
    margin: 12px 0; padding: 2px 16px; }
  .md details > summary { cursor: pointer; list-style: none; margin: 0 -16px; padding: 12px 16px;
    font-weight: 600; color: var(--text); display: flex; align-items: center; gap: 10px; }
  .md details > summary::-webkit-details-marker { display: none; }
  .md details > summary::before { content: "▸"; color: var(--text-dim); transition: transform .15s ease; flex: 0 0 auto; }
  .md details[open] > summary::before { transform: rotate(90deg); }
  .md details[open] > summary { border-bottom: 1px solid var(--border); margin-bottom: 10px; }
  .md .kicker { font-size: 10px; text-transform: uppercase; letter-spacing: .06em;
    color: var(--accent); font-weight: 700; margin-right: 6px; }
  .md .step > summary .n { display: inline-flex; width: 22px; height: 22px; align-items: center;
    justify-content: center; border-radius: 50%; background: var(--accent); color: #fff;
    font-size: 12px; font-weight: 700; flex: 0 0 auto; }
  .md .dur { margin-left: auto; font-weight: 500; font-size: 12px; color: var(--text-dim); }
  .md .step.hot > summary .dur { color: var(--accent); font-weight: 600; }
  .md details.proof > summary { color: var(--text-dim); }
  .md .flowctrl { display: flex; gap: 8px; margin: 2px 0 12px; }
  .md .exp-btn { background: var(--bg-elev); border: 1px solid var(--border); color: var(--text-dim);
    border-radius: 6px; padding: 5px 12px; font-size: 12px; cursor: pointer; }
  .md .exp-btn:hover { color: var(--text); border-color: var(--accent); }

  /* cards / grids */
  .md .grid2, .md .paingrid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 12px 0; }
  .md .grid2 .card, .md .paincard { border: 1px solid var(--border); border-radius: 10px;
    background: var(--bg-elev); padding: 2px 14px; }
  @media (max-width: 640px) { .md .grid2, .md .paingrid { grid-template-columns: 1fr; } }

  /* callouts */
  .md .callout { border-left: 3px solid var(--accent); background: var(--bg-elev);
    border-radius: 0 8px 8px 0; padding: 2px 16px; margin: 14px 0; }
  .md .callout.irm { border-left-color: #3b82f6; }
  .md .zonetag { border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px;
    font-size: 13px; margin: 16px 0 8px; color: var(--muted); }
  .md .zonetag.alerting { border-left: 3px solid #eab308; }
  .md .zonetag.irm { border-left: 3px solid var(--accent); }
  .md .whoroom { background: var(--bg-elev); border: 1px solid var(--border); border-radius: 8px;
    padding: 10px 14px; font-size: 14px; margin: 4px 0 14px; }

  .md .frame { display: grid; gap: 8px; margin: 12px 0; }
  .md .frame .f { border-left: 3px solid var(--border); padding: 8px 14px; background: var(--bg-elev);
    border-radius: 0 8px 8px 0; font-size: 14px; }
  .md .frame .f b { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }
  .md .frame .f.lead { border-left-color: #22c55e; } .md .frame .f.lead b { color: #22c55e; }
  .md .frame .f.emph { border-left-color: #3b82f6; } .md .frame .f.emph b { color: #3b82f6; }
  .md .frame .f.skip { border-left-color: #ef4444; } .md .frame .f.skip b { color: #ef4444; }
  .md .keyline { border-left: 3px solid var(--accent); background: rgba(255,103,29,.08);
    padding: 10px 14px; border-radius: 0 8px 8px 0; font-style: italic; margin: 12px 0; }
  .md .keyline b { font-style: normal; display: block; font-size: 11px; text-transform: uppercase;
    letter-spacing: .05em; color: var(--accent); margin-bottom: 2px; }

  /* Tabs — generic, driven by a tiny JS handler (data-tab attributes) */
  .md .tablabels { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0; padding-bottom: 16px;
    border-bottom: 1px solid var(--border); }
  .md .tab-label { cursor: pointer; border: 1px solid var(--border); border-radius: 10px;
    padding: 9px 16px; font-size: 13.5px; color: var(--muted); background: var(--bg-elev);
    font: inherit; font-size: 13.5px; transition: border-color .12s, background .12s, color .12s; }
  .md .tab-label:hover { border-color: var(--text-dim); color: var(--text); }
  .md .tab-label.active { border-color: var(--accent); background: var(--accent-soft); color: #ffb27a; font-weight: 600; }
  .md .tabpanel { display: none; }
  .md .tabpanel.active { display: block; }

  #welcome { display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center; padding: 80px 40px; color: var(--text-dim); }
  #welcome h2 { color: var(--text); font-weight: 600; margin: 0 0 8px; }
  #welcome .dot { width: 44px; height: 44px; border-radius: 50%; margin-bottom: 18px;
    background: radial-gradient(circle at 30% 30%, #ff8a3d, var(--accent));
    box-shadow: 0 0 30px var(--accent); }
</style>
</head>
<body>
  <aside id="sidebar">
    <div id="brand">
      <div class="dot"></div>
      <div>
        <h1>__SITE_TITLE__</h1>
        <div class="sub">__SITE_SUBTITLE__</div>
      </div>
    </div>
    <div id="search-wrap">
      <input id="search" type="text" placeholder="Filter pages…" autocomplete="off">
    </div>
    <nav id="nav"></nav>
    <div id="sidebar-foot">
      <div class="foot-link" id="help-link">
        <span class="fi">✎</span>
        <span>Authoring guide — how to write pages</span>
      </div>
    </div>
  </aside>

  <div id="main">
    <div id="topbar">
      <span id="crumb">Select a page</span>
      <span class="spacer"></span>
      <div id="prev-next">
        <button id="prev" title="Previous page">← Prev</button>
        <button id="next" title="Next page">Next →</button>
      </div>
      <button id="open-raw" title="Open the raw .md file">↗ Raw</button>
    </div>
    <div id="scroll">
      <div id="content">
        <div id="welcome">
          <div class="dot"></div>
          <h2>__SITE_TITLE__</h2>
          <p>Pick a page from the menu on the left.</p>
        </div>
      </div>
    </div>
  </div>

<script>
// marked v12 dropped the `highlight` option; we highlight after render instead.
marked.setOptions({ gfm: true, breaks: false });

function highlightBlocks(root) {
  root.querySelectorAll('pre code').forEach(block => {
    try { hljs.highlightElement(block); } catch (e) { /* ignore */ }
  });
}

// Build the hero header from a note's leading content, consuming the pieces
// it uses out of the body so they aren't duplicated below.
function buildHero(md, entry) {
  // Title: the note's first <h1>, else the menu title.
  const h1 = md.querySelector('h1');
  const titleText = (h1 ? h1.textContent : entry.title).trim();

  // Eyebrow: an explicit .eyebrow element if the note has one, else the
  // breadcrumb ancestors (everything before the title).
  let eyebrowText = '';
  const eye = md.querySelector('.eyebrow');
  if (eye) { eyebrowText = eye.textContent.trim(); eye.remove(); }
  else { eyebrowText = entry.crumb.split('  ›  ').slice(0, -1).join('  ·  '); }

  if (h1) h1.remove();

  // Lead: only if the body now *starts* with a paragraph (a genuine intro).
  let leadHTML = '';
  const first = md.firstElementChild;
  if (first && first.tagName === 'P') { leadHTML = first.innerHTML; first.remove(); }

  const hero = document.createElement('div');
  hero.className = 'hero';
  const inner = document.createElement('div');
  inner.className = 'hero-inner';
  if (eyebrowText) {
    const e = document.createElement('div'); e.className = 'hero-eyebrow';
    e.textContent = eyebrowText; inner.appendChild(e);
  }
  const h = document.createElement('h1'); h.className = 'hero-title';
  h.textContent = titleText; inner.appendChild(h);
  if (leadHTML) {
    const p = document.createElement('p'); p.className = 'hero-lead';
    p.innerHTML = leadHTML; inner.appendChild(p);
  }
  hero.appendChild(inner);
  return hero;
}

const content = document.getElementById('content');
const crumb = document.getElementById('crumb');
const scroll = document.getElementById('scroll');
let flatOrder = [];   // ordered list of {path,title,crumb,leaf}
let currentIdx = -1;

function encPath(p) { return '/' + p.split('/').map(encodeURIComponent).join('/'); }

function setActive(entry) {
  document.querySelectorAll('.leaf.active, .foot-link.active').forEach(x => x.classList.remove('active'));
  if (entry.leaf) entry.leaf.classList.add('active');
  currentIdx = flatOrder.indexOf(entry);
  updatePrevNext();
}

// Footer: the authoring guide (a page that lives outside the content tree,
// so it never shows up in the auto-generated menu).
const helpEntry = {
  path: 'content/_help/Authoring Guide.md',
  title: 'Authoring guide', type: 'md',
  crumb: 'Help  ›  Authoring guide',
  leaf: document.getElementById('help-link'),
};
document.getElementById('help-link').onclick = () => loadNote(helpEntry);

async function loadNote(entry) {
  const url = encPath(entry.path);
  crumb.textContent = entry.crumb;
  document.title = entry.title + ' — __SITE_TITLE__';

  // Standalone HTML pages render full-bleed in an iframe (own design + JS).
  if (entry.type === 'html') {
    document.body.classList.add('page-mode');
    content.innerHTML = '';
    const fr = document.createElement('iframe');
    fr.className = 'page-frame';
    fr.src = url;
    content.appendChild(fr);
    setActive(entry);
    return;
  }
  document.body.classList.remove('page-mode');
  content.innerHTML = '<div class="md">Loading…</div>';
  let text;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(res.status);
    text = await res.text();
  } catch (e) {
    content.innerHTML = '<div class="md">⚠️ Failed to load note (' + e.message + ')</div>';
    return;
  }
  const div = document.createElement('div');
  div.className = 'md';
  div.innerHTML = marked.parse(text);

  // Resolve relative image/link paths against the note's real location.
  const baseUrl = new URL(url, location.href);
  div.querySelectorAll('img').forEach(img => {
    const raw = img.getAttribute('src');
    if (raw && !/^https?:|^data:/.test(raw)) img.src = new URL(raw, baseUrl).href;
  });
  div.querySelectorAll('a').forEach(a => {
    const raw = a.getAttribute('href');
    if (raw && /^https?:/.test(raw)) { a.target = '_blank'; a.rel = 'noopener'; }
  });

  const hero = buildHero(div, entry);
  highlightBlocks(div);

  content.innerHTML = '';
  content.appendChild(hero);
  const wrap = document.createElement('div');
  wrap.className = 'md-wrap';
  wrap.appendChild(div);
  content.appendChild(wrap);
  scroll.scrollTop = 0;
  setActive(entry);
}

function updatePrevNext() {
  document.getElementById('prev').disabled = currentIdx <= 0;
  document.getElementById('next').disabled = currentIdx < 0 || currentIdx >= flatOrder.length - 1;
}
function go(delta) {
  const i = currentIdx + delta;
  if (i < 0 || i >= flatOrder.length) return;
  const entry = flatOrder[i];
  // expand ancestors so the active item is visible
  let el = entry.leaf;
  while (el) { el.classList && el.classList.remove('collapsed'); el = el.parentElement && el.parentElement.closest('.session,.module'); }
  entry.leaf.scrollIntoView({block: 'nearest'});
  loadNote(entry);
}
document.getElementById('prev').onclick = () => go(-1);
document.getElementById('next').onclick = () => go(1);
document.getElementById('open-raw').onclick = () => {
  if (currentIdx >= 0) window.open(encPath(flatOrder[currentIdx].path), '_blank');
};

function el(tag, cls, txt) { const n = document.createElement(tag); if (cls) n.className = cls; if (txt != null) n.textContent = txt; return n; }

function makeLeaf(note, crumbPrefix) {
  const leaf = el('div', 'leaf');
  leaf.dataset.title = note.title.toLowerCase();
  leaf.appendChild(el('span', 'lab-label', note.title));
  const entry = { path: note.path, title: note.title, type: note.type || 'md',
                  crumb: crumbPrefix + '  ›  ' + note.title, leaf };
  flatOrder.push(entry);
  leaf.onclick = () => loadNote(entry);
  return leaf;
}

function makeGroup(kind, title, count) {
  const wrap = el('div', kind);
  const row = el('div', 'row');
  row.appendChild(el('span', 'caret', '▾'));
  row.appendChild(el('span', null, title));
  if (count != null) row.appendChild(el('span', 'count', count + ' __PAGE_WORD__' + (count === 1 ? '' : 's')));
  row.onclick = () => wrap.classList.toggle('collapsed');
  const children = el('div', 'children');
  wrap.appendChild(row); wrap.appendChild(children);
  return { wrap, children };
}

function render(tree) {
  const nav = document.getElementById('nav');
  nav.innerHTML = ''; flatOrder = [];
  tree.sections.forEach((section, si) => {
    let total = section.pages.length;
    section.groups.forEach(g => total += g.pages.length);
    const s = makeGroup('section', section.title, total);
    if (si > 0) s.wrap.classList.add('collapsed');
    section.pages.forEach(pg => s.children.appendChild(makeLeaf(pg, section.title)));
    section.groups.forEach(group => {
      const gg = makeGroup('group', group.title, group.pages.length);
      group.pages.forEach(pg => gg.children.appendChild(makeLeaf(pg, section.title + '  ›  ' + group.title)));
      s.children.appendChild(gg.wrap);
    });
    nav.appendChild(s.wrap);
  });
  updatePrevNext();

  // Landing page: prefer an intro/overview/readme page, else the first page.
  const home = flatOrder.find(e => /introduction|overview|welcome|readme|index|getting started/i.test(e.title))
            || flatOrder[0];
  if (home) loadNote(home);
}

document.getElementById('search').addEventListener('input', (e) => {
  const q = e.target.value.trim().toLowerCase();
  document.querySelectorAll('.section').forEach(sec => {
    let secVisible = false;
    sec.querySelectorAll('.group').forEach(grp => {
      let grpVisible = false;
      grp.querySelectorAll('.leaf').forEach(leaf => {
        const match = !q || leaf.dataset.title.includes(q);
        leaf.classList.toggle('hidden', !match);
        if (match) grpVisible = true;
      });
      grp.classList.toggle('hidden', !grpVisible);
      if (grpVisible && q) grp.classList.remove('collapsed');
      if (grpVisible) secVisible = true;
    });
    sec.querySelectorAll(':scope > .children > .leaf').forEach(leaf => {
      const match = !q || leaf.dataset.title.includes(q);
      leaf.classList.toggle('hidden', !match);
      if (match) secVisible = true;
    });
    sec.classList.toggle('hidden', !secVisible);
    if (q && secVisible) sec.classList.remove('collapsed');
  });
});

// keyboard: left/right arrows navigate when not typing in the filter
document.addEventListener('keydown', (e) => {
  if (document.activeElement === document.getElementById('search')) return;
  if (e.key === 'ArrowLeft') go(-1);
  if (e.key === 'ArrowRight') go(1);
});

// Delegated handlers (survive note re-renders):
content.addEventListener('click', (e) => {
  // Expand all / Collapse all — toggles every step accordion in the same tabs/panel.
  const btn = e.target.closest('.exp-btn');
  if (btn) {
    const scope = btn.closest('.tabpanel') || content;
    const open = btn.dataset.act === 'open';
    scope.querySelectorAll('details.step, details').forEach(d => { d.open = open; });
    return;
  }
  // Tabs — click a .tab-label to show the matching .tabpanel (by data-tab).
  const tab = e.target.closest('.tab-label');
  if (tab) {
    const tabs = tab.closest('.tabs');
    const key = tab.dataset.tab;
    tabs.querySelectorAll(':scope .tab-label').forEach(l => l.classList.toggle('active', l === tab));
    tabs.querySelectorAll(':scope > .tabpanel, :scope .tabpanel').forEach(p =>
      p.classList.toggle('active', p.dataset.tab === key));
  }
});

fetch('/api/tree').then(r => r.json()).then(render);
</script>
</body>
</html>
"""

# Bake the config values into the shell (the shell is a raw string full of
# CSS braces, so we use simple token replacement rather than str.format).
SHELL = (SHELL
         .replace("__SITE_TITLE__", SITE_TITLE)
         .replace("__SITE_SUBTITLE__", SITE_SUBTITLE)
         .replace("__PAGE_WORD__", PAGE_WORD))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._send(SHELL.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/api/tree":
            return self._send(json.dumps(build_tree()).encode("utf-8"),
                              "application/json; charset=utf-8")
        return super().do_GET()

    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def guess_type(self, path):
        if path.lower().endswith(".md"):
            return "text/markdown; charset=utf-8"
        return super().guess_type(path)

    def log_message(self, fmt, *args):
        msg = fmt % args
        if "_resources" in msg or "/_app/" in msg:
            return
        sys.stderr.write("%s - %s\n" % (self.address_string(), msg))


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(CONFIG["port"])
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"{SITE_TITLE} → http://localhost:{port}/")
    print(f"Serving from: {ROOT}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.shutdown()


if __name__ == "__main__":
    main()
