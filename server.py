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
    "host": "127.0.0.1",             # bind address (use "0.0.0.0" for LAN/containers)
    "port": 8000,                    # default port (a CLI arg still overrides it)
    "base_path": "",                 # mount under a sub-path, e.g. "/docs", when behind a proxy
    "accent": "#FF671D",             # theme accent color (hex) — re-skins the whole UI
    "home": "",                      # default page: a path or title; blank = auto (intro/overview)
    "donate_url": "",                # optional "Buy me a coffee" footer link; blank = hidden
    "github_repo": "",               # "owner/repo" — enables live version display from GitHub releases
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


def norm_base(bp):
    """Normalize a base path: '' | 'docs' | '/docs/' -> '' | '/docs'."""
    bp = (bp or "").strip().strip("/")
    return "/" + bp if bp else ""


def _hex_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (255, 103, 29)  # fall back to the default orange


def _lighten(rgb, f):
    return tuple(round(c + (255 - c) * f) for c in rgb)


CONFIG = load_config()
SITE_TITLE = CONFIG["site_title"]
SITE_SUBTITLE = CONFIG["site_subtitle"]
CONTENT_DIR = CONFIG["content_dir"]
PAGE_WORD = CONFIG["page_word"]
BASE_PATH = norm_base(CONFIG["base_path"])
_accent_rgb = _hex_rgb(CONFIG["accent"])
ACCENT = CONFIG["accent"]
ACCENT_RGB = "{}, {}, {}".format(*_accent_rgb)
ACCENT_HI = "#{:02x}{:02x}{:02x}".format(*_lighten(_accent_rgb, 0.45))
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


def _load_shell():
    """Read the shared UI template (_app/shell.html) and fill config tokens.
    The same template is used by the PHP backend, so the UI lives in one place."""
    tpl = open(os.path.join(ROOT, "_app", "shell.html"), encoding="utf-8").read()
    return (tpl
            .replace("__SITE_TITLE__", SITE_TITLE)
            .replace("__SITE_SUBTITLE__", SITE_SUBTITLE)
            .replace("__PAGE_WORD__", PAGE_WORD)
            .replace("__DONATE_URL__", str(CONFIG["donate_url"]).replace('"', ''))
            .replace("__GITHUB_REPO__", str(CONFIG["github_repo"]).replace('"', ''))
            .replace("__HOME__", str(CONFIG["home"]).replace('"', '\"'))
            .replace("__ACCENT_RGB__", ACCENT_RGB)
            .replace("__ACCENT_HI__", ACCENT_HI)
            .replace("__ACCENT__", ACCENT)
            .replace("__ASSET__", BASE_PATH)          # "" or "/docs"
            .replace("__TREE__", BASE_PATH + "/api/tree"))


SHELL = _load_shell()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        # When mounted under a base path (behind a proxy that forwards it),
        # strip the prefix before routing / serving files.
        if BASE_PATH and (path == BASE_PATH or path.startswith(BASE_PATH + "/")):
            path = path[len(BASE_PATH):] or "/"
            self.path = path + (("?" + urlparse(self.path).query)
                                if urlparse(self.path).query else "")
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
    host = CONFIG["host"]
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(CONFIG["port"])
    httpd = ThreadingHTTPServer((host, port), Handler)
    shown = "localhost" if host in ("127.0.0.1", "0.0.0.0", "") else host
    print(f"{SITE_TITLE} → http://{shown}:{port}{BASE_PATH or ''}/")
    print(f"Serving from: {ROOT}  (bind {host}:{port}"
          + (f", base path {BASE_PATH}" if BASE_PATH else "") + ")")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.shutdown()


if __name__ == "__main__":
    main()
