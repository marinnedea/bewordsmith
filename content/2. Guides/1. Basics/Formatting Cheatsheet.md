# Formatting Cheatsheet

Everyday Markdown, all supported.

## Text

**Bold**, *italic*, `inline code`, and [links](https://example.com) (external links open in a new tab). Press <kbd>Ctrl</kbd> <kbd>K</kbd> renders with `<kbd>` tags.

> Blockquotes look like this — handy for notes and callouts.

## Lists

- Bullet one
- Bullet two
  - Nested item
1. Ordered
2. Lists work too

## Code with highlighting

Tag the language for syntax colors:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

## Tables

| Feature | Supported |
| --- | --- |
| Headings | ✅ |
| Tables | ✅ |
| Images | ✅ |

## Images

Put files in the top-level `_resources/` folder and link relatively:

![A placeholder](../../../_resources/placeholder.svg)
