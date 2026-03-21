# How to add a blog post

1. Create a new file e.g. `blog4.md` in this `blogs/` folder

2. Start the file with frontmatter:
```
---
title: "Your Post Title"
date: "March 22, 2026"
excerpt: "A short summary shown on the homepage."
---

Your post content in Markdown goes here...

## A Heading

Normal paragraph text.

- List item one
- List item two

`inline code` and **bold** and *italic* all work.

```python
# Code blocks work too
print("hello world")
```
```

3. **Add the filename to `index.json`** — this is required for GitHub Pages:
```json
[
  "blog1.md",
  "blog2.md",
  "blog3.md",
  "blog4.md"
]
```

That's it — the site will show the new post automatically.
