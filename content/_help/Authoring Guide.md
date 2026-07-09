# Authoring guide — writing &amp; formatting pages

Everything you need to add a page and get the layout right. This page is itself a normal page, so what you see here is exactly what your Markdown will look like.

## Where files live

```
wiki-template/
├─ _resources/                  ← all images go here (shared)
├─ content/
│  ├─ Getting Started/          ← a Section
│  │  └─ Introduction.md        ← a Page
│  └─ Guides/                   ← a Section
│     └─ Basics/                ← a Group
│        └─ Your First Page.md  ← a Page
└─ server.py
```

## Adding a section, group, or page

<div class="callout">

1. Create the folder(s) — e.g. `content/Guides/Advanced/`.
2. Drop a `.md` file inside — e.g. `Deep Dive.md`.
3. **Refresh the browser.** The menu rebuilds itself from the folders on every load. No restart needed.

</div>

**Order:** names are sorted naturally (`Page 2` before `Page 10`). To force a specific order, prefix a folder or file name with a number — `1. Introduction`, `2. Setup`. The number sets the order and is **hidden from the menu label**, so the sidebar still reads cleanly.

## The title bar (hero) is built for you

| Hero part | Comes from |
| --- | --- |
| **Eyebrow** (small accent line) | the breadcrumb — e.g. `Guides · Basics` |
| **Title** (big heading) | the page's first `# H1` |
| **Lead** (intro line) | the page's first paragraph, if it follows the title |

Override the eyebrow with custom text by adding this right after the `# H1`:

```html
<p class="eyebrow">Custom eyebrow text</p>
```

## Images

Put files in the top-level `_resources/` folder, then link with a relative path that climbs back to it. A page in a Group (two folders deep under `content/`) uses `../../../`:

```markdown
![Alt text](../../../_resources/diagram.svg)
```

(A Section-level page uses `../../_resources/…`.)

## Rich components

These use a little inline HTML. **The one rule that matters:** leave a **blank line** between an HTML tag and the Markdown inside it.

### Callout

<div class="callout">

**Tip:** `<div class="callout">…</div>` — add `class="callout irm"` for a blue accent.

</div>

### Collapsible (accordion)

<details>
<summary>Summary line (always visible)</summary>

Hidden content — remember the blank line above.

</details>

### Tabs

<div class="tabs">
<div class="tablabels">
<button class="tab-label active" data-tab="a">First</button>
<button class="tab-label" data-tab="b">Second</button>
</div>
<div class="tabpanel active" data-tab="a">

Content of the first tab.

</div>
<div class="tabpanel" data-tab="b">

Content of the second tab.

</div>
</div>

```html
<div class="tabs">
<div class="tablabels">
<button class="tab-label active" data-tab="a">First</button>
<button class="tab-label" data-tab="b">Second</button>
</div>
<div class="tabpanel active" data-tab="a">

Content of the first tab.

</div>
<div class="tabpanel" data-tab="b">

Content of the second tab.

</div>
</div>
```

### Callout row &amp; key line

<div class="frame">
<div class="f lead"><b>Do</b> …</div>
<div class="f emph"><b>Highlight</b> …</div>
<div class="f skip"><b>Avoid</b> …</div>
</div>

<div class="keyline"><b>Key line</b> "The one sentence to remember."</div>
