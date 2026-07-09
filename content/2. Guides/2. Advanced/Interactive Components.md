# Interactive Components

These use a little inline HTML. **The one rule:** leave a blank line between an HTML tag and the Markdown inside it.

## Callout box

<div class="callout">

**Note:** wrap anything in `<div class="callout">…</div>`. Add `irm` for a blue accent variant.

</div>

## Collapsible section

<details>
<summary>Click to expand</summary>

Hidden content lives here. Great for optional detail or long output.

</details>

## Tabs

<div class="tabs">
<div class="tablabels">
<button class="tab-label active" data-tab="mac">macOS</button>
<button class="tab-label" data-tab="win">Windows</button>
<button class="tab-label" data-tab="linux">Linux</button>
</div>
<div class="tabpanel active" data-tab="mac">

Install with Homebrew:

```bash
brew install something
```

</div>
<div class="tabpanel" data-tab="win">

Install with winget:

```powershell
winget install Something
```

</div>
<div class="tabpanel" data-tab="linux">

Install with apt:

```bash
sudo apt install something
```

</div>
</div>

## Callout row

<div class="frame">
<div class="f lead"><b>Do</b> keep pages focused on one task.</div>
<div class="f emph"><b>Highlight</b> the part that matters most.</div>
<div class="f skip"><b>Avoid</b> walls of text without headings.</div>
</div>

## Key line

<div class="keyline"><b>Remember</b> "One clear idea per page beats a giant page nobody reads."</div>
